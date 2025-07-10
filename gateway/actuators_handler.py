import json
import time
import socket
import logging
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import ActuatorUpdate, ActuatorsReport
from messages_pb2 import CommandType, ActuatorCommand, ActuatorComply


def actuators_report_generator(args):
    logger = logging.getLogger('ACTUATORS_REPORT_GENERATOR')
    logger.info('Iniciando o gerador de relatórios dos atuadores')
    idle_time = 0
    while not args.stop_flag.is_set():
        if (
            not args.pending_actuators_updates.is_set()
            and idle_time < args.reports_gen_interval
        ):
            time.sleep(1.0)
            idle_time += 1
            continue
        idle_time = 0
        with args.db_actuators_lock:
            actuators = args.db.get_actuators_summary()
            args.pending_actuators_updates.clear()
        today = date.today()
        now_clock = time.monotonic()
        tolerance = args.actuators_tolerance
        for i, actuator in enumerate(actuators):
            last_seen = actuator['last_seen']
            is_online = (
                last_seen[0] == today
                and (now_clock - last_seen[1]) <= tolerance
            )
            actuators[i] = ActuatorUpdate(
                device_name=actuator['name'],
                state=json.dumps(actuator['state']),
                metadata=json.dumps(actuator['metadata']),
                timestamp=actuator['timestamp'].isoformat(),
                is_online=is_online,
            )
        logger.debug(
            'Novo relatório gerado: %d atuadores reportados',
            len(actuators),
        )
        report = ActuatorsReport(devices=actuators).SerializeToString()
        with args.db_actuators_report_lock:
            args.db.actuators_report = report


def build_command_message(type, body):
    match type:
        case CommandType.CT_ACTION | CommandType.CT_SET_STATE:
            msg = ActuatorCommand(type=type, body=body)
        case CommandType.CT_GET_STATE:
            msg = ActuatorCommand(type=type)
        case _:
            return None
    return msg.SerializeToString()


def send_actuator_command(args, actuator_name, command_type, command_body):
    command = build_command_message(command_type, command_body)
    if command is None:
        return None
    with args.db_actuators_lock:
        address = args.db.get_actuator_address_by_name(actuator_name)
    if address is None:
        return None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(address)
            sock.send(command)
            msg = sock.recv(1024)
        except OSError:
            return None
    reply = ActuatorComply()
    reply.ParseFromString(msg)
    state = json.loads(reply.update.state)
    metadata = json.loads(reply.update.metadata)
    timestamp = datetime.fromisoformat(reply.update.timestamp)
    with args.db_actuators_lock:
        args.db.add_actuator_update(
            actuator_name,
            state,
            metadata,
            timestamp,
        )
        args.pending_actuators_updates.set()
    return reply


def actuator_handler(args, sock, address):
    try:
        logger = logging.getLogger(f'ACTUATOR_HANLDER_{address}')
        msg = sock.recv(1024)
        update = ActuatorUpdate()
        update.ParseFromString(msg)
    except Exception as e:
        logger.error(
            'Erro durante o recebimento de uma atualização: (%s) %s',
            type(e).__name__,
            e,
        )
        raise e
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            logger.error(
                'Erro ao tentar enviar FIN para %s',
                address,
            )
        finally:
            sock.close()
    if not args.db.is_actuator_registered(update.device_name):
        logger.warning(
            'Atuador não registrado enviando atualizações: %s',
            update.device_name,
        )
        return
    logger.debug(
        'Atuador %s enviou uma atualização: (%s, %s)',
        update.device_name,
        update.timestamp,
        update.device_name,
    )
    state = json.loads(update.state)
    metadata = json.loads(update.metadata)
    timestamp = datetime.fromisoformat(update.timestamp)
    with args.db_actuators_lock:
        result = args.db.add_actuator_update(
            update.device_name,
            state,
            metadata,
            timestamp,
        )
        if result:
            args.pending_actuators_updates.set()


def actuators_listener(args):
    logger = logging.getLogger('ACTUATORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.actuators_port))
        sock.listen()
        logger.info(
            'Escutando por atualizações dos atuadores em (%s, %s)',
            args.host_ip,
            args.actuators_port,
        )
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=5) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, addrs = sock.accept()
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error(
                        'Erro ao tentar conexão com um atuador: (%s) %s',
                        type(e).__name__,
                        e,
                    )
                    continue
                with args.db_actuators_lock:
                    actuator_name = args.db.get_actuator_name_by_ip(addrs[0])
                if actuator_name is None:
                    logger.warning(
                        'Recebendo atualizações de um atuador '
                        'não registrado localizado em %s',
                        addrs[0],
                    )
                    continue
                try:
                    conn.settimeout(sock.gettimeout())
                    executor.submit(actuator_handler, args, conn, addrs)
                except Exception:
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        logger.error(
                            'Erro ao tentar enviar FIN para %s',
                            addrs,
                        )
                    finally:
                        conn.close()
                    raise
