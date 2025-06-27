import sys
import time
import socket
import threading
import logging
from google.protobuf import message
from messages_pb2 import SensorsReport
from struct import unpack


def recv_exaclty(sock, n, retries=2):
    msg_chunks = []
    remaining = n
    while remaining:
        try:
            chunk = sock.recv(remaining)
        except TimeoutError as e:
            retries -= 1
            if not retries:
                raise e
            continue
        if not chunk:
            raise EOFError('Socket closed before receiving all expected data')
        msg_chunks.append(chunk)
        remaining -= len(chunk)
    return b''.join(msg_chunks)


def recv_report(sock):
    report_size = recv_exaclty(sock, 4)
    report_size = unpack('!I', report_size)[0]
    msg = recv_exaclty(sock, report_size)
    report = SensorsReport()
    report.ParseFromString(msg)
    return report


def connect_to_gateway(args):
    logger = logging.getLogger('GATEWAY_CONNECTION')
    logger.info(
        'Tentando conexão com o Gateway em (%s, %s)',
        args.gateway_ip, args.gateway_port
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(args.base_timeout)
        sock.connect((args.gateway_ip, args.gateway_port))
        logger.info('Conexão bem-sucedida')
        while not args.stop_flag.is_set():
            try:
                report = recv_report(sock)
                if args.verbose:
                    logger.info(
                        'Relatório de %d dispositivo(s) recebido: %s',
                        len(report.devices), report
                    )
            except TimeoutError:
                logger.error('Timeout na comunicação com o Gateway')
                continue
            except message.DecodeError as e:
                logger.error(
                    'Falha durante a desserialização da mensagem: (%s) %s',
                    type(e).__name__, e
                )
                continue
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
        '-v', '--verbose', action='store_true',
        help='Torna o Gateway verboso ao logar informações.'
    )

    parser.add_argument(
        '-l', '--level', type=str, default='INFO',
        help='Nível do logging. Valores permitidos são "DEBUG", "INFO", "WARN", "ERROR".'
    )

    args = parser.parse_args()
    lvl = args.level.strip().upper()
    args.level = lvl if lvl in ('DEBUG', 'WARN', 'ERROR') else 'INFO'
    if args.level == 'DEBUG':
        args.verbose = True
    args.base_timeout = 5.0
    args.stop_flag = threading.Event()

    return _run(args)

if __name__ == '__main__':
    main()
