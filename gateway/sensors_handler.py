import json
import time
import socket
import logging
from datetime import date, datetime
from google.protobuf import message
from messages_pb2 import SensorReading, SensorsReport


def sensors_report_generator(args):
    logger = logging.getLogger('SENSORS_REPORT_GENERATOR')
    logger.info('Iniciando o gerador de relatórios dos sensores')
    while not args.stop_flag.is_set():
        with args.db_sensors_lock:
            sensors = args.db.get_sensors_summary()
        today = date.today()
        now_clock = time.monotonic()
        for i, sensor_summary in enumerate(sensors):
            last_seen = sensor_summary['last_seen']
            is_online = (
                last_seen[0] == today
                and (now_clock - last_seen[1]) <= args.sensors_tolerance
            )
            sensors[i] = SensorReading(
                device_name=sensor_summary['device_name'],
                reading_value=str(sensor_summary['reading_value']),
                timestamp=sensor_summary['timestamp'].isoformat(),
                metadata=json.dumps(sensor_summary['metadata']),
                is_online=is_online,
            )
        if args.verbose:
            logger.info(
                'Novo relatório: %d sensores reportados', len(sensors)
            )
        report_msg = SensorsReport(devices=sensors).SerializeToString()
        with args.db_sensors_report_lock:
            args.db.att_sensors_report(report_msg)
        time.sleep(args.sensors_gen_interval)


def sensors_listener(args):
    logger = logging.getLogger('SENSORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', args.sensors_port))
        logger.info(
            'Escutando por dados sensoriais em (%s, %s)',
            args.host_ip, args.sensors_port
        )
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            try:
                msg, _ = sock.recvfrom(1024)
                reading = SensorReading()
                reading.ParseFromString(msg)
            except (TimeoutError, message.DecodeError):
                continue
            name = reading.device_name
            if name.startswith('Temperature'):
                value = float(reading.reading_value)
                timestamp = datetime.fromisoformat(reading.timestamp)
                metadata = json.loads(reading.metadata)
                if args.verbose:
                    logger.info(
                        'Leitura de temperatura recebida: (%s, %s %s, %s)',
                        name, value, metadata['UnitSymbol'], reading.timestamp
                    )
            else:
                continue
            with args.db_sensors_lock:
                result = args.db.add_sensor_reading(name, value, metadata, timestamp)
            if args.verbose and not result:
                logger.info(
                    'Recebendo leituras de um sensor desconhecido: %s', name
                )
