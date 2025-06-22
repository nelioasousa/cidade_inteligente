import socket
import threading
import time
import json
import datetime
import traceback
from messages_pb2 import Address, SensorReading
from messages_pb2 import JoinRequest, JoinReply
from messages_pb2 import DeviceRequest, RequestType, DeviceReply


GATEWAY_IP = socket.gethostbyname(socket.gethostname())
GATEWAY_CLIENT_PORT = 5000
GATEWAY_JOIN_PORT = 50111
GATEWAY_SENSORS_PORT = 50222
GATEWAY_ACTUATORS_PORT = 50333
MULTICAST_ADDR = ('224.0.1.0', 12345)
SENSORS_REPORT_INTERVAL = 1
ACTUATORS_REPORT_INTERVAL = 5
DEVICES = {}


def multicast_gateway_location(interval_sec=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    address = Address(ip=GATEWAY_IP, port=GATEWAY_JOIN_PORT)
    while True:
        sock.sendto(address.SerializeToString(), MULTICAST_ADDR)
        time.sleep(interval_sec)


def join_handler(sock):
    with sock:
        try:
            req = JoinRequest()
            req.ParseFromString(sock.recv(1024))
        except Exception:
            pass
        else:
            device_info = {
                'name': req.device_info.name,
                'address': (req.device_address.ip, req.device_address.port),
                'state': json.loads(req.device_info.state),
                'metadata': json.loads(req.device_info.metadata),
                'data': []
            }
            name = device_info['name']
            if name not in DEVICES:
                DEVICES[name] = device_info
            if name.startswith('Sensor'):
                report_interval = SENSORS_REPORT_INTERVAL
                report_address = Address(
                    ip=GATEWAY_IP, port=GATEWAY_SENSORS_PORT
                )
            else:
                report_interval = ACTUATORS_REPORT_INTERVAL
                report_address = Address(
                    ip=GATEWAY_IP, port=GATEWAY_ACTUATORS_PORT
                )
            reply = JoinReply(
                report_address=report_address, report_interval=report_interval
            )
            sock.send(reply.SerializeToString())
        finally:
            sock.shutdown(socket.SHUT_RDWR)


def join_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', GATEWAY_JOIN_PORT))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            threading.Thread(target=join_handler, args=(conn,)).start()


def sensors_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', GATEWAY_SENSORS_PORT))
        while True:
            msg, _ = sock.recvfrom(1024)
            try:
                reading = SensorReading()
                reading.ParseFromString(msg)
            except Exception:
                continue
            name = reading.sensor_name
            print(reading)
            if name.startswith('Sensor-Temp'):
                reading_value = float(reading.reading_value)
                timestamp = datetime.datetime.fromisoformat(reading.timestamp)
                DEVICES[name]['data'].append((timestamp, reading_value))
                DEVICES[name]['data'].sort(key=(lambda x: x[0]))
            else:
                continue


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
    threading.Thread(target=multicast_gateway_location, daemon=True).start()
    threading.Thread(target=join_listener, daemon=True).start()
    threading.Thread(target=sensors_listener, daemon=True).start()
    while True:
        time.sleep(10)
