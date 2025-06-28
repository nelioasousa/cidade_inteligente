import sys
import time
import socket
import threading
import logging


def connect_to_gateway(args):
    logger = logging.getLogger('GATEWAY_CONNECTION')
    logger.info(
        'Tentando conexão com o Gateway em (%s, %s)',
        args.gateway_ip, args.gateway_port
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        sock.connect((args.gateway_ip, args.gateway_port))
        logger.info('Conexão com o Gateway bem-sucedida')
        while not args.stop_flag.is_set():
            time.sleep(2.0)


def _run(args):
    logging.basicConfig(
        level=args.level,
        handlers=(logging.StreamHandler(sys.stdout),),
        format='[%(levelname)s %(asctime)s] %(name)s\n  %(message)s',
    )
    try:
        connect_to_gateway(args)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            print('\nDESLIGANDO...')
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

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN", "ERROR".'
    )

    args = parser.parse_args()

    # Logging
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'

    # Timeouts
    args.base_timeout = 5.0

    # Events
    args.stop_flag = threading.Event()

    return _run(args)

if __name__ == '__main__':
    main()
