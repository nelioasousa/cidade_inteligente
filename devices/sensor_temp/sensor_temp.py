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


NAME = 'Sensor-Temp-01'
DEVICE_IP = socket.gethostbyname(socket.gethostname())
DEVICE_PORT = 5000
MULTICAST_ADDRS = ('224.0.1.0', 12345)
BASE_TEMP = 20.0 + 20 * random.random()
GATEWAY_ADDRS = None
GATEWAY_TIMEOUT = 5.0
MAX_ATTEMPTS = 5


STATE = {
    'ReportInterval': None,
    'Actions': ('reset', 'celsius', 'fahrenheit', 'kelvin'),
}

METADATA = {
    'UnitName': 'Celsius',
    'UnitSymbol': '°C',
    'Location': {'Latitude': -3.733486, 'Longitude': -38.570860},
}


def gateway_discoverer(stop_flag):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        multicast_ip, multicast_port = MULTICAST_ADDRS
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', multicast_port))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(multicast_ip) + socket.inet_aton('0.0.0.0')
        )
        sock.settimeout(GATEWAY_TIMEOUT)
        num_attempts = MAX_ATTEMPTS
        while not stop_flag.is_set():
            try:
                msg = sock.recv(1024)
            except TimeoutError:
                print('Timeout no multicast')
                num_attempts -= 1
                # Gateway offline or failed
                if num_attempts < 1:
                    print('Gateway falhou, terminando tudo...')
                    stop_flag.set()
                    break
                continue
            gateway_addrs = Address()
            gateway_addrs.ParseFromString(msg)
            gateway_addrs = (gateway_addrs.ip, gateway_addrs.port)
            if GATEWAY_ADDRS is None or GATEWAY_ADDRS[0] != gateway_addrs[0]:
                if try_to_connect(gateway_addrs):
                    print('Conexão bem-sucedida com', gateway_addrs)
                    num_attempts = MAX_ATTEMPTS
                else:
                    num_attempts -= 1
            else:
                num_attempts = MAX_ATTEMPTS


def try_to_connect(addrs):
    print('Tentando conectar com', addrs)
    global GATEWAY_ADDRS
    GATEWAY_ADDRS = None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        try:
            sock.connect(addrs)
        except Exception:
            return False
        device_info = DeviceInfo(
            name=NAME,
            state=json.dumps(STATE),
            metadata=json.dumps(METADATA)
        )
        device_address = Address(ip=DEVICE_IP, port=DEVICE_PORT)
        join_request = JoinRequest(
            device_info=device_info,
            device_address=device_address
        ).SerializeToString()
        try:
            sock.send(join_request)
        except Exception:
            return False
        try:
            msg = sock.recv(1024)
        except Exception:
            return False
        join_reply = JoinReply()
        join_reply.ParseFromString(msg)
    report_addrs = join_reply.report_address
    report_interval = join_reply.report_interval
    GATEWAY_ADDRS = (report_addrs.ip, report_addrs.port)
    STATE['ReportInterval'] = report_interval
    return True


def get_reading():
    global BASE_TEMP
    temp = min(max(BASE_TEMP + random.random() - 0.5, 20), 40)
    BASE_TEMP = temp
    if METADATA['UnitName'] == 'Kelvin':
        return temp + 273.15
    if METADATA['UnitName'] == 'Fahrenheit':
        return 32.0 + (temp * 9 / 5)
    return temp


def transmit_readings(stop_flag):
    print('Começando a transmissão de leituras')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while not stop_flag.is_set():
            if GATEWAY_ADDRS is None:
                time.sleep(5.0)
            else:
                reading = SensorReading(
                    sensor_name=NAME,
                    reading_value=f'{get_reading():.2f}',
                    timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                )
                sock.sendto(reading.SerializeToString(), GATEWAY_ADDRS)
                print('Leitura de temperatura enviada')
                time.sleep(STATE['ReportInterval'])


def exec_action(action):
    status = ReplyStatus.OK
    match action.strip().lower():
        case 'reset':
            global GATEWAY_ADDRS
            GATEWAY_ADDRS = None
            STATE['ReportInterval'] = None
            METADATA['UnitName'] = 'Celsius'
            METADATA['UnitSymbol'] = '°C'
        case 'celsius':
            METADATA['UnitName'] = 'Celsius'
            METADATA['UnitSymbol'] = '°C'
        case 'fahrenheit':
            METADATA['UnitName'] = 'Fahrenheit'
            METADATA['UnitSymbol'] = 'F'
        case 'kelvin':
            METADATA['UnitName'] = 'Kelvin'
            METADATA['UnitSymbol'] = 'K'
        case _:
            status = ReplyStatus.UNKNOWN_ACTION
    return status, ''


def set_state(state_string):
    try:
        new_state = json.loads(state_string)
    except json.JSONDecodeError:
        return (
            ReplyStatus.BAD_REQUEST,
            'Não foi possível decodificar o corpo da requisição'
        )
    except UnicodeDecodeError:
        return (
            ReplyStatus.BAD_REQUEST,
            'Corpo da requisição precisar estar codificado em UTF-8, 16 ou 32'
        )
    if not isinstance(new_state, dict):
        return (
            ReplyStatus.BAD_REQUEST,
            'Corpo da requisição precisar ser um objeto JSON.'
        )
    if 'Actions' in new_state:
        return ReplyStatus.DENIED, '"Actions" é readonly'
    if not isinstance(new_state.get('ReportInterval'), (NoneType, Real)):
        return (
            ReplyStatus.BAD_REQUEST,
            '"ReportInterval" precisa ser `None` ou numérico (`int`, `float`)'
        )
    if (set(new_state) - set(STATE)):
        return ReplyStatus.BAD_REQUEST, 'Existem chaves inválidas'
    reply_body = json.dumps(STATE)
    STATE.update(new_state)
    return ReplyStatus.OK, reply_body


def set_metadata(metadata_string):
    try:
        new_metadata = json.loads(metadata_string)
    except json.JSONDecodeError:
        return (
            ReplyStatus.BAD_REQUEST,
            'Não foi possível decodificar o corpo da requisição'
        )
    except UnicodeDecodeError:
        return (
            ReplyStatus.BAD_REQUEST,
            'Corpo da requisição precisar estar codificado em UTF-8, 16 ou 32'
        )
    if not isinstance(new_metadata, dict):
        return (
            ReplyStatus.BAD_REQUEST,
            'Corpo da requisição precisar ser um objeto JSON.'
        )
    if 'UnitName' in new_metadata or 'UnitSymbol' in new_metadata:
        return (
            ReplyStatus.DENIED,
            '"UnitName" e "UnitSymbol" são readonly. '
            'Use `RequestType.ACTION` para mudar as unidades de medição.'
        )
    if 'Location' in new_metadata:
        try:
            lat = new_metadata['Location']['Latitude']
            long = new_metadata['Location']['Longitude']
        except KeyError:
            return (
                ReplyStatus.BAD_REQUEST,
                'Valor de "Location" precisa ser da forma '
                '{"Latitude": <`float`>, "Longitude": <`float`>}'
            )
        if not (isinstance(lat, Real) and isinstance(long, Real)):
            return (
                ReplyStatus.BAD_REQUEST,
                '"Latitude" e "Longitude" precisam ser `float`'
            )
    reply_body = json.dumps(METADATA)
    METADATA.update(new_metadata)
    return ReplyStatus.OK, reply_body


def request_handler(sock):
    print('Tratando requisição do Gateway')
    try:
        sock.settimeout(3.0)
        req = DeviceRequest()
        req.ParseFromString(sock.recv(1024))
    except TimeoutError:
        status = ReplyStatus.TIMEOUT
        reply_body = 'Requisição do cliente não chegou em tempo hábil'
    except message.DecodeError:
        status = ReplyStatus.BAD_REQUEST
        reply_body = 'Não foi possível compreender a requisição'
    except Exception:
        status = ReplyStatus.FAIL
        reply_body = 'Erro ao processar a requisição'
    else:
        match req.type:
            case RequestType.ACTION:
                status, reply_body = exec_action(req.body)
            case RequestType.GET_STATE:
                reply_body = json.dumps(STATE)
                status = ReplyStatus.OK
            case RequestType.SET_STATE:
                status, reply_body = set_state(req.body)
            case RequestType.GET_METADATA:
                reply_body = json.dumps(METADATA)
                status = ReplyStatus.OK
            case RequestType.SET_METADATA:
                status, reply_body = set_metadata(req.body)
            case _:
                status, reply_body = ReplyStatus.UNKNOWN_TYPE, ''
    finally:
        try:
            reply = DeviceReply(status=status, body=reply_body)
            sock.send(reply.SerializeToString())
        finally:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()


def request_listener(stop_flag):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', DEVICE_PORT))
        sock.listen()
        print('Ouvindo requisições do gateway')
        sock.settimeout(2.0)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not stop_flag.is_set():
                try:
                    conn, _ = sock.accept()
                except TimeoutError:
                    continue
                executor.submit(request_handler, conn)


if __name__ == '__main__':
    stop_flag = threading.Event()
    try:
        threading.Thread(target=request_listener, args=(stop_flag,)).start()
        threading.Thread(target=transmit_readings, args=(stop_flag,)).start()
        discoverer = threading.Thread(target=gateway_discoverer, args=(stop_flag,))
        discoverer.start()
        discoverer.join()
    except:
        stop_flag.set()
        raise
