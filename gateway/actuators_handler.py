import json
import time
import socket
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import ActuatorUpdate, ActuatorsReport
from messages_pb2 import CommandType, ActuatorCommand, ActuatorComply


def actuators_report_generator(args):
    logger = logging.getLogger('ACTUATORS_REPORT_GENERATOR')
    logger.info('Iniciando o gerador de relatórios dos atuadores')
    while not args.stop_flag.is_set():
        if not args.pending_actuators_updates.is_set():
            time.sleep(1.0)
            continue
        with args.db_actuators_lock:
            actuators = args.db.get_actuators_summary()
            args.pending_actuators_updates.clear()
        actuators = [
            ActuatorUpdate(
                device_name=actuator['name'],
                state=json.dumps(actuator['state']),
                metadata=json.dumps(actuator['metadata']),
                timestamp=actuator['timestamp'].isoformat(),
                is_online=actuator['is_online'],
            )
            for actuator in actuators
        ]
        logger.debug(
            'Novo relatório gerado: %d atuadores reportados',
            len(actuators),
        )
        report_msg = ActuatorsReport(devices=actuators).SerializeToString()
        with args.db_actuators_report_lock:
            args.db.att_actuators_report(report_msg)


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
        except Exception:
            msg = None
        finally:
            sock.shutdown(socket.SHUT_RDWR)
    if msg is None:
        with args.db_actuators_lock:
            args.db.mark_actuator_as_offline(actuator_name)
            args.pending_actuators_updates.set()
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


def actuator_handler(args, sock):
    logger = logging.getLogger(f'ACTUATOR_HANLDER_{threading.get_ident()}')
    try:
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
        sock.shutdown(socket.SHUT_RDWR)
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
                    conn, _ = sock.accept()
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
                    executor.submit(actuator_handler, args, conn)
                except:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    raise
