import json
import time
import socket
import logging
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


def actuator_handler(args, sock, ip_address):
    try:
        logger = logging.getLogger(f'ACTUATOR_HANDLER_{ip_address}')
        logger.info('Gerenciando conexão com o atuador em %s', ip_address)
        with args.db_actuators_lock:
            actuator = args.db.get_actuator_name_by_ip(ip_address)
        if actuator is None:
            logger.warning(
                'Não há nenhum atuador registrado com o endereço %s. '
                'Encerrando conexão por segurança.',
                ip_address,
            )
            return
    except:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        raise
    try:
        sock.settimeout(args.base_timeout)
        msg = sock.recv(1024)
        update = ActuatorUpdate()
        update.ParseFromString(msg)
    except Exception as e:
        with args.db_actuators_lock:
            args.db.mark_actuator_as_offline(actuator)
            args.pending_actuators_updates.set()
        logger.error(
            'Erro ao receber atualizações do atuador %s: (%s) %s',
            actuator,
            type(e).__name__,
            e,
        )
        raise e
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    logger.debug(
        'Atuador %s enviou uma atualização: (%s, %s)',
        actuator,
        update.timestamp,
        update.device_name,
    )
    state = json.loads(update.state)
    metadata = json.loads(update.metadata)
    timestamp = datetime.fromisoformat(update.timestamp)
    with args.db_actuators_lock:
        result = args.db.add_actuator_update(
            actuator,
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
                executor.submit(actuator_handler, args, conn, addrs[0])
