import time
import socket
import threading
from messages_pb2 import SensorReading, SensorsReport


def connect_to_gateway(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        sock.connect((args.gateway_ip, args.gateway_port))
        while not args.stop_flag.is_set():
            try:
                report = SensorsReport()
                report.ParseFromString(sock.recv(1024))
                print(report)
            except Exception:
                import traceback
                traceback.print_exc()
                continue
            time.sleep(2.0)


def _run(args):
    try:
        connect_to_gateway(args)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            print('\rDESLIGANDO...')
        else:
            raise e


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente simples em Python')

    parser.add_argument(
        '--gateway_ip', type=str, default='localhost',
        help='IP do Gateway (servidor).'
    )

    parser.add_argument(
        '--gateway_port', type=int, default=5000,
        help='Porta do Gateway para comunicação com clientes.'
    )

    args = parser.parse_args()
    args.base_timeout = 5.0
    args.stop_flag = threading.Event()

    return _run(args)

if __name__ == '__main__':
    main()
