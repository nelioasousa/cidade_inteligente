import sys
import json
import time
import socket
import threading
import logging
from copy import deepcopy
from messages_pb2 import SensorsReport, ActuatorsReport, SendNextReport
from messages_pb2 import ConnectionRequest
from messages_pb2 import SensorReading, ActuatorUpdate


def recvall(sock, retries=5):
    chunks = []
    fail_count = 0
    while True:
        try:
            chunk = sock.recv(1024)
        except TimeoutError:
            fail_count += 1
            if fail_count > retries:
                break
            continue
        if chunk:
            fail_count = 0
            chunks.append(chunk)
            continue
        else:
            raise ConnectionError('Remote side closed the connection')
    if not chunks:
        raise TimeoutError('No data to recieve')
    return b''.join(chunks)  


def register_sensors_report(args, report):
    with args.sensors_report_lock:
        args.sensors_report = (args.sensors_report[0] + 1, report)


def register_actuators_report(args, report):
    with args.actuators_report_lock:
        args.actuators_report = (args.actuators_report[0] + 1, report)


def sensors_report_listener(args):
    logger = logging.getLogger('SENSORS_REPORT')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # sock.settimeout(args.streams_timeout)
        sock.bind('', 0)
        sock.listen()
        args.sensors_port = sock.getsockname()[1]
        logger.info(
            'Esperando relatórios dos sensores na porta %d',
            args.sensors_port,
        )
        try:
            conn, _ = sock.accept()
            # conn.settimeout(args.base_timeout)
        except Exception as e:
            args.stop_flag.set()
            logger.error(
                'Erro ao estabelecer conexão com o Gateway: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        send_next_report = SendNextReport().SerializeToString()
        while not args.stop_flag.is_set():
            try:
                report = SensorsReport()
                report.ParseFromString(recvall(conn))
            except Exception as e:
                args.stop_flag.set()
                logger.error(
                    'Erro ao receber relatório: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            register_sensors_report(args, report)
            try:
                conn.send(send_next_report)
            except Exception as e:
                args.stop_flag.set()
                logger.error(
                    'Erro ao solicitar novo relatório: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e


def actuators_report_listener(args):
    logger = logging.getLogger('ACTUATORS_REPORT')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # sock.settimeout(args.streams_timeout)
        sock.bind('', 0)
        sock.listen()
        args.actuators_port = sock.getsockname()[1]
        logger.info(
            'Esperando relatórios dos atuadores na porta %d',
            args.actuators_port,
        )
        try:
            conn, _ = sock.accept()
            # conn.settimeout(args.base_timeout)
        except Exception as e:
            args.stop_flag.set()
            logger.error(
                'Erro ao estabelecer conexão com o Gateway: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        send_next_report = SendNextReport().SerializeToString()
        while not args.stop_flag.is_set():
            try:
                report = ActuatorsReport()
                report.ParseFromString(recvall(conn))
            except Exception as e:
                args.stop_flag.set()
                logger.error(
                    'Erro ao receber relatório: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            register_actuators_report(args, report)
            try:
                conn.send(send_next_report)
            except Exception as e:
                args.stop_flag.set()
                logger.error(
                    'Erro ao solicitar novo relatório: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e


def print_help():
    print('The following commands are available:')
    print('  help      : show this help message')
    print('  sensors   : list sensors devices')
    print('  actuators : list actuators devices')
    print('  actuator <name> <command>')
    print('            : send command <command> to actuator <name>')
    print('  actuator <name> <key> <value>')
    print('            : set state <key> to <value> for actuator <name>', end='\n\n')


def print_sensor_summary(sensor):
    metadata = json.loads(sensor.metadata)
    print('[INFO]')
    print(' Sensor    : %s' %sensor.device_name)
    print(' Reading   : %.3f' %sensor.reading_value)
    print(' Timestamp : %s' %sensor.timestamp)
    print(' Status    : %s' %('ONLINE' if sensor.is_online else 'OFFLINE'))
    if metadata:
        max_key_length = max(len(k) for k in metadata)
        print('[METADATA]')
        for key, value in metadata:
            print(f' {key.rjust(max_key_length)} : {value}')
    print()


def print_actuator_summary(actuator):
    state = json.loads(actuator.state)
    metadata = json.loads(actuator.metadata)
    print('[INFO]')
    print(' Actuator  : %s' %actuator.device_name)
    print(' Timestamp : %s' %actuator.timestamp)
    print(' Status    : %s' %('ONLINE' if actuator.is_online else 'OFFLINE'))
    if state:
        max_key_length = max(len(k) for k in state)
        print('[STATE]')
        for key, value in state:
            print(f' {key.ljust(max_key_length)} : {value}')
    if metadata:
        max_key_length = max(len(k) for k in metadata)
        print('[METADATA]')
        for key, value in metadata:
            print(f' {key.ljust(max_key_length)} : {value}')
    print()


def print_sensors(args):
    with args.sensors_report_lock:
        sensors = deepcopy(args.sensors_report[1])
    for sensor in sensors.devices:
        print_sensor_summary(sensor)


def print_actuators(args):
    with args.actuators_report_lock:
        actuators = deepcopy(args.actuators_report[1])
    for actuator in actuators.devices:
        print_actuator_summary(actuator)


def client_cli(args, sock):
    while not args.stop_flag.is_set():
        command = input('>>> ').strip().lower()
        match command:
            case 'help':
                print_help()
            case 'sensors':
                print_sensors(args)
            case 'actuators':
                print_actuators(args)


def connect_to_gateway(args):
    logger = logging.getLogger('GATEWAY_CONNECTION')
    logger.info(
        'Tentando conexão com o Gateway em (%s, %s)',
        args.gateway_ip,
        args.gateway_port,
    )
    sensors_listener = threading.Thread(
        target=sensors_report_listener, args=(args,),
    )
    actuators_listener = threading.Thread(
        target=actuators_report_listener, args=(args,),
    )
    sensors_listener.start()
    actuators_listener.start()
    # Esperar as threads ouvintes estarem configuradas
    while (args.sensors_port is None or args.actuators_port is None):
        time.sleep(1.0)
    conn_msg = ConnectionRequest(
        sensors_port=args.sensors_port, actuators_port=args.actuators_port,
    ).SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # sock.settimeout(args.connect_timeout)
        sock.connect((args.gateway_ip, args.gateway_port))
        try:
            sock.send(conn_msg)
            logger.info('Conexão com o Gateway bem-sucedida')
        except Exception as e:
            logger.error(
                'Erro durante o envio do pedido de conexão: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        try:
            client_cli(args, sock)
        except:
            args.stop_flag.set()
            raise
        finally:
            sensors_listener.join()
            actuators_listener.join()


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        connect_to_gateway(args)
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN...')


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente simples em Python')

    parser.add_argument(
        '--gateway_ip', type=str, default='localhost',
        help='IP do Gateway (servidor).'
    )

    parser.add_argument(
        '--gateway_port', type=int, default=5000,
        help='Porta do Gateway para comunicação com clientes.'
    )

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN", "ERROR".'
    )

    args = parser.parse_args()

    # Logging
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'

    # Timeouts
    args.base_timeout = 5.0
    args.connect_timeout = 10.0
    args.streams_timeout = 30.0

    # Events
    args.stop_flag = threading.Event()

    # Background ports
    args.sensors_port = None
    args.actuators_port = None

    # Storage
    args.sensors_report = (0, None)
    args.sensors_report_lock = threading.Lock()
    args.actuators_report = (0, None)
    args.actuators_report_lock = threading.Lock()

    return _run(args)

if __name__ == '__main__':
    main()
