import json
import socket
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import message
from messages_pb2 import ActuatorUpdate, ActuatorComply, ComplyStatus


def send_command(args, device_name, command_message_bytes):
    logger = logging.getLogger(f'SEND_COMMAND_TO_{device_name}')
    logger.info('Tentando enviar comando para %s', device_name)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        actuator = args.db.get_actuator(device_name)
        if actuator is None:
            logger.warning('Actuator %s não está registrado', device_name)
            return None
        sock.settimeout(args.actuators_timeout)
        try:
            sock.connect(actuator['address'])
        except OSError as e:
            logger.error(
                'Erro ao estabelecer conexão com %s: (%s) %s',
                device_name, type(e).__name__, e
            )
            msg = None
        try:
            sock.send(command_message_bytes)
        except OSError as e:
            logger.error(
                'Erro ao enviar comando para %s: (%s) %s',
                device_name, type(e).__name__, e
            )
            msg = None
        try:
            msg = sock.recv(1024)
        except OSError as e:
            logger.error(
                'Erro ao receber resposta de %s: (%s) %s',
                device_name, type(e).__name__, e
            )
            msg = None
        if msg is None:
            with args.db_actuators_lock:
                args.db.mark_actuator_as_offline(device_name)
                args.pending_actuators_updates.set()
            return None
        reply = ActuatorComply()
        reply.ParseFromString(msg)
        if reply.status is ComplyStatus.OK:
            name = reply.update.device_name
            state = json.loads(reply.update.state)
            metadata = json.loads(reply.update.metadata)
            timestamp = datetime.fromisoformat(reply.update.timestamp)
            with args.db_actuators_lock:
                args.db.add_actuator_update(name, state, metadata, timestamp)
                args.pending_actuators_updates.set()
        return reply


def actuator_handler(args, sock, addrs):
    logger = logging.getLogger(f'ACTUATOR_HANDLER_{threading.get_ident()}')
    logger.info('Gerenciando conexão com o atuador em %s', addrs)
    try:
        msg, _ = sock.recvfrom(1024)
        update = ActuatorUpdate()
        update.ParseFromString(msg)
    except (TimeoutError, message.DecodeError):
        return
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    name = update.device_name
    if name.startswith('Lamp'):
        state = json.loads(update.state)
        metadata = json.loads(update.metadata)
        timestamp = datetime.fromisoformat(update.timestamp)
        if args.verbose:
            logger.info(
                'Atualização de lâmpada recebida: (%s, %s, %s)',
                name, update.timestamp, 'ON' if state['is_on'] else 'OFF'
            )
    else:
        return
    with args.db_actuators_lock:
        result = args.db.add_actuator_update(name, state, metadata, timestamp)
        if result:
            args.pending_actuators_updates.set()
    if args.verbose and not result:
        logger.info(
            'Recebendo atualizações de um atuador desconhecido: %s', name
        )


def actuators_listener(args):
    logger = logging.getLogger('ACTUATORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', args.actuators_port))
        sock.listen()
        logger.info(
            'Escutando por atualizações dos atuadores em (%s, %s)',
            args.host_ip, args.actuators_port
        )
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, addrs = sock.accept()
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error(
                        'Erro ao tentar conexão com um atuador: (%s) %s',
                        type(e).__name__, e
                    )
                    continue
                executor.submit(actuator_handler, args, conn, addrs)
