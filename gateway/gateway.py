import sys
import socket
import threading
import time
import json
import logging
from struct import pack
from datetime import datetime
from db import Database
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import message
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceType, JoinRequest, JoinReply
from messages_pb2 import ActuatorUpdate
from messages_pb2 import SensorsReport


def multicast_location(args):
    logger = logging.getLogger('MULTICASTER')
    logger.info(
        'Multicasting endereço de registro de dispositivos: (%s, %s)',
        args.host_ip, args.registration_port
    )
    addrs = Address(ip=args.host_ip, port=args.registration_port)
    addrs = addrs.SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        try:
            while not args.stop_flag.is_set():
                sock.sendto(addrs, (args.multicast_ip, args.multicast_port))
                time.sleep(args.multicast_interval)
        except Exception as e:
            logger.error('Erro durante multicast: (%s) %s', type(e).__name__, e)


def join_handler(args, sock, addrs):
    logger = logging.getLogger(f'JOIN_HANDLER_{threading.get_ident()}')
    logger.info(
        'Processando requisição de ingresso de %s', addrs
    )
    try:
        sock.settimeout(args.base_timeout)
        req = JoinRequest()
        req.ParseFromString(sock.recv(1024))
        if req.device_info.type is DeviceType.SENSOR:
            report_interval = args.sensors_report_interval
            report_port = args.sensors_port
            with args.db_sensors_lock:
                args.db.register_sensor(
                    name=req.device_info.name,
                    address=(req.device_address.ip, req.device_address.port),
                    metadata=json.loads(req.device_info.metadata),
                )
        elif req.device_info.type is DeviceType.ACTUATOR:
            report_interval = args.actuators_report_interval
            report_port = args.actuators_port
            with args.db_actuators_lock:
                args.db.register_actuator(
                    name=req.device_info.name,
                    address=(req.device_address.ip, req.device_address.port),
                    state=json.loads(req.device_info.state),
                    metadata=json.loads(req.device_info.metadata),
                )
        else:
            raise RuntimeError('Invalid device type')
        reply = JoinReply(
            report_port=report_port,
            report_interval=report_interval,
        )
        sock.send(reply.SerializeToString())
        logger.info(
            'Ingresso bem-sucedido do dispositivo %s em %s',
            req.device_info.name, addrs
        )
    except Exception as e:
        logger.error(
            'Erro no processamento da requisição de %s: (%s) %s',
            addrs, type(e).__name__, e
        )
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def registration_listener(args):
    logger = logging.getLogger('REGISTRATION_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((args.host_ip, args.registration_port))
        sock.listen()
        logger.info(
            'Escutando requisições de registro em (%s, %s)',
            args.host_ip, args.registration_port
        )
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, addrs = sock.accept()
                except TimeoutError:
                    continue
                executor.submit(join_handler, args, conn, addrs)


def sensors_listener(args):
    logger = logging.getLogger('SENSORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((args.host_ip, args.sensors_port))
        logger.info(
            'Escutando por dados sensoriais em (%s, %s)',
            args.host_ip, args.sensors_port
        )
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            try:
                msg, _ = sock.recvfrom(1024)
                reading = SensorReading()
                reading.ParseFromString(msg)
            except (TimeoutError, message.DecodeError):
                continue
            name = reading.device_name
            if name.startswith('Temperature'):
                value = float(reading.reading_value)
                timestamp = datetime.fromisoformat(reading.timestamp)
                metadata = json.loads(reading.metadata)
                if args.verbose:
                    logger.info(
                        'Leitura de temperatura recebida: (%s, %s %s, %s)',
                        name, value, metadata['UnitSymbol'], reading.timestamp
                    )
            else:
                continue
            with args.db_sensors_lock:
                result = args.db.add_sensor_reading(name, value, timestamp, metadata)
            if args.verbose and not result:
                logger.info(
                    'Recebendo leituras de um sensor desconhecido: %s', name
                )


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
        value = update.action_value.strip().upper()
        timestamp = datetime.fromisoformat(update.timestamp)
        state = json.loads(update.state)
        metadata = json.loads(update.metadata)
        if args.verbose:
            logger.info(
                'Atualização de lâmpada recebida: (%s, %s, %s)',
                name, update.timestamp, value
            )
    else:
        return
    with args.db_actuators_lock:
        result = args.db.add_actuator_update(
            name, value, timestamp, state, metadata
        )
    if args.verbose and not result:
        logger.info(
            'Recebendo atualizações de um atuador desconhecido: %s', name
        )


def actuators_listener(args):
    logger = logging.getLogger('ACTUATORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((args.host_ip, args.actuators_port))
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


def send_report(args, sock, addrs):
    logger = logging.getLogger('SEND_REPORT')
    if args.verbose:
        logger.info('Enviando relatório para cliente em %s', addrs)
    with args.db_sensors_lock:
        sensors_summary = args.db.get_sensors_summary()
    for i, sensor_summary in enumerate(sensors_summary):
        not_seen_since = (time.monotonic() - sensor_summary['last_seen'])
        sensors_summary[i] = SensorReading(
            device_name=sensor_summary['device_name'],
            reading_value=str(sensor_summary['reading_value']),
            timestamp=sensor_summary['timestamp'].isoformat(),
            metadata=json.dumps(sensor_summary['metadata']),
            is_online=(not_seen_since <= 2 * args.sensors_report_interval),
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
        sock.bind((args.host_ip, args.clients_port))
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


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        jlistener = threading.Thread(
            target=registration_listener, args=(args,)
        )
        slistener = threading.Thread(
            target=sensors_listener, args=(args,)
        )
        alistener = threading.Thread(
            target=actuators_listener, args=(args,)
        )
        multicaster = threading.Thread(
            target=multicast_location, args=(args,)
        )
        jlistener.start()
        slistener.start()
        alistener.start()
        multicaster.start()
        clients_listener(args)
    except BaseException as e:
        args.stop_flag.set()
        if isinstance(e, KeyboardInterrupt):
            print('\nDESLIGANDO...')
        else:
            raise e
    finally:
        jlistener.join()
        slistener.join()
        alistener.join()
        multicaster.join()
        args.db.persist()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Gateway')

    parser.add_argument(
        '--clients_port', type=int, default=5000,
        help='Porta para comunicação com os clientes. Usa TCP.'
    )

    parser.add_argument(
        '--registration_port', type=int, default=50111,
        help='Porta em que os dispositivos se registram no Gateway. Usa TCP.'
    )

    parser.add_argument(
        '--sensors_port', type=int, default=50222,
        help='Porta de recebimento de dados sensoriais. Usa UDP.'
    )

    parser.add_argument(
        '--actuators_port', type=int, default=50333,
        help='Porta de recebimento dos dados dos atuadores. Usa UDP.'
    )

    parser.add_argument(
        '--multicast_ip', type=str, default='224.0.1.0',
        help='IP para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_port', type=int, default=12345,
        help='Porta para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_interval', type=float, default=2.5,
        help='Intervalo de envio do endereço do Gateway para o grupo multicast.'
    )

    parser.add_argument(
        '--sensors_report_interval', type=float, default=1.0,
        help='Intervalo de envio de dados dos sensores.'
    )

    parser.add_argument(
        '--actuators_report_interval', type=float, default=5.0,
        help='Intervalo de envio de dados dos atuadores.'
    )

    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Torna o Gateway verboso ao logar informações.'
    )

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN" e "ERROR".'
    )

    parser.add_argument(
        '-c', '--clear', action='store_true',
        help='Limpar o banco de dados ao iniciar.'
    )

    args = parser.parse_args()
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'
    if args.level == 'DEBUG':
        args.verbose = True
    args.base_timeout = 2.5
    args.client_timeout = 5.0
    args.host_ip = socket.gethostbyname(socket.gethostname())
    args.db = Database(clear=args.clear)
    args.stop_flag = threading.Event()
    args.db_sensors_lock = threading.Lock()
    args.db_actuators_lock = threading.Lock()

    return _run(args)


if __name__ == '__main__':
    main()
