import json
import socket
import time
import datetime
import random
import threading
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceInfo, JoinRequest, JoinReply
from messages_pb2 import DeviceRequest, DeviceReply, RequestType, Status


NAME = 'Sensor-Temp-01'
DEVICE_IP = socket.gethostbyname(socket.gethostname())
DEVICE_PORT = 5000
MULTICAST_ADDR = ('224.0.1.0', 12345)
BASE_TEMP = 20.0 + 20 * random.random()
GATEWAY_ADDR = None


STATE = {
    'ReportInterval': None,
    'Actions': ('reset', 'celsius', 'fahrenheit', 'kelvin')
}

METADATA = {
    'UnitName': 'Celsius',
    'UnitSymbol': '°C',
    'Location': {'Latitude': -3.733486, 'Longitude': -38.570860}
}


def discover_gateway():
    global GATEWAY_ADDR
    GATEWAY_ADDR = None
    STATE['ReportInterval'] = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MULTICAST_ADDR[1]))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(MULTICAST_ADDR[0]) + socket.inet_aton('0.0.0.0')
        )
        gateway_addrs = Address()
        gateway_addrs.ParseFromString(sock.recv(1024))
        GATEWAY_ADDR = (gateway_addrs.ip, gateway_addrs.port)
    device_info = DeviceInfo(
        name=NAME, state=json.dumps(STATE), metadata=json.dumps(METADATA)
    )
    device_address = Address(ip=DEVICE_IP, port=DEVICE_PORT)
    join_request = JoinRequest(
        device_info=device_info, device_address=device_address
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(GATEWAY_ADDR)
        sock.send(join_request.SerializeToString())
        join_reply = JoinReply()
        join_reply.ParseFromString(sock.recv(1024))
        GATEWAY_ADDR = (
            join_reply.report_address.ip, join_reply.report_address.port
        )
        STATE['ReportInterval'] = join_reply.report_interval


def get_reading():
    global BASE_TEMP
    temp = min(max(BASE_TEMP + random.random() - 0.5, 20), 40)
    BASE_TEMP = temp
    if METADATA['UnitName'] == 'Kelvin':
        return temp + 273.15
    elif METADATA['UnitName'] == 'Fahrenheit':
        return 32.0 + (temp * 9 / 5)
    elif METADATA['UnitName'] == 'Celsius':
        return temp
    # Pode ser útil para simular falhas
    else:
        raise RuntimeError('Bad metadata')


def transmit_readings():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while GATEWAY_ADDR is not None and STATE['ReportInterval'] is not None:
            reading = SensorReading(
                sensor_name=NAME,
                reading_value='%.2f' %get_reading(),
                timestamp=datetime.datetime.now(tz=datetime.UTC).isoformat(),
            )
            sock.sendto(reading.SerializeToString(), GATEWAY_ADDR)
            time.sleep(STATE['ReportInterval'])


def exec_action(action):
    status = Status.STATUS_OK
    result = ''
    match action.strip().lower():
        case 'reset':
            global GATEWAY_ADDR
            GATEWAY_ADDR = None
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
            status = Status.STATUS_UNKNOWN
    return status, result


def request_handler(sock):
    try:
        req = DeviceRequest()
        req.ParseFromString(sock.recv(1024))
    except Exception:
        status, result = Status.STATUS_BAD, ''
    else:
        match req.type:
            case RequestType.REQUESTTYPE_ACTION:
                status, result = exec_action(req.key)
            case RequestType.REQUESTTYPE_GET_STATE:
                try:
                    result = STATE[req.key]
                    status = Status.STATUS_OK
                except KeyError:
                    status, result = Status.STATUS_UNKNOWN, ''
            case RequestType.REQUESTTYPE_SET_STATE:
                try:
                    result = STATE[req.key]
                    status = Status.STATUS_OK
                    STATE[req.key] = req.value
                except KeyError:
                    status, result = Status.STATUS_UNKNOWN, ''
            case RequestType.REQUESTTYPE_GET_METADATA:
                try:
                    result = METADATA[req.key]
                    status = Status.STATUS_OK
                except KeyError:
                    status, result = Status.STATUS_UNKNOWN, ''
            case RequestType.REQUESTTYPE_SET_METADATA:
                try:
                    result = METADATA[req.key]
                    status = Status.STATUS_OK
                    METADATA[req.key] = req.value
                except KeyError:
                    status, result = Status.STATUS_UNKNOWN, ''
            case _:
                status, result = Status.STATUS_UNKNOWN, ''
    finally:
        reply = DeviceReply(status=status, result=result)
        sock.send(reply.SerializeToString())
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def request_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', DEVICE_PORT))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            threading.Thread(target=request_handler, args=(conn,)).start()


def run():
    threading.Thread(target=request_listener, daemon=True).start()
    while True:
        discover_gateway()
        transmit_readings()


if __name__ == '__main__':
    run()
