import socket
import threading
import time
import json
import datetime
from messages_pb2 import Address, GatewayLocation, SensorReading
from messages_pb2 import JoinRequest, JoinReply


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
    msg = GatewayLocation(address=address)
    while True:
        sock.sendto(msg.SerializeToString(), MULTICAST_ADDR)
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
            if name.startswith('Sensor-Temp'):
                reading_value = float(reading.reading_value)
                timestamp = datetime.datetime.fromisoformat(reading.timestamp)
                DEVICES[name]['data'].append((timestamp, reading_value))
                DEVICES[name]['data'].sort(key=(lambda x: x[0]))
            else:
                continue


# def monitoramento():
#     while True:
#         now = time.time()
#         for id, (info, addr, last_seen) in list(DEVICES.items()):
#             if now - last_seen > 30:
#                 print(f"[ALERTA] {id} inativo. Removendo...")
#                 DEVICES.pop(id)
#         time.sleep(10)


# def handle_client(conn):
#     while True:
#         data = conn.recv(1024)
#         if not data:
#             break
#         cmd = Comando()
#         cmd.ParseFromString(data)
#         if cmd.id == "LISTAR":
#             resposta = ListaDispositivos()
#             for d in DEVICES.values():
#                 resposta.dispositivos.append(d[0])
#             conn.send(resposta.SerializeToString())
#         elif cmd.id in DEVICES:
#             _, (ip, _) , _ = DEVICES[cmd.id]
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.connect((ip, 6000))
#                 s.send(data)
#                 resposta = s.recv(1024)  # Recebe a resposta do dispositivo
#                 conn.send(resposta)  # Encaminha a resposta ao cliente
#                 DEVICES[cmd.id] = (
#                     DEVICES[cmd.id][0], DEVICES[cmd.id][1], time.time()
#                 )


# def client_listener():
#     server = socket.socket()
#     server.bind(("0.0.0.0", 9000))
#     server.listen()
#     while True:
#         conn, _ = server.accept()
#         threading.Thread(
#             target=handle_client, args=(conn,), daemon=True
#         ).start()


if __name__ == '__main__':
    threading.Thread(target=multicast_gateway_location, daemon=True).start()
    threading.Thread(target=join_listener, daemon=True).start()
    threading.Thread(target=sensors_listener, daemon=True).start()
    while True:
        time.sleep(10)
