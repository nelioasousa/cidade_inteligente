import time
import json
import socket
import logging
import datetime
import threading
from functools import wraps
from actuators_handler import send_actuator_command
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import ConnectionRequest
from messages_pb2 import RequestType, ClientRequest
from messages_pb2 import ReplyStatus, ClientReply
from messages_pb2 import SensorData
from messages_pb2 import SendNextReport
from messages_pb2 import ActuatorUpdate, CommandType, ComplyStatus


def transmit_sensors_reports(args, address, stop_transmission_flag):
    logger = logging.getLogger(f'TRANSMIT_SENSORS_REPORTS_{address}')
    logger.info(
        'Preparando envio de relatórios para o cliente em %s',
        address,
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.settimeout(args.cautious_timeout)
        try:
            sock.connect(address)
        except Exception as e:
            logger.error(
                'Erro ao estabelecer conexão para '
                'envio de relatórios: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        last_report_sent = 0
        sock.settimeout(args.generous_timeout)
        while not (args.stop_flag.is_set() or stop_transmission_flag.is_set()):
            with args.db_sensors_report_lock:
                report_number, report = args.db.sensors_report
            if report_number <= last_report_sent:
                time.sleep(1.0)
                continue
            try:
                sent = sock.send(report)
                if len(report) != sent:
                    raise RuntimeError('Not all data was sent')
            except Exception as e:
                logger.error(
                    'Erro ao tentar enviar relatório #%d',
                    report_number,
                )
                raise e
            try:
                msg = sock.recv(1024)
            except Exception as e:
                logger.error(
                    'Erro no recebimento da confirmação '
                    'de envio do relatório #%d',
                    report_number,
                )
                raise e
            confirmation = SendNextReport()
            confirmation.ParseFromString(msg)
            last_report_sent = report_number


def transmit_actuators_reports(args, address, stop_transmission_flag):
    logger = logging.getLogger(f'TRANSMIT_ACTUATORS_REPORTS_{address}')
    logger.info(
        'Preparando envio de relatórios para o cliente em %s',
        address,
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.settimeout(args.cautious_timeout)
        try:
            sock.connect(address)
        except Exception as e:
            logger.error(
                'Erro ao estabelecer conexão para '
                'envio de relatórios: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        last_report_sent = 0
        sock.settimeout(args.generous_timeout)
        while not (args.stop_flag.is_set() or stop_transmission_flag.is_set()):
            with args.db_actuators_report_lock:
                report_number, report = args.db.actuators_report
            if report_number <= last_report_sent:
                time.sleep(1.0)
                continue
            try:
                sent = sock.send(report)
                if len(report) != sent:
                    raise RuntimeError('Not all data was sent')
            except Exception as e:
                logger.error(
                    'Erro ao tentar enviar relatório #%d',
                    report_number,
                )
                raise e
            try:
                msg = sock.recv(1024)
            except Exception as e:
                logger.error(
                    'Erro no recebimento da confirmação '
                    'de envio do relatório #%d',
                    report_number,
                )
                raise e
            confirmation = SendNextReport()
            confirmation.ParseFromString(msg)
            last_report_sent = report_number


def stop_wrapper(func, stop_flag):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            stop_flag.set()
    return wrapper


def init_transmissions(
    args,
    client_ip,
    sensors_port,
    actuators_port,
    stop_transmission_flag,
):
    sensors_reporter = stop_wrapper(
        transmit_sensors_reports, stop_transmission_flag,
    )
    sensors_thread = threading.Thread(
        target=sensors_reporter,
        args=(args, (client_ip, sensors_port), stop_transmission_flag),
    )
    actuators_reporter = stop_wrapper(
        transmit_actuators_reports, stop_transmission_flag,
    )
    actuators_thread = threading.Thread(
        target=actuators_reporter,
        args=(args, (client_ip, actuators_port), stop_transmission_flag),
    )
    sensors_thread.start()
    actuators_thread.start()
    return sensors_thread, actuators_thread


def process_client_request(args, request):
    match request.type:
        case RequestType.RT_GET_SENSOR_DATA:
            with args.db_sensors_lock:
                sensor = args.db.get_sensor(request.device_name)
            if sensor is None:
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            readings = [
                SensorData.SimpleReading(
                    timestamp=timestamp.isoformat(),
                    reading_value=reading,
                )
                for timestamp, reading in sensor['data']
            ]
            ls_day, ls_clock = sensor['last_seen']
            is_online = (
                ls_day == datetime.date.today()
                and (time.monotonic() - ls_clock) <= args.sensors_tolerance
            )
            data = SensorData(
                device_name=request.device_name,
                metadata=json.dumps(sensor['metadata']),
                readings=readings,
                is_online=is_online,
            )
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=request.type,
                data=data.SerializeToString(),
            )
        case RequestType.RT_GET_ACTUATOR_UPDATE:
            with args.db_actuators_lock:
                actuator = args.db.get_actuator(request.device_name)
            if actuator is None:
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            update = ActuatorUpdate(
                device_name=request.device_name,
                state=json.dumps(actuator['state']),
                metadata=json.dumps(actuator['metadata']),
                timestamp=actuator['timestamp'].isoformat(),
                is_online=actuator['is_online'],
            )
            return ClientReply(
                status=ReplyStatus.OK,
                reply_to=request.type,
                data=update.SerializeToString(),
            )
        case RequestType.RT_SET_ACTUATOR_STATE:
            if not args.db.is_actuator_registered():
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            actuator_comply = send_actuator_command(
                args=args,
                actuator_name=request.device_name,
                command_type=CommandType.CT_SET_STATE,
                command_body=request.body,
            )
            if (
                actuator_comply is None
                or actuator_comply.status is ComplyStatus.CS_FAIL
            ):
                return ClientReply(
                    status=ReplyStatus.RS_FAIL, reply_to=request.type,
                )
            if actuator_comply.status is ComplyStatus.CS_INVALID_STATE:
                return ClientReply(
                    status=ReplyStatus.RS_INVALID_STATE,
                    reply_to=request.type,
                    data=actuator_comply.update.SerializeToString(),
                )
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=request.type,
                data=actuator_comply.update.SerializeToString(),
            )
        case RequestType.RT_RUN_ACTUATOR_ACTION:
            if not args.db.is_actuator_registered():
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            actuator_comply = send_actuator_command(
                args=args,
                actuator_name=request.device_name,
                command_type=CommandType.CT_ACTION,
                command_body=request.body,
            )
            if (
                actuator_comply is None
                or actuator_comply.status is ComplyStatus.CS_FAIL
            ):
                return ClientReply(
                    status=ReplyStatus.RS_FAIL, reply_to=request.type,
                )
            if actuator_comply.status is ComplyStatus.CS_UNKNOWN_ACTION:
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_ACTION,
                    reply_to=request.type,
                    data=actuator_comply.update.SerializeToString(),
                )
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=request.type,
                data=actuator_comply.update.SerializeToString(),
            )


def client_handler(args, sock, address):
    try:
        transmission_stop_flag = threading.Event()
        logger = logging.getLogger(f'CLIENT_HANDLER_{address}')
        logger.info('Gerenciando conexão com o cliente em %s', address)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # sock.settimeout(...)
        try:
            conn_req = ConnectionRequest()
            conn_req.ParseFromString(sock.recv(1024))
        except Exception as e:
            logger.error(
                'Não foi possível estabelecer conexão com o cliente: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        init_transmissions(
            args,
            address[0],
            conn_req.sensors_port,
            conn_req.actuators_port,
            transmission_stop_flag,
        )
        while not (args.stop_flag.is_set() or transmission_stop_flag.is_set()):
            try:
                request = ClientRequest()
                request.ParseFromString(sock.recv(1024))
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(
                    'Erro durante o recebimento da '
                    'requisição do cliente: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            try:
                reply = process_client_request(args, request)
                reply = reply.SerializeToString()
            except Exception as e:
                logger.error(
                    'Erro durante o processamento da '
                    'requisição do cliente: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
            try:
                sent = sock.send(reply)
                if len(reply) != sent:
                    raise RuntimeError('Not all data was sent')
            except Exception as e:
                logger.error(
                    'Erro ao enviar resposta ao cliente: (%s) %s',
                    type(e).__name__,
                    e,
                )
                raise e
    finally:
        try:
            transmission_stop_flag.set()
        finally:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()


def clients_listener(args):
    logger = logging.getLogger('CLIENTS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.clients_port))
        sock.listen()
        logger.info(
            'Escutando pedidos de conexão dos clientes em (%s, %s)',
            args.host_ip,
            args.clients_port,
        )
        sock.settimeout(args.base_timeout)
        with ThreadPoolExecutor(max_workers=5) as executor:
            while not args.stop_flag.is_set():
                try:
                    conn, addrs = sock.accept()
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.error(
                        'Erro ao tentar conexão com um novo cliente: (%s) %s',
                        type(e).__name__,
                        e,
                    )
                    raise e
                try:
                    executor.submit(client_handler, args, conn, addrs)
                except:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    raise
