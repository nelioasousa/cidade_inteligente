import json
import socket
import time
import datetime
import random
from messages_pb2 import GatewayLocation, Address, DeviceInfo, JoinRequest, JoinReply, SensorReading


NAME = "Sensor-Temp-01"
DEVICE_ADDR = (socket.gethostbyname(socket.gethostname()), 5000)
MULTICAST_ADDR = ('224.0.1.0', 12345)
BASE_TEMP = 20.0 + 20 * random.random()
GATEWAY_ADDR = None
REPORT_INTERVAL = None


STATE  = {}
METADATA = {
    'UnitName': 'celsius',
    'UnitSymbol': '°C',
    'Location': {'Latitude': -3.733486, 'Longitude': -38.570860}
}


def discover_gateway():
    global GATEWAY_ADDR
    global REPORT_INTERVAL
    GATEWAY_ADDR = None
    REPORT_INTERVAL = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MULTICAST_ADDR[1]))
        mreq = socket.inet_aton(MULTICAST_ADDR[0]) + socket.inet_aton('0.0.0.0')
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while GATEWAY_ADDR is None:
            gateway_loc = GatewayLocation()
            gateway_loc.ParseFromString(sock.recv(1024))
            GATEWAY_ADDR = (gateway_loc.address.ip, gateway_loc.address.port)
    device_info = DeviceInfo()
    device_info.name = NAME
    device_info.state = json.dumps(STATE, sort_keys=True)
    device_info.metadata = json.dumps(METADATA, sort_keys=True)
    join_req = JoinRequest()
    join_req.device_info = device_info
    join_req.device_address = Address(*DEVICE_ADDR)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(GATEWAY_ADDR)
        sock.send(join_req.SerializeToString())
        join_reply = JoinReply()
        join_reply.ParseFromString(sock.recv(1024))
        GATEWAY_ADDR = (join_reply.report_address.ip, join_reply.report_address.port)
        REPORT_INTERVAL = join_reply.report_interval


def get_reading():
    global BASE_TEMP
    temp = min(max(BASE_TEMP + random.random() - 0.5, 20), 40)
    BASE_TEMP = temp
    return temp


def transmit_readings(sock):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while GATEWAY_ADDR is not None:
            reading = SensorReading()
            reading.sensor_name = NAME
            reading.reading_value = '%.2f' %get_reading()
            reading.timestamp = datetime.datetime.now(tz=datetime.UTC).isoformat()
            reading.metadata = json.dumps(METADATA, sort_keys=True)
            sock.sendto(reading.SerializeToString(), GATEWAY_ADDR)
            time.sleep(REPORT_INTERVAL)


def run():
    while True:
        while GATEWAY_ADDR is None or REPORT_INTERVAL is None:
            discover_gateway()
        transmit_readings()


if __name__ == '__main__':
    run()
