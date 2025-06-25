import json
import socket
import time
import datetime
import random
import threading
from messages_pb2 import Address, SensorReading
from messages_pb2 import DeviceType, DeviceInfo, JoinRequest, JoinReply


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
    args.report_interval = None
    return


def try_to_connect(args, addrs):
    print('Tentando conectar com', addrs)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        try:
            sock.connect(addrs)
            device_info = DeviceInfo(
                type=DeviceType.SENSOR,
                name=args.name,
                metadata=json.dumps(args.metadata),
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
    args.report_interval = join_reply.report_interval
    return True


def get_reading(args):
    temp = args.temperature + random.random() - 0.5
    temp = min(max(temp, args.min_temperature), args.max_temperature)
    args.temperature = temp
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
                    reading_value=str(get_reading(args)),
                    timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                    metadata=json.dumps(args.metadata),
                )
                sock.sendto(
                    reading.SerializeToString(),
                    (args.gateway_ip, args.transmission_port),
                )
                print('Leitura de temperatura enviada')
                time.sleep(args.report_interval)


def _run(args):
    try:
        transmiter = threading.Thread(target=transmit_readings, args=(args,))
        transmiter.start()
        gateway_discoverer(args)
    except BaseException as e:
        args.stop_flag.set()
        if isinstance(e, KeyboardInterrupt):
            print('\rDESLIGANDO...')
        else:
            raise e
    finally:
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
    args.name = f'Temperature-{args.name}'
    args.base_timeout = 2.5
    args.multicast_timeout = 5.0
    args.host_ip = socket.gethostbyname(socket.gethostname())
    args.gateway_ip = None
    args.transmission_port = None
    args.report_interval = None
    args.metadata = {
        'UnitName': 'Celsius',
        'UnitSymbol': '°C',
        'Location': {'Latitude': -3.733486, 'Longitude': -38.570860},
    }
    args.stop_flag = threading.Event()

    return _run(args)


if __name__ == '__main__':
    main()
