import sys
import json
import socket
import time
import datetime
import random
import threading
import logging
from functools import wraps
import pika
from messages_pb2 import Address, SensorReading


def broker_discoverer(args):
    logger = logging.getLogger('BROKER_DISCOVERER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(args.multicast_ip) + socket.inet_aton('0.0.0.0'),
        )
        logger.info(
            'Procurando broker no grupo multicast (%s, %s)',
            args.multicast_ip,
            args.multicast_port,
        )
        sock.settimeout(args.multicast_timeout)
        seq_fails = 0
        while not args.stop_flag.is_set():
            try:
                msg = sock.recv(1024)
            except TimeoutError:
                seq_fails += 1
                if (
                    args.message_broker_ip is not None
                    and seq_fails >= args.disconnect_after
                ):
                    logger.warning(
                        'Gateway está offline. Parando transmissão de leituras...'
                    )
                    disconnect_device(args)
                continue
            addresses = Address()
            addresses.ParseFromString(msg)
            seq_fails = 0
            if addresses.broker_ip == args.message_broker_ip:
                continue
            if args.message_broker_ip is not None:
                logger.warning(
                    'Broker realocado de %s para %s. Desconectando...',
                    args.message_broker_ip,
                    addresses.broker_ip,
                )
                disconnect_device(args)
            register_broker(args, addresses.broker_ip, addresses.broker_port)


def disconnect_device(args):
    with args.address_lock:
        args.message_broker_ip = None
        args.message_broker_port = None
    args.disconnect_flag.set()


def register_broker(args, broker_ip, broker_port):
    with args.address_lock:
        args.message_broker_ip = broker_ip
        args.message_broker_port = broker_port


def get_reading(args):
    temp = args.temperature + random.random() - 0.5
    temp = min(max(temp, args.min_temperature), args.max_temperature)
    args.temperature = temp
    return temp


def publish_readings(args):
    logger = logging.getLogger('READINGS_PUBLISHER')
    while not args.stop_flag.is_set():
        with args.address_lock:
            broker_ip = args.message_broker_ip
            broker_port = args.message_broker_port
        if broker_ip is None:
            logger.info('Sem conexão com o Broker')
            time.sleep(1.0)
            continue
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=broker_ip,
                port=broker_port,
                socket_timeout=args.base_timeout,
            )
        )
        channel = connection.channel()
        try:
            channel.exchange_declare(exchange='readings', exchange_type='fanout')
            while (
                not args.stop_flag.is_set()
                and not args.disconnect_flag.is_set()
            ):
                reading = SensorReading(
                    device_name=args.name,
                    reading_value=get_reading(args),
                    timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                    metadata=json.dumps(args.metadata),
                ).SerializeToString()
                channel.basic_publish(exchange='logs', routing_key='', body=reading)
                time.sleep(args.report_interval)
        finally:
            channel.close()
            connection.close()
            args.disconnect_flag.clear()


# def transmit_readings(args):
#     logger = logging.getLogger('READINGS_TRANSMITER')
#     logger.info('Começando a transmissão de leituras para o Gateway')
#     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
#         while not args.stop_flag.is_set():
#             with args.address_lock:
#                 addrs = (args.gateway_ip, args.transmission_port)
#             if addrs[0] is None:
#                 logger.info('Transmissão interrompida. Sem conexão com o Gateway')
#                 time.sleep(2.0)
#                 continue
#             reading = SensorReading(
#                 device_name=args.name,
#                 reading_value=get_reading(args),
#                 timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
#                 metadata=json.dumps(args.metadata),
#             )
#             sock.sendto(reading.SerializeToString(), addrs)
#             logger.debug('Leitura de temperatura enviada para %s', addrs)
#             time.sleep(args.report_interval)


def stop_wrapper(func, stop_flag):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            stop_flag.set()
    return wrapper


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        publisher = threading.Thread(
            target=stop_wrapper(publish_readings, args.stop_flag),
            args=(args,)
        )
        publisher.start()
        broker_discoverer(args)
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN...')
    finally:
        args.stop_flag.set()
        publisher.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sensor de temperatura')

    parser.add_argument(
        '--id', type=int, default=1,
        help='Nome que unicamente identifica o sensor de temperatura.'
    )

    parser.add_argument(
        '--multicast_ip', type=str, default='224.0.1.0',
        help='IP multicast para descobrimento do Gateway.'
    )

    parser.add_argument(
        '--multicast_port', type=int, default=50444,
        help='Porta na qual escutar por mensagens do grupo multicast.'
    )

    parser.add_argument(
        '--message_broker_ip', type=str, default='localhost',
        help='Endereço IP do message broker.'
    )

    parser.add_argument(
        '--message_broker_port', type=int, default=5672,
        help='Porta de comunicação com o message broker.'
    )

    parser.add_argument(
        '--report_interval', type=float, default=5.0,
        help='Intervalo entre o envio de leituras.'
    )

    parser.add_argument(
        '--temperature', type=float, default=25.0,
        help='Temperatura inicial do sensor em °C.'
    )

    parser.add_argument(
        '--max_temperature', type=float, default=40.0,
        help='Temperatura máximo do sensor em °C.'
    )

    parser.add_argument(
        '--min_temperature', type=float, default=20.0,
        help='Temperatura mínima do sensor em °C.'
    )

    parser.add_argument(
        '--disconnect_after', type=int, default=3,
        help='Número de falhas sequenciais necessárias para desconectar o Gateway.'
    )

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN", "ERROR".'
    )

    args = parser.parse_args()

    # Logging
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'

    # Identifier
    args.name = f'temperature-{args.id}'

    # Timeouts
    args.base_timeout = 2.0
    args.multicast_timeout = 5.0

    # Host IP
    args.host_ip = socket.gethostbyname('localhost')

    # Broker
    args.message_broker_ip = None
    args.message_broker_port = None

    # Metadata
    args.metadata = {
        'UnitName': 'Celsius',
        'UnitSymbol': '°C',
        'Location': {'Latitude': -3.733486, 'Longitude': -38.570860},
    }

    # Events and locks
    args.stop_flag = threading.Event()
    args.disconnect_flag = threading.Event()
    args.address_lock = threading.Lock()

    return _run(args)


if __name__ == '__main__':
    main()
