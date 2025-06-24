import socket
import threading
import time
import json
from db import Database
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import message
from messages_pb2 import Address, SensorReading
from messages_pb2 import JoinRequest, JoinReply
from messages_pb2 import DeviceRequest, DeviceReply, RequestType


def multicast_location(args):
    addrs = Address(ip=args.host_ip, port=args.registration_port)
    addrs = addrs.SerializeToString()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        while not args.stop_flag.is_set():
            sock.sendto(addrs, (args.multicast_ip, args.multicast_port))
            time.sleep(args.multicast_interval)


def join_handler(args, sock):
    print('Tratando pedido de ingresso')
    try:
        sock.settimeout(args.base_timeout)
        req = JoinRequest()
        req.ParseFromString(sock.recv(1024))
        name = req.device_info.name
        if name.startswith('Sensor'):
            report_interval = args.sensors_report_interval
            report_port = args.sensors_port
        else:
            report_interval = args.actuators_report_interval
            report_port = args.actuators_port
        report_address = Address(ip=args.host_ip, port=report_port)
        sock.send(
            JoinReply(
                report_address=report_address, report_interval=report_interval
            ).SerializeToString()
        )
        with args.db_lock:
            args.db.register_decive(
                name=name,
                address=(req.device_address.ip, req.device_address.port),
                state_json=json.loads(req.device_info.state),
            )
        print(f'Ingresso bem-sucedido: {name}')
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def join_listener(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.registration_port))
        sock.listen()
        print('Ouvindo requisições de ingresso')
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, _ = sock.accept()
                except TimeoutError:
                    continue
                executor.submit(join_handler, args, conn)


def sensors_listener(args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', args.sensors_port))
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            try:
                msg, _ = sock.recvfrom(1024)
                reading = SensorReading()
                reading.ParseFromString(msg)
            except (TimeoutError, message.DecodeError):
                continue
            name = reading.sensor_name
            if not args.db.is_device_registered(name):
                continue
            if name.startswith('Sensor-Temp'):
                print('Leitura de temperatura recebida')
                reading_value = float(reading.reading_value)
                data_item = (reading.timestamp, reading_value)
            with args.db_lock:
                args.db.insert_data_item(name, data_item)


def simulate_requests(args):
    device = args.db.get_device('Sensor-Temp-01')
    if device is None:
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print('Solicitar ação do sensor')
        sock.connect(device['address'])
        sock.settimeout(args.base_timeout)
        req = DeviceRequest(type=RequestType.ACTION, body='')
        sock.send(req.SerializeToString())
        reply = DeviceReply()
        reply.ParseFromString(sock.recv(1024))
        print(f'Ação bem-sucedida? {reply.status}: {reply.body}')
        sock.shutdown(socket.SHUT_RDWR)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print('Requisitando estado do dispositivo')
        sock.connect(device['address'])
        sock.settimeout(args.base_timeout)
        req = DeviceRequest(type=RequestType.GET_STATE)
        sock.send(req.SerializeToString())
        reply = DeviceReply()
        reply.ParseFromString(sock.recv(1024))
        print(f'Resultado da requisição: {reply.status}: {reply.body}')
        sock.shutdown(socket.SHUT_RDWR)


def _run(args):
    try:
        jlistener = threading.Thread(
            target=join_listener, args=(args,)
        )
        slistener = threading.Thread(
            target=sensors_listener, args=(args,)
        )
        multicaster = threading.Thread(
            target=multicast_location, args=(args,)
        )
        jlistener.start()
        slistener.start()
        multicaster.start()
        while True:
            time.sleep(10.0)
            if args.db.has_data():
                simulate_requests(args)
    except BaseException as e:
        args.stop_flag.set()
        if isinstance(e, KeyboardInterrupt):
            print('\rDESLIGANDO...')
        else:
            raise e
    finally:
        multicaster.join()
        slistener.join()
        jlistener.join()
        args.db.persist()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gateway')

    parser.add_argument(
        '--clients_port', type=int, default=50111,
        help='Porta para comunicação com os clientes. Usa TCP.'
    )

    parser.add_argument(
        '--registration_port', type=int, default=50111,
        help='Porta em que os dispositivos se registram no Gateway. Usa TCP.'
    )

    parser.add_argument(
        '--sensors_port', type=int, default=50222,
        help='Porta de recebimento de dados sensoriais. Usa UDP.'
    )

    parser.add_argument(
        '--actuators_port', type=int, default=50333,
        help='Porta de recebimento dos dados dos atuadores. Usa UDP.'
    )

    parser.add_argument(
        '--multicast_ip', type=str, default='224.0.1.0',
        help='IP para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_port', type=int, default=12345,
        help='Porta para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_interval', type=float, default=2.5,
        help='Intervalo de envio do endereço do Gateway para o grupo multicast.'
    )

    parser.add_argument(
        '--sensors_report_interval', type=float, default=1.0,
        help='Intervalo de envio de dados dos sensores.'
    )

    parser.add_argument(
        '--actuators_report_interval', type=float, default=5.0,
        help='Intervalo de envio de dados dos atuadores.'
    )

    args = parser.parse_args()
    args.base_timeout = 2.5
    args.host_ip = socket.gethostbyname(socket.gethostname())
    args.db = Database()
    args.stop_flag = threading.Event()
    args.db_lock = threading.Lock()

    return _run(args)


if __name__ == '__main__':
    main()
