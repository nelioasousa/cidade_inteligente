import socket
import threading
import time
import json
from datetime import datetime
from db import Database
from concurrent.futures import ThreadPoolExecutor
from google.protobuf import message
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceType, JoinRequest, JoinReply
from messages_pb2 import SensorsReport


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
        if req.device_info.type is DeviceType.SENSOR:
            report_interval = args.sensors_report_interval
            report_port = args.sensors_port
            with args.db_sensors_lock:
                args.db.register_sensor(
                    name=req.device_info.name,
                    address=(req.device_address.ip, req.device_address.port),
                    metadata=json.loads(req.device_info.metadata),
                )
        elif req.device_info.type is DeviceType.ACTUATOR:
            report_interval = args.actuators_report_interval
            report_port = args.actuators_port
            # with args.db_actuators_lock:
            #     args.db.register_actuator(...)
        else:
            raise RuntimeError('Invalid device type')
        report_address = Address(ip=args.host_ip, port=report_port)
        reply = JoinReply(
            report_address=report_address,
            report_interval=report_interval,
        )
        sock.send(reply.SerializeToString())
        print(f'Ingresso bem-sucedido: {req.device_info.name}')
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
            if name.startswith('Temperature'):
                print('Leitura de temperatura recebida')
                value = float(reading.reading_value)
                timestamp = datetime.fromisoformat(reading.timestamp)
                metadata = json.loads(reading.metadata)
            else:
                return
            with args.db_sensors_lock:
                args.db.add_sensor_reading(name, value, timestamp, metadata)


def send_report(args, sock):
    with args.db_sensors_lock:
        sensors_summary = args.db.get_sensors_summary()
    for i, sensor_summary in enumerate(sensors_summary):
        not_seen_since = (time.monotonic() - sensor_summary['last_seen'])
        sensors_summary[i] = SensorReading(
            sensor_name=sensor_summary['sensor_name'],
            reading_value=str(sensor_summary['reading_value']),
            timestamp=sensor_summary['timestamp'].isoformat(),
            metadata=json.dumps(sensor_summary['metadata']),
            is_online=(not_seen_since <= 2 * args.sensors_report_interval),
        )
    print(f'Número de sensores reportados: {len(sensors_summary)}')
    sensors_report = SensorsReport(readings=sensors_summary)
    try:
        sock.send(sensors_report.SerializeToString())
    except Exception:
        print(f'Erro ao enviar relatório para {sock.getpeername()}')
        return


def client_handler(args, sock):
    try:
        sock.settimeout(args.client_timeout)
        while not args.stop_flag.is_set():
            print(f'Enviando relatório para cliente em {sock.getpeername()}')
            send_report(args, sock)
            try:
                _ = sock.recv(1024)
            except TimeoutError:
                continue
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


def clients_listener(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.clients_port))
        sock.listen()
        print('Ouvindo requisições dos clientes')
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, addrs = sock.accept()
                    print(f'Conectado com {addrs}')
                except TimeoutError:
                    continue
                executor.submit(client_handler, args, conn)


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
        clients_listener(args)
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
        '--clients_port', type=int, default=5000,
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
    args.client_timeout = 1.0
    args.host_ip = socket.gethostbyname(socket.gethostname())
    args.db = Database()
    args.stop_flag = threading.Event()
    args.db_sensors_lock = threading.Lock()

    return _run(args)


if __name__ == '__main__':
    main()
