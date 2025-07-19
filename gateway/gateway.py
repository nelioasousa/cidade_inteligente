import sys
import socket
import threading
import logging
from db.sessions import init_db
from registration_handler import multicast_location, registration_listener
from sensors_handler import sensors_listener
from actuators_handler import actuators_listener
from clients_handler import clients_listener
from functools import wraps


def stop_wrapper(func, stop_flag):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            stop_flag.set()
    return wrapper


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        rlistener = threading.Thread(
            target=stop_wrapper(registration_listener, args.stop_flag),
            args=(args,)
        )
        slistener = threading.Thread(
            target=stop_wrapper(sensors_listener, args.stop_flag),
            args=(args,)
        )
        alistener = threading.Thread(
            target=stop_wrapper(actuators_listener, args.stop_flag),
            args=(args,)
        )
        multicaster = threading.Thread(
            target=stop_wrapper(multicast_location, args.stop_flag),
            args=(args,)
        )
        rlistener.start()
        slistener.start()
        alistener.start()
        multicaster.start()
        clients_listener(args)
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN...')
    finally:
        args.stop_flag.set()
        rlistener.join()
        slistener.join()
        alistener.join()
        multicaster.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Gateway')

    parser.add_argument(
        '--clients_port', type=int, default=50000,
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
        help='Porta de recebimento dos dados dos atuadores. Usa TCP.'
    )

    parser.add_argument(
        '--multicast_ip', type=str, default='224.0.1.0',
        help='IP para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_port', type=int, default=50444,
        help='Porta para multicast do endereço do Gateway.'
    )

    parser.add_argument(
        '--multicast_interval', type=float, default=2.5,
        help='Intervalo de envio do endereço do Gateway para o grupo multicast.'
    )

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN" e "ERROR".'
    )

    parser.add_argument(
        '-c', '--clear', action='store_true',
        help='Limpar o banco de dados ao iniciar.'
    )

    args = parser.parse_args()

    # Logging
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'

    # Timeouts
    args.base_timeout = 1.0

    # Host IP
    args.host_ip = socket.gethostbyname('localhost')

    # Database
    init_db(args.clear)

    # Stop event
    args.stop_flag = threading.Event()

    # Tolerances
    args.sensors_tolerance = 6.0
    args.actuators_tolerance = 6.0

    return _run(args)


if __name__ == '__main__':
    main()
