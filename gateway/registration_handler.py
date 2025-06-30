import time
import json
import socket
import logging
from threading import get_ident
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import Address, JoinRequest, JoinReply, DeviceType


def multicast_location(args):
    logger = logging.getLogger('MULTICASTER')
    logger.info(
        'Enviando endereço de registro para grupo multicast (%s, %s)',
        args.multicast_ip, args.multicast_port
    )
    addrs = Address(ip=args.host_ip, port=args.registration_port)
    addrs = addrs.SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        while not args.stop_flag.is_set():
            try:
                sock.sendto(addrs, (args.multicast_ip, args.multicast_port))
            except Exception as e:
                logger.error(
                    'Erro ao enviar mensagem para o grupo multicast: (%s) %s',
                    type(e).__name__,
                    e,
                )
            time.sleep(args.multicast_interval)


def registration_handler(args, sock):
    try:
        logger = logging.getLogger(f'REGISTRATION_HANDLER_{get_ident()}')
        logger.info('Processando requisição de registro')
        msg = sock.recv(1024)
        request = JoinRequest()
        request.ParseFromString(msg)
        device_info = request.device_info
        device_addrs = request.device_address
        match request.device_info.type:
            case DeviceType.DT_SENSOR:
                report_port = args.sensors_port
                with args.db_sensors_lock:
                    args.db.register_sensor(
                        name=device_info.name,
                        address=(device_addrs.ip, device_addrs.port),
                        metadata=json.loads(device_info.metadata),
                    )
            case DeviceType.DT_ACTUATOR:
                report_port = args.actuators_port
                with args.db_actuators_lock:
                    args.db.register_actuator(
                        name=device_info.name,
                        address=(device_addrs.ip, device_addrs.port),
                        state=json.loads(device_info.state),
                        metadata=json.loads(device_info.metadata),
                        timestamp=datetime.fromisoformat(device_info.timestamp),
                    )
            case _:
                raise ValueError('Invalid DeviceType')
        reply = JoinReply(report_port=report_port)
        sock.send(reply.SerializeToString())
        logger.info('Ingresso bem-sucedido: %s', device_info.name)
    except Exception as e:
        logger.error(
            'Erro durante registro do dispositivo %s: (%s) %s',
            device_info.name,
            type(e).__name__,
            e,
        )
        raise e
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def registration_listener(args):
    logger = logging.getLogger('REGISTRATION_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', args.registration_port))
            sock.listen()
        except:
            args.stop_flag.set()
            raise
        logger.info(
            'Escutando por requisições de registro em (%s, %s)',
            args.host_ip,
            args.registration_port,
        )
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=5) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, _ = sock.accept()
                except TimeoutError:
                    continue
                except:
                    args.stop_flag.set()
                    raise
                try:
                    executor.submit(registration_handler, args, conn)
                except:
                    args.stop_flag.set()
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    raise
