import json
import time
import socket
import logging
import datetime
from db.repositories import get_actuators_repository
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import ActuatorUpdate, ActuatorsReport
from messages_pb2 import CommandType, ActuatorCommand, ActuatorComply


def actuators_report_generator(args):
    actuators_repository = get_actuators_repository()
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
        args.pending_actuators_updates.clear()
        actuators = actuators_repository.get_all_actuators()
        today = datetime.datetime.now(datetime.UTC).date()
        now_clock = time.monotonic()
        tolerance = args.actuators_tolerance
        summary = []
        for actuator in actuators:
            is_online = (
                actuator.last_seen_date == today
                and (now_clock - actuator.last_seen_clock) <= tolerance
            )
            summary.append(ActuatorUpdate(
                device_name=f'{actuator.category}-{actuator.id}',
                state=json.dumps(actuator.device_state),
                metadata=json.dumps(actuator.device_metadata),
                timestamp=actuator.timestamp.isoformat(),
                is_online=is_online,
            ))
        logger.debug(
            'Novo relatório gerado: %d atuadores reportados',
            len(actuators),
        )
        report = ActuatorsReport(devices=summary).SerializeToString()
        with args.db_actuators_report_lock:
            args.actuators_report = report


def build_command_message(type, body):
    match type:
        case CommandType.CT_ACTION | CommandType.CT_SET_STATE:
            msg = ActuatorCommand(type=type, body=body)
        case CommandType.CT_GET_STATE:
            msg = ActuatorCommand(type=type)
        case _:
            return None
    return msg.SerializeToString()


def send_actuator_command(args, actuator_id, actuator_category, command_type, command_body):
    actuators_repository = get_actuators_repository()
    command = build_command_message(command_type, command_body)
    if command is None:
        return None
    actuator = actuators_repository.get_actuator(actuator_id, actuator_category)
    if actuator is None:
        return None
    address = (actuator.ip_address, actuator.communication_port)
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
    timestamp = datetime.datetime.fromisoformat(reply.update.timestamp)
    actuators_repository.register_actuator_update(
        actuator_id=actuator_id,
        actuator_category=actuator_category,
        device_state=state,
        device_metadata=metadata,
        timestamp=timestamp,
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
    actuator_category, actuator_id = update.device_name.split('-')
    actuator_id = int(actuator_id)
    actuators_repository = get_actuators_repository()
    actuator = actuators_repository.get_actuator(actuator_id, actuator_category)
    if actuator is None:
        logger.warning(
            'Recebendo atualizações de um atuador '
            'não registrado localizado em %s',
            address[0],
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
    timestamp = datetime.datetime.fromisoformat(update.timestamp)
    actuators_repository.register_actuator_update(
        actuator_id=actuator_id,
        actuator_category=actuator_category,
        device_state=state,
        device_metadata=metadata,
        timestamp=timestamp,
    )
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
