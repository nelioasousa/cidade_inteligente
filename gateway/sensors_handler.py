import json
import time
import socket
import logging
from datetime import date, datetime
from messages_pb2 import SensorReading, SensorsReport


def sensors_report_generator(args):
    logger = logging.getLogger('SENSORS_REPORT_GENERATOR')
    logger.info('Iniciando o gerador de relatórios dos sensores')
    while not args.stop_flag.is_set():
        with args.db_sensors_lock:
            sensors = args.db.get_sensors_summary()
        today = date.today()
        now_clock = time.monotonic()
        tolerance = args.sensors_tolerance
        for i, sensor_summary in enumerate(sensors):
            last_seen = sensor_summary['last_seen']
            is_online = (
                last_seen[0] == today
                and (now_clock - last_seen[1]) <= tolerance
            )
            sensors[i] = SensorReading(
                device_name=sensor_summary['device_name'],
                reading_value=sensor_summary['reading_value'],
                timestamp=sensor_summary['timestamp'].isoformat(),
                metadata=json.dumps(sensor_summary['metadata']),
                is_online=is_online,
            )
        logger.debug(
            'Novo relatório gerado: %d sensores reportados',
            len(sensors),
        )
        report = SensorsReport(devices=sensors).SerializeToString()
        with args.db_sensors_report_lock:
            args.db.sensors_report = report
        time.sleep(args.reports_gen_interval)


def sensors_listener(args):
    logger = logging.getLogger('SENSORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', args.sensors_port))
        except Exception as e:
            logger.error(
                'Erro ao tentar vínculo com a porta %s: (%s) %s',
                args.sensors_port,
                type(e).__name__,
                e,
            )
            raise e
        logger.info(
            'Escutando por dados sensoriais na porta %s',
            args.sensors_port,
        )
        sock.settimeout(args.base_timeout)
        while not args.stop_flag.is_set():
            try:
                msg, addrs = sock.recvfrom(1024)
            except TimeoutError:
                continue
            with args.db_sensors_lock:
                sensor_name = args.db.get_sensor_name_by_ip(addrs[0])
            if sensor_name is None:
                logger.warning(
                    'Recebendo leituras de um sensor '
                    'não registrado localizado em %s',
                    addrs[0],
                )
                continue
            reading = SensorReading()
            reading.ParseFromString(msg)
            logger.debug(
                'Leitura de sensor recebida: (%s, %s, %.6f)',
                reading.timestamp,
                reading.device_name,
                reading.reading_value,
            )
            metadata = json.loads(reading.metadata)
            timestamp = datetime.fromisoformat(reading.timestamp)
            with args.db_sensors_lock:
                args.db.add_sensor_reading(
                    reading.device_name,
                    reading.reading_value,
                    metadata,
                    timestamp,
                )
