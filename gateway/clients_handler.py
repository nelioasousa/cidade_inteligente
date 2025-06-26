import time
import json
import socket
import logging
import datetime
import threading
from struct import pack
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import SensorReading, SensorsReport


def send_report(args, sock, addrs):
    logger = logging.getLogger('SEND_REPORT')
    if args.verbose:
        logger.info('Enviando relatório para cliente em %s', addrs)
    with args.db_sensors_lock:
        sensors_summary = args.db.get_sensors_summary()
    today = datetime.date.today()
    now_clock = time.monotonic()
    for i, sensor_summary in enumerate(sensors_summary):
        last_seen = sensor_summary['last_seen']
        is_online = (
            last_seen[0] == today
            and (now_clock - last_seen[1]) <= args.sensors_tolerance
        )
        sensors_summary[i] = SensorReading(
            device_name=sensor_summary['device_name'],
            reading_value=str(sensor_summary['reading_value']),
            timestamp=sensor_summary['timestamp'].isoformat(),
            metadata=json.dumps(sensor_summary['metadata']),
            is_online=is_online,
        )
    if args.verbose:
        logger.info('Número de sensores reportados: %d', len(sensors_summary))
    report_msg = SensorsReport(readings=sensors_summary).SerializeToString()
    report_msg = pack('!I', len(report_msg)) + report_msg
    sock.sendall(report_msg)


def client_handler(args, sock, addrs):
    logger = logging.getLogger(f'CLIENT_HANDLER_{threading.get_ident()}')
    logger.info('Gerenciando conexão com o cliente em %s', addrs)
    try:
        sock.settimeout(args.client_timeout)
        while not args.stop_flag.is_set():
            send_report(args, sock, addrs)
            try:
                _ = sock.recv(1024)
            except TimeoutError:
                continue
    except Exception as e:
        logger.error(
            'Erro durante conexão com o cliente em %s: (%s) %s',
            addrs, type(e).__name__, e
        )
        raise e
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def clients_listener(args):
    logger = logging.getLogger('CLIENTS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.clients_port))
        sock.listen()
        logger.info(
            'Escutando pedidos de conexão dos clientes em (%s, %s)',
            args.host_ip, args.clients_port
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
                        'Erro ao tentar conexão com um novo cliente: (%s) %s',
                        type(e).__name__, e
                    )
                    continue
                executor.submit(client_handler, args, conn, addrs)
