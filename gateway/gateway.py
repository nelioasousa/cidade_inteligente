import socket
import threading
import time
import json
import datetime
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import message
from messages_pb2 import Address, SensorReading
from messages_pb2 import JoinRequest, JoinReply


GATEWAY_IP = socket.gethostbyname(socket.gethostname())
GATEWAY_CLIENT_PORT = 5000
GATEWAY_JOIN_PORT = 50111
GATEWAY_SENSORS_PORT = 50222
GATEWAY_ACTUATORS_PORT = 50333
MULTICAST_ADDRS = ('224.0.1.0', 12345)
SENSORS_REPORT_INTERVAL = 1
ACTUATORS_REPORT_INTERVAL = 5
CONNECTED_DEVICES = {}


def multicast_location(stop_flag, interval_sec=5.0):
    addrs = Address(ip=GATEWAY_IP, port=GATEWAY_JOIN_PORT).SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        while not stop_flag.is_set():
            sock.sendto(addrs, MULTICAST_ADDRS)
            time.sleep(interval_sec)


def join_handler(sock):
    try:
        sock.settimeout(5.0)
        req = JoinRequest()
        req.ParseFromString(sock.recv(1024))
    except Exception:
        return
    else:
        device_info = {
            'name': req.device_info.name,
            'address': (req.device_address.ip, req.device_address.port),
            'state': json.loads(req.device_info.state),
            'metadata': json.loads(req.device_info.metadata),
            'data': []
        }
        name = device_info['name']
        CONNECTED_DEVICES[name] = device_info
        if name.startswith('Sensor'):
            report_interval = SENSORS_REPORT_INTERVAL
            report_port = GATEWAY_SENSORS_PORT
        else:
            report_interval = ACTUATORS_REPORT_INTERVAL
            report_port = GATEWAY_ACTUATORS_PORT
        report_address = Address(ip=GATEWAY_IP, port=report_port)
        reply = JoinReply(
            report_address=report_address, report_interval=report_interval
        )
        sock.send(reply.SerializeToString())
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def join_listener(stop_flag):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', GATEWAY_JOIN_PORT))
        sock.listen()
        sock.settimeout(2.0)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not stop_flag.is_set():
                try:
                    conn, _ = sock.accept()
                except TimeoutError:
                    continue
                executor.submit(join_handler, conn)


def sensors_listener(stop_flag):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', GATEWAY_SENSORS_PORT))
        while not stop_flag.is_set():
            msg, _ = sock.recvfrom(1024)
            try:
                reading = SensorReading()
                reading.ParseFromString(msg)
            except message.DecodeError:
                continue
            name = reading.sensor_name
            try:
                device = CONNECTED_DEVICES[name]
            except KeyError:
                continue
            if name.startswith('Sensor-Temp'):
                reading_value = float(reading.reading_value)
                timestamp = datetime.datetime.fromisoformat(reading.timestamp)
                device['data'].append((timestamp, reading_value))
                device['data'].sort(key=(lambda x: x[0]))


# def make_requests(device_name):
#     device = DEVICES[device_name]

#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#         sock.connect(device['address'])
#         sock.settimeout(5.0)
#         req = DeviceRequest(
#             type=RequestType.ACTION,
#             body='kelvin'
#         )
#         sock.send(req.SerializeToString())
#         reply = DeviceReply()
#         reply.ParseFromString(sock.recv(1024))
#         print(reply)
#         sock.shutdown(socket.SHUT_RDWR)

#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#         sock.connect(device['address'])
#         sock.settimeout(5.0)
#         req = DeviceRequest(type=RequestType.GET_STATE)
#         sock.send(req.SerializeToString())
#         reply = DeviceReply()
#         reply.ParseFromString(sock.recv(1024))
#         print(reply)
#         sock.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    stop_flag = threading.Event()
    try:
        threading.Thread(target=multicast_location, args=(stop_flag,)).start()
        threading.Thread(target=join_listener, args=(stop_flag,)).start()
        threading.Thread(target=sensors_listener, args=(stop_flag,)).start()
        while True:
            time.sleep(10.0)
    finally:
        stop_flag.set()
