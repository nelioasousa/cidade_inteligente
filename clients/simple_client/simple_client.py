import sys
import json
import time
import socket
import threading
import logging
from functools import wraps
from copy import deepcopy
from messages_pb2 import SensorsReport, ActuatorsReport, SendNextReport
from messages_pb2 import ConnectionRequest
from messages_pb2 import SensorReading, ActuatorUpdate


def att_sensors_report(args, report):
    with args.sensors_report_lock:
        args.sensors_report = (args.sensors_report[0] + 1, report)


def att_actuators_report(args, report):
    with args.actuators_report_lock:
        args.actuators_report = (args.actuators_report[0] + 1, report)


def sensors_report_listener(args):
    logger = logging.getLogger('SENSORS_REPORT')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', args.sensors_port))
        sock.listen()
        logger.info(
            'Esperando relatório dos sensores na porta %d',
            args.sensors_port,
        )
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            args.receiving_sensors_data.clear()
            try:
                conn, _ = sock.accept()
                conn.settimeout(args.report_timeout)
                logger.info('Conexão com o Gateway aceita')
            except TimeoutError:
                logger.info('Gateway não solicitou conexão em tempo hábil')
                time.sleep(2.0)
                continue
            except Exception as e:
                logger.error(
                    'Erro ao aceitar conexão com o Gateway: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            with conn:
                args.receiving_sensors_data.set()
                send_next_report = SendNextReport().SerializeToString()
                while not args.stop_flag.is_set():
                    try:
                        msg = conn.recv(1024)
                    except Exception as e:
                        logger.error(
                            'Erro ao receber relatório: (%s) %s',
                            type(e).__name__,
                            e,
                        )
                        break
                    report = SensorsReport()
                    report.ParseFromString(msg)
                    att_sensors_report(args, report)
                    try:
                        conn.send(send_next_report)
                    except Exception as e:
                        logger.error(
                            'Erro ao solicitar novo relatório: (%s) %s',
                            type(e).__name__,
                            e,
                        )
                        break


def actuators_report_listener(args):
    logger = logging.getLogger('ACTUATORS_REPORT')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', args.actuators_port))
        sock.listen()
        logger.info(
            'Esperando relatórios dos atuadores na porta %d',
            args.actuators_port,
        )
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            args.receiving_actuators_data.clear()
            try:
                conn, _ = sock.accept()
                conn.settimeout(args.report_timeout)
                logger.info('Conexão com o Gateway aceita')
            except TimeoutError:
                logger.info('Gateway não solicitou conexão em tempo hábil')
                time.sleep(2.0)
                continue
            except Exception as e:
                logger.error(
                    'Erro ao aceitar conexão com o Gateway: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            with conn:
                args.receiving_actuators_data.set()
                send_next_report = SendNextReport().SerializeToString()
                while not args.stop_flag.is_set():
                    try:
                        msg = conn.recv(1024)
                    except Exception as e:
                        logger.error(
                            'Erro ao receber relatório: (%s) %s',
                            type(e).__name__,
                            e,
                        )
                        break
                    report = ActuatorsReport()
                    report.ParseFromString(msg)
                    att_actuators_report(args, report)
                    try:
                        conn.send(send_next_report)
                    except Exception as e:
                        logger.error(
                            'Erro ao solicitar novo relatório: (%s) %s',
                            type(e).__name__,
                            e,
                        )
                        break


def disconnect_gateway(args):
    with args.connection_lock:
        args.connection = None
        args.gateway_connected.clear()


def gateway_connector(args):
    logger = logging.getLogger('GATEWAY_CONNECTOR')
    connection_message = ConnectionRequest(
        sensors_port=args.sensors_port, actuators_port=args.actuators_port,
    ).SerializeToString()
    args.gateway_connected.clear()
    while not args.stop_flag.is_set():
        disconnect_gateway(args)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(args.base_timeout)
            try:
                sock.connect((args.gateway_ip, args.gateway_port))
            except Exception as e:
                logger.info('Não foi possível se conectar ao Gateway')
                time.sleep(2.0)
                continue
            try:
                sock.send(connection_message)
                logger.info('Conexão com o Gateway foi bem-sucedida')
                with args.connection_lock:
                    args.gateway_connected.set()
                    args.connection = sock
            except Exception as e:
                logger.error(
                    'Erro durante o envio da requisição de conexão: (%s) %s',
                    type(e).__name__,
                    e,
                )
                continue
            while (
                not args.stop_flag.is_set()
                and args.gateway_connected.is_set()
            ):
                time.sleep(1.0)
                continue


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
        for key, value in metadata.items():
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
        for key, value in state.items():
            print(f' {key.ljust(max_key_length)} : {value}')
    if metadata:
        max_key_length = max(len(k) for k in metadata)
        print('[METADATA]')
        for key, value in metadata.items():
            print(f' {key.ljust(max_key_length)} : {value}')
    print()


def print_sensors(args):
    with args.sensors_report_lock:
        sensors = deepcopy(args.sensors_report[1])
    if sensors is None:
        print('Nenhum relatório foi fornecido.')
        return
    if not sensors.devices:
        print('Nenhum sensor para listar.')
        return
    for sensor in sensors.devices:
        print_sensor_summary(sensor)


def print_actuators(args):
    with args.actuators_report_lock:
        actuators = deepcopy(args.actuators_report[1])
    if actuators is None:
        print('Nenhum relatório foi fornecido.')
        return
    if not actuators.devices:
        print('Nenhum atuador para listar.')
        return
    for actuator in actuators.devices:
        print_actuator_summary(actuator)


def app(args):
    while not args.stop_flag.is_set():
        command = input('>>> ').strip().lower()
        match command:
            case 'help':
                print_help()
            case 'sensors':
                print_sensors(args)
            case 'actuators':
                print_actuators(args)


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
        sensors_listener = threading.Thread(
            target=stop_wrapper(sensors_report_listener, args.stop_flag),
            args=(args,)
        )
        actuators_listener = threading.Thread(
            target=stop_wrapper(actuators_report_listener, args.stop_flag),
            args=(args,)
        )
        connector = threading.Thread(
            target=stop_wrapper(gateway_connector, args.stop_flag),
            args=(args,)
        )
        sensors_listener.start()
        actuators_listener.start()
        connector.start()
        app(args)
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN...')
    finally:
        args.stop_flag.set()
        sensors_listener.join()
        actuators_listener.join()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente simples em Python')

    parser.add_argument(
        '--sensors_port', type=int, default=60444,
        help='Porta na qual receber os relatórios dos sensores.'
    )

    parser.add_argument(
        '--actuators_port', type=int, default=60333,
        help='Porta na qual receber os relatórios dos atuadores.'
    )

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

    # Gateway connection
    args.connection = None
    args.connection_lock = threading.Lock()

    # Timeouts
    args.base_timeout = 2.0
    args.generous_timeout = 120.0
    args.report_timeout = 60.0

    # Events
    args.stop_flag = threading.Event()
    args.gateway_connected = threading.Event()
    args.receiving_sensors_data = threading.Event()
    args.receiving_actuators_data = threading.Event()

    # Storage
    args.sensors_report = (0, None)
    args.sensors_report_lock = threading.Lock()
    args.actuators_report = (0, None)
    args.actuators_report_lock = threading.Lock()

    return _run(args)

if __name__ == '__main__':
    main()
