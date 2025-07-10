import time
import json
import socket
import logging
import datetime
from struct import pack
from actuators_handler import send_actuator_command
from concurrent.futures import ThreadPoolExecutor
from messages_pb2 import SensorData
from messages_pb2 import RequestType, ClientRequest
from messages_pb2 import ReplyStatus, ClientReply
from messages_pb2 import ActuatorUpdate, CommandType, ComplyStatus


def get_sensors_report(args):
    with args.db_sensors_report_lock:
        return args.db.sensors_report


def get_actuators_report(args):
    with args.db_actuators_report_lock:
        return args.db.actuators_report


def build_sensor_data(args, device_name):
    with args.db_sensors_lock:
        sensor = args.db.get_sensor(device_name)
    if sensor is None:
        return None
    readings = [
        SensorData.SimpleReading(
            timestamp=timestamp.isoformat(), reading_value=reading,
        )
        for timestamp, reading in sensor['data']
    ]
    ls_day, ls_clock = sensor['last_seen']
    is_online = (
        ls_day == datetime.date.today()
        and (time.monotonic() - ls_clock) <= args.sensors_tolerance
    )
    return SensorData(
        device_name=device_name,
        metadata=json.dumps(sensor['metadata']),
        readings=readings,
        is_online=is_online,
    )


def build_actuator_update(args, device_name):
    with args.db_actuators_lock:
        actuator = args.db.get_actuator(device_name)
    if actuator is None:
        return None
    now_clock = time.monotonic()
    tolerance = args.actuators_tolerance
    last_seen = actuator['last_seen']
    is_online = (
        last_seen[0] == datetime.date.today()
        and (now_clock - last_seen[1]) <= tolerance
    )
    return ActuatorUpdate(
        device_name=device_name,
        state=json.dumps(actuator['state']),
        metadata=json.dumps(actuator['metadata']),
        timestamp=actuator['timestamp'].isoformat(),
        is_online=is_online,
    )


def process_set_actuator_state(args, device_name, state_string):
    if not args.db.is_actuator_registered(device_name):
        return ClientReply(
            status=ReplyStatus.RS_UNKNOWN_DEVICE,
            reply_to=RequestType.RT_SET_ACTUATOR_STATE,
        )
    comply_msg = send_actuator_command(
        args=args,
        actuator_name=device_name,
        command_type=CommandType.CT_SET_STATE,
        command_body=state_string,
    )
    if comply_msg is None or comply_msg.status is ComplyStatus.CS_FAIL:
        return ClientReply(
            status=ReplyStatus.RS_FAIL,
            reply_to=RequestType.RT_SET_ACTUATOR_STATE,
        )
    if comply_msg.status is ComplyStatus.CS_INVALID_STATE:
        return ClientReply(
            status=ReplyStatus.RS_INVALID_STATE,
            reply_to=RequestType.RT_SET_ACTUATOR_STATE,
        )
    return ClientReply(
        status=ReplyStatus.RS_OK,
        reply_to=RequestType.RT_SET_ACTUATOR_STATE,
        data=comply_msg.update.SerializeToString(),
    )


def process_run_actuator_action(args, device_name, action_name):
    if not args.db.is_actuator_registered(device_name):
        return ClientReply(
            status=ReplyStatus.RS_UNKNOWN_DEVICE,
            reply_to=RequestType.RT_RUN_ACTUATOR_ACTION,
        )
    comply_msg = send_actuator_command(
        args=args,
        actuator_name=device_name,
        command_type=CommandType.CT_ACTION,
        command_body=action_name,
    )
    if comply_msg is None or comply_msg.status is ComplyStatus.CS_FAIL:
        return ClientReply(
            status=ReplyStatus.RS_FAIL,
            reply_to=RequestType.RT_RUN_ACTUATOR_ACTION,
        )
    if comply_msg.status is ComplyStatus.CS_UNKNOWN_ACTION:
        return ClientReply(
            status=ReplyStatus.RS_UNKNOWN_ACTION,
            reply_to=RequestType.RT_RUN_ACTUATOR_ACTION,
        )
    return ClientReply(
        status=ReplyStatus.RS_OK,
        reply_to=RequestType.RT_RUN_ACTUATOR_ACTION,
        data=comply_msg.update.SerializeToString(),
    )


def process_client_request(args, request):
    match request.type:
        case RequestType.RT_GET_SENSORS_REPORT:
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=RequestType.RT_GET_SENSORS_REPORT,
                data=get_sensors_report(args),
            )
        case RequestType.RT_GET_ACTUATORS_REPORT:
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=RequestType.RT_GET_ACTUATORS_REPORT,
                data=get_actuators_report(args),
            )
        case RequestType.RT_GET_SENSOR_DATA:
            data = build_sensor_data(args, request.device_name)
            if data is None:
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=request.type,
                data=data.SerializeToString(),
            )
        case RequestType.RT_GET_ACTUATOR_UPDATE:
            update = build_actuator_update(args, request.device_name)
            if update is None:
                return ClientReply(
                    status=ReplyStatus.RS_UNKNOWN_DEVICE,
                    reply_to=request.type,
                )
            return ClientReply(
                status=ReplyStatus.RS_OK,
                reply_to=request.type,
                data=update.SerializeToString(),
            )
        case RequestType.RT_SET_ACTUATOR_STATE:
            return process_set_actuator_state(
                args=args,
                device_name=request.device_name,
                state_string=request.body,
            )
        case RequestType.RT_RUN_ACTUATOR_ACTION:
            return process_run_actuator_action(
                args=args,
                device_name=request.device_name,
                action_name=request.body,
            )
        case _:
            return ClientReply(
                status=ReplyStatus.RS_FAIL,
                reply_to=RequestType.RT_UNSPECIFIED,
            )


def frame_message(message):
    msg_size = len(message)
    msg_size = pack('!I', msg_size)
    return msg_size + message


def client_handler(args, sock, address):
    try:
        logger = logging.getLogger(f'CLIENT_HANDLER_{address}')
        logger.info('Tratando requisição de um cliente em %s', address)
        try:
            msg = sock.recv(1024)
            request = ClientRequest()
            request.ParseFromString(msg)
        except Exception as e:
            logger.error(
                'Error ao tentar receber requisição do cliente: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        try:
            reply = process_client_request(args, request)
            reply = reply.SerializeToString()
        except Exception as e:
            logger.error(
                'Erro durante o processamento da requisição: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
        try:
            sock.sendall(frame_message(reply))
        except Exception as e:
            logger.error(
                'Erro ao enviar resposta ao cliente: (%s) %s',
                type(e).__name__,
                e,
            )
            raise e
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            logger.error(
                'Erro ao tentar enviar FIN para %s',
                address,
            )
        finally:
            sock.close()


def clients_listener(args):
    logger = logging.getLogger('CLIENTS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', args.clients_port))
        sock.listen()
        logger.info(
            'Escutando por requisições dos clientes em (%s, %s)',
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
                    conn.settimeout(sock.gettimeout())
                    executor.submit(client_handler, args, conn, addrs)
                except Exception:
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        logger.error(
                            'Erro ao tentar enviar FIN para %s',
                            addrs,
                        )
                    finally:
                        conn.close()
                    raise
