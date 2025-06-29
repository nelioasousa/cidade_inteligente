import sys
import json
import socket
import time
import datetime
import random
import threading
import logging
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceType, DeviceInfo, JoinRequest, JoinReply


def gateway_discoverer(args):
    logger = logging.getLogger('GATEWAY_DISCOVERER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(args.multicast_ip) + socket.inet_aton('0.0.0.0'),
        )
        logger.info(
            'Procurando pelo Gateway no grupo multicast (%s, %s)',
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
                    args.gateway_ip is not None
                    and seq_fails >= args.disconnect_after
                ):
                    logger.warning(
                        'Gateway em %s está offline: falhou %d '
                        'transmissões em sequência. Desconectando...',
                        args.gateway_ip,
                        args.disconnect_after,
                    )
                    disconnect_device(args)
                continue
            gateway_addrs = Address()
            gateway_addrs.ParseFromString(msg)
            seq_fails = 0
            if gateway_addrs.ip == args.gateway_ip:
                continue
            if args.gateway_ip is not None:
                logger.warning(
                    'Gateway realocado de %s para %s. Desconectando...',
                    args.gateway_ip,
                    gateway_addrs.ip,
                )
                disconnect_device(args)
            try_to_register(args, (gateway_addrs.ip, gateway_addrs.port), logger)


def disconnect_device(args):
    args.gateway_ip = None
    args.transmission_port = None
    return


def try_to_register(args, address, logger):
    logger.info('Tentando registro no endereço %s', address)
    sensor_info = DeviceInfo(
        type=DeviceType.DT_SENSOR,
        name=args.name,
        metadata=json.dumps(args.metadata),
    )
    sensor_addrs = Address(ip=args.host_ip, port=0)
    join_request = JoinRequest(
        device_info=sensor_info, device_address=sensor_addrs,
    )
    join_request = join_request.SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(address)
            sock.send(join_request)
            join_reply = JoinReply()
            join_reply.ParseFromString(sock.recv(1024))
        except Exception as e:
            logger.warning(
                'Erro durante tentativa de registro em %s: (%s) %s',
                address,
                type(e).__name__,
                e,
            )
            return
        finally:
            sock.shutdown(socket.SHUT_RDWR)
    args.gateway_ip = address[0]
    args.transmission_port = join_reply.report_port
    logger.info('Registro bem-sucedido com o Gateway em %s', address[0])
    return


def get_reading(args):
    temp = args.temperature + random.random() - 0.5
    temp = min(max(temp, args.min_temperature), args.max_temperature)
    args.temperature = temp
    return temp


def transmit_readings(args):
    logger = logging.getLogger('READINGS_TRANSMITER')
    logger.info('Começando a transmissão de leituras para o Gateway')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while not args.stop_flag.is_set():
            if args.gateway_ip is None:
                logger.info('Transmissão interrompida. Sem conexão com o Gateway')
                time.sleep(1.0)
                continue
            reading = SensorReading(
                device_name=args.name,
                reading_value=get_reading(args),
                timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                metadata=json.dumps(args.metadata),
            )
            addrs = (args.gateway_ip, args.transmission_port)
            sock.sendto(reading.SerializeToString(), addrs)
            logger.debug('Leitura de temperatura enviada para %s', addrs)
            time.sleep(args.report_interval)


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        transmiter = threading.Thread(target=transmit_readings, args=(args,))
        transmiter.start()
        gateway_discoverer(args)
    except BaseException as e:
        args.stop_flag.set()
        if isinstance(e, KeyboardInterrupt):
            print('\nSHUTTING DOWN...')
        else:
            raise e
    finally:
        transmiter.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sensor de temperatura')

    parser.add_argument(
        '--name', type=str, default='01',
        help='Nome que unicamente identifica o sensor de temperatura.'
    )

    parser.add_argument(
        '--multicast_ip', type=str, default='224.0.1.0',
        help='IP multicast para descobrimento do Gateway.'
    )

    parser.add_argument(
        '--multicast_port', type=int, default=12345,
        help='Porta na qual escutar por mensagens do grupo multicast.'
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
    args.name = f'Temperature-{args.name}'

    # Timeouts
    args.base_timeout = 2.0
    args.multicast_timeout = 5.0

    # Host IP
    args.host_ip = socket.gethostbyname(socket.gethostname())

    # Gateway
    args.gateway_ip = None
    args.transmission_port = None

    # Metadata
    args.metadata = {
        'UnitName': 'Celsius',
        'UnitSymbol': '°C',
        'Location': {'Latitude': -3.733486, 'Longitude': -38.570860},
    }

    # Events
    args.stop_flag = threading.Event()

    return _run(args)


if __name__ == '__main__':
    main()
