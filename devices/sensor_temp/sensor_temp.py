import json
import socket
import time
import datetime
from messages_pb2 import GatewayLocation, Address, DeviceInfo, JoinRequest, JoinReply


NAME = "Sensor-Temp-01"
DEVICE_ADDR = (socket.gethostbyname(socket.gethostname()), 5000)
MULTICAST_ADDR = ('224.0.1.0', 12345)
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
        REPORT_INTERVAL = join_reply.report_interval


# def announce():
#     info = DispositivoInfo(tipo="sensor", id=ID, ip="127.0.0.1", porta=6001, estado="ativo")
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#     sock.sendto(info.SerializeToString(), ("224.0.0.1", 5000))

# def enviar_leitura():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     while True:
#         if FALHA:
#             print("[sensor_temp1] FALHA: parando envio.")
#             break
#         leitura = LeituraSensor(
#             id=ID,
#             tipo="temperatura",
#             valor="24.7",
#             timestamp=str(datetime.datetime.now())
#         )
#         s.sendto(leitura.SerializeToString(), ("127.0.0.1", 7000))
#         time.sleep(15)

# announce()
# enviar_leitura()
