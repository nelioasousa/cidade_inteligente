import json
import socket
import time
import datetime
import random
import threading
from types import NoneType
from numbers import Real
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceInfo, JoinRequest, JoinReply
from messages_pb2 import DeviceRequest, DeviceReply, RequestType, ReplyStatus
from google.protobuf import message


def gateway_discoverer(args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(args.multicast_ip) + socket.inet_aton('0.0.0.0')
        )
        sock.settimeout(args.multicast_timeout)
        fail_counter = 0
        while not args.stop_flag.is_set():
            try:
                msg = sock.recv(1024)
            except TimeoutError:
                if args.gateway_ip is not None:
                    print(f'Falha do Gateway em {args.gateway_ip}')
                    fail_counter += 1
                    if fail_counter >= args.disconnect_after:
                        print('Gateway offline. Desconectando sensor...')
                        disconnect_device(args)
                continue
            gateway_addrs = Address()
            gateway_addrs.ParseFromString(msg)
            if args.gateway_ip is not None:
                if gateway_addrs.ip == args.gateway_ip:
                    continue
                else:
                    print('Gateway realocado. Desconectando...')
                    disconnect_device(args)
            if try_to_connect(args, (gateway_addrs.ip, gateway_addrs.port)):
                fail_counter = 0
                print(f'Conexão bem-sucedida com {gateway_addrs.ip}')
            else:
                print(f'Falha ao se conectar com {gateway_addrs.ip}')


def disconnect_device(args):
    args.gateway_ip = None
    args.transmission_port = None
    return


def try_to_connect(args, addrs):
    print('Tentando conectar com', addrs)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(addrs)
            device_info = DeviceInfo(
                name=args.name,
                state=json.dumps(args.state),
            )
            device_address = Address(ip=args.host_ip, port=args.port)
            join_request = JoinRequest(
                device_info=device_info,
                device_address=device_address,
            )
            sock.send(join_request.SerializeToString())
            join_reply = JoinReply()
            join_reply.ParseFromString(sock.recv(1024))
        except Exception:
            return False
    report_addrs = join_reply.report_address
    if report_addrs.ip != addrs[0]:
        print('Não é permitido redirecionamento para outro servidor')
        return False
    args.gateway_ip = report_addrs.ip
    args.transmission_port = report_addrs.port
    args.state['ReportInterval'] = join_reply.report_interval
    return True


def get_reading(args):
    temp = args.temperature + random.random() - 0.5
    temp = min(max(temp, args.min_temperature), args.max_temperature)
    args.temperature = temp
    if args.state['UnitName'] == 'Kelvin':
        return temp + 273.15
    if args.state['UnitName'] == 'Fahrenheit':
        return 32.0 + (temp * 9 / 5)
    return temp


def transmit_readings(args):
    print('Começando a transmissão de leituras')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while not args.stop_flag.is_set():
            if args.gateway_ip is None:
                print('Transmissão parada. Sem conexão com o Gateway')
                time.sleep(5.0)
            else:
                reading = SensorReading(
                    sensor_name=args.name,
                    reading_value=f'{get_reading(args):.2f}',
                    timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                )
                sock.sendto(
                    reading.SerializeToString(),
                    (args.gateway_ip, args.transmission_port),
                )
                print('Leitura de temperatura enviada')
                time.sleep(args.state['ReportInterval'])


def exec_action(args, action):
    status = ReplyStatus.OK
    match action.strip().lower():
        case 'reset':
            args.gateway_ip = None
            args.transmission_port = None
            args.state['ReportInterval'] = None
            args.state['UnitName'] = 'Celsius'
            args.state['UnitSymbol'] = '°C'
        case 'celsius':
            args.state['UnitName'] = 'Celsius'
            args.state['UnitSymbol'] = '°C'
        case 'fahrenheit':
            args.state['UnitName'] = 'Fahrenheit'
            args.state['UnitSymbol'] = 'F'
        case 'kelvin':
            args.state['UnitName'] = 'Kelvin'
            args.state['UnitSymbol'] = 'K'
        case _:
            status = ReplyStatus.UNKNOWN_ACTION
    return status, ''


def set_state(args, new_state_string):
    try:
        new_state = json.loads(new_state_string)
    except json.JSONDecodeError:
        status = ReplyStatus.BAD_REQUEST
        body = 'Não foi possível decodificar o corpo da requisição'
        return status, body
    except UnicodeDecodeError:
        status = ReplyStatus.BAD_REQUEST
        body = 'Corpo da requisição precisar estar em UTF-8, 16 ou 32'
        return status, body
    if not isinstance(new_state, dict):
        status = ReplyStatus.BAD_REQUEST
        body = 'Corpo da requisição precisar ser um objeto JSON.'
        return status, body
    if 'Actions' in new_state:
        status = ReplyStatus.DENIED
        body = '"Actions" é readonly'
    if 'ReportInterval' in new_state:
        report_interval = new_state['ReportInterval']
        if not isinstance(report_interval, Real) or report_interval <= 0.0:
            status = ReplyStatus.BAD_REQUEST
            body = '"ReportInterval" precisa um número real positivo'
            return status, body
    if 'UnitName' in new_state or 'UnitSymbol' in new_state:
        status = ReplyStatus.DENIED
        body = '"UnitName" e "UnitSymbol" são readonly.'
        return status, body
    if 'Location' in new_state:
        try:
            lat = new_state['Location']['Latitude']
            long = new_state['Location']['Longitude']
        except (TypeError, KeyError):
            status = ReplyStatus.BAD_REQUEST
            body = (
                'Valor da chave "Location" precisa ser da forma '
                '{"Latitude": <`float`>, "Longitude": <`float`>}'
            )
            return status, body
        if not (isinstance(lat, Real) and isinstance(long, Real)):
            status = ReplyStatus.BAD_REQUEST
            body = (
                'Valores das chaves "Latitude" e "Longitude" '
                'precisam ser númericos (`float`)'
            )
            return status, body
    if (set(new_state) - set(args.state)):
        status = ReplyStatus.BAD_REQUEST
        body = 'Existem chaves inválidas'
        return status, body
    body = json.dumps(args.state)
    args.state.update(new_state)
    return ReplyStatus.OK, body


def request_handler(args, sock):
    print('Tratando requisição do Gateway')
    try:
        sock.settimeout(args.base_timeout)
        req = DeviceRequest()
        req.ParseFromString(sock.recv(1024))
        match req.type:
            case RequestType.ACTION:
                status, body = exec_action(args, req.body)
            case RequestType.GET_STATE:
                status = ReplyStatus.OK
                body = json.dumps(args.state)
            case RequestType.SET_STATE:
                status, body = set_state(args, req.body)
            case _:
                status, body = ReplyStatus.UNKNOWN_TYPE, ''
    except TimeoutError:
        status = ReplyStatus.TIMEOUT
        body = 'Requisição do cliente não chegou em tempo hábil'
    except message.DecodeError:
        status = ReplyStatus.BAD_REQUEST
        body = 'Não foi possível compreender a requisição'
    except Exception:
        status = ReplyStatus.FAIL
        body = 'Erro ao processar a requisição'
    finally:
        try:
            reply = DeviceReply(status=status, body=body)
            sock.send(reply.SerializeToString())
        finally:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()


def request_listener(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.port))
        sock.listen()
        print('Ouvindo requisições do gateway')
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, _ = sock.accept()
                except TimeoutError:
                    continue
                executor.submit(request_handler, args, conn)


def _run(args):
    try:
        rlistener = threading.Thread(target=request_listener, args=(args,))
        transmiter = threading.Thread(target=transmit_readings, args=(args,))
        rlistener.start()
        transmiter.start()
        gateway_discoverer(args)
    except BaseException as e:
        args.stop_flag.set()
        if isinstance(e, KeyboardInterrupt):
            print('\rDESLIGANDO...')
        else:
            raise e
    finally:
        rlistener.join()
        transmiter.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sensor de temperatura')

    parser.add_argument(
        '--name', type=str, default='01',
        help='Nome que unicamente identifica o sensor de temperatura.'
    )

    parser.add_argument(
        '--port', type=int, default=5000,
        help='Porta em que o Gateway deve se comunicar com o sensor.'
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

    args = parser.parse_args()
    args.name = f'Sensor-Temp-{args.name}'
    args.base_timeout = 2.5
    args.multicast_timeout = 5.0
    args.host_ip = socket.gethostbyname(socket.gethostname())
    args.gateway_ip = None
    args.transmission_port = None
    args.state = {
        'ReportInterval': None,
        'Actions': ('reset', 'celsius', 'fahrenheit', 'kelvin'),
        'UnitName': 'Celsius',
        'UnitSymbol': '°C',
        'Location': {'Latitude': -3.733486, 'Longitude': -38.570860},
    }
    args.stop_flag = threading.Event()

    return _run(args)


if __name__ == '__main__':
    main()
