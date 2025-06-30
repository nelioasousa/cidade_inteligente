import sys
import json
import time
import socket
import threading
import logging
from struct import unpack
from messages_pb2 import SensorsReport, ActuatorsReport
from messages_pb2 import RequestType, ClientRequest
from messages_pb2 import ReplyStatus, ClientReply
from messages_pb2 import ActuatorUpdate, SensorData


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
            print(f' {key.ljust(max_key_length)} : {value}')
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


def recv_exaclty(sock, n, timeout_tolerance=3):
    msg_chunks = []
    remaining = n
    while remaining:
        try:
            chunk = sock.recv(remaining)
        except TimeoutError as e:
            if timeout_tolerance < 1:
                raise e
            timeout_tolerance -= 1
            continue
        if not chunk:
            raise EOFError('Socket closed before receiving all expected data')
        msg_chunks.append(chunk)
        remaining -= len(chunk)
    return b''.join(msg_chunks)


def recv_reply(sock):
    msg_size = recv_exaclty(sock, 4)
    msg_size = unpack('!I', msg_size)[0]
    return recv_exaclty(sock, msg_size)


def list_sensors(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(args.gateway)
        except Exception:
            print('[!] Could\'nt connect to Gateway')
            return
        try:
            request = ClientRequest(type=RequestType.RT_GET_SENSORS_REPORT)
            request = request.SerializeToString()
            sock.send(request)
        except Exception:
            print('[!] Error when sending request to Gateway')
            return
        try:
            msg = recv_reply(sock)
            reply = ClientReply()
            reply.ParseFromString(msg)
        except Exception:
            print('[!] Error when waiting for Gateway response')
            return
    if reply.status is not ReplyStatus.RS_OK:
        print('[!] Gateway failure')
        return
    try:
        report = SensorsReport()
        report.ParseFromString(reply.data)
    except Exception:
        print('[!] Couldn\'t undestand Gateway response')
        return
    if not report.devices:
        print('No sensors to report')
        return
    for sensor in report.devices:
        print_sensor_summary(sensor)


def list_actuators(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(args.gateway)
        except Exception:
            print('[!] Could\'nt connect to Gateway')
            return
        try:
            request = ClientRequest(type=RequestType.RT_GET_ACTUATORS_REPORT)
            request = request.SerializeToString()
            sock.send(request)
        except Exception:
            print('[!] Error when sending request to Gateway')
            return
        try:
            msg = recv_reply(sock)
            reply = ClientReply()
            reply.ParseFromString(msg)
        except Exception:
            print('[!] Error when waiting for Gateway response')
            return
    if reply.status is not ReplyStatus.RS_OK:
        print('[!] Gateway failure')
        return
    try:
        report = ActuatorsReport()
        report.ParseFromString(reply.data)
    except Exception:
        print('[!] Couldn\'t undestand Gateway response')
        return
    if not report.devices:
        print('No actuators to report')
        return
    for actuator in report.devices:
        print_actuator_summary(actuator)


def send_action_to_actuator(args, device_name, action_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(args.gateway)
        except Exception:
            print('[!] Could\'nt connect to Gateway')
            return
        try:
            request = ClientRequest(
                type=RequestType.RT_RUN_ACTUATOR_ACTION,
                device_name=device_name,
                body=action_name,
            )
            request = request.SerializeToString()
            sock.send(request)
        except Exception:
            print('[!] Error when sending request to Gateway')
            return
        try:
            msg = recv_reply(sock)
            reply = ClientReply()
            reply.ParseFromString(msg)
        except Exception:
            print('[!] Error when waiting for Gateway response')
            return
    if reply.status is ReplyStatus.RS_UNKNOWN_DEVICE:
        print(f'[!] Unknown actuator with name "{device_name}"')
        return
    if reply.status is ReplyStatus.RS_UNKNOWN_ACTION:
        print(f'[!] Actuator "{device_name}" don\'t have action "{action_name}"')
        return
    if reply.status is not ReplyStatus.RS_OK:
        print('[!] Something went wrong...')
        return
    try:
        update = ActuatorUpdate()
        update.ParseFromString(reply.data)
        print_actuator_summary(update)
    except Exception:
        print('[!] Couldn\'t undestand Gateway response')
        return


def send_set_state_to_actuator(args, device_name, state_key, state_value):
    state_string = '{"%s": %s}' %(state_key, state_value)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(args.gateway)
        except Exception:
            print('[!] Could\'nt connect to Gateway')
            return
        try:
            request = ClientRequest(
                type=RequestType.RT_SET_ACTUATOR_STATE,
                device_name=device_name,
                body=state_string,
            )
            request = request.SerializeToString()
            sock.send(request)
        except Exception:
            print('[!] Error when sending request to Gateway')
            return
        try:
            msg = recv_reply(sock)
            reply = ClientReply()
            reply.ParseFromString(msg)
        except Exception:
            import traceback
            traceback.print_exc()
            print('[!] Error when waiting for Gateway response')
            return
    if reply.status is ReplyStatus.RS_UNKNOWN_DEVICE:
        print(f'[!] Unknown actuator with name "{device_name}"')
        return
    if reply.status is ReplyStatus.RS_INVALID_STATE:
        print(f'[!] Invalid state for actuator "{device_name}": {state_string}')
        return
    if reply.status is not ReplyStatus.RS_OK:
        print('[!] Something went wrong...')
        return
    try:
        update = ActuatorUpdate()
        update.ParseFromString(reply.data)
        print_actuator_summary(update)
    except Exception:
        print('[!] Couldn\'t undestand Gateway response')
        return


def print_help(bad_command=False):
    if bad_command:
        print('[!] Command not understood', end='\n\n')
    print('The following commands are available:')
    print('  help      : show this help message')
    print('  sensors   : list sensors devices')
    print('  actuators : list actuators devices')
    print('  actuator <name> <command>')
    print('            : send command <command> to actuator <name>')
    print('  actuator <name> <key> <value>')
    print('            : set state <key> to <value> for actuator <name>', end='\n\n')


def app(args):
    while True:
        command = input('>>> ').strip()
        command, *params = command.split()
        command = command.lower()
        match command:
            case 'help':
                print_help()
            case 'sensors':
                if params:
                    print_help(True)
                else:
                    list_sensors(args)
            case 'actuators':
                if params:
                    print_help(True)
                else:
                    list_actuators(args)
            case 'actuator':
                if len(params) == 2:
                    send_action_to_actuator(args, *params)
                elif len(params) == 3:
                    send_set_state_to_actuator(args, *params)
                else:
                    print_help(True)
            case _:
                print_help(True)


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        app(args)
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

    # Gateway address
    args.gateway = (args.gateway_ip, args.gateway_port)

    # Logging
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'

    # Timeouts
    args.base_timeout = 2.0

    return _run(args)

if __name__ == '__main__':
    main()
