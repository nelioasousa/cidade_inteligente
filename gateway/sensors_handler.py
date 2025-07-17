import json
import time
import socket
import logging
import datetime
from db.repositories import get_sensor_repository
from messages_pb2 import SensorReading, SensorsReport


def sensors_report_generator(args):
    sensors_repository = get_sensor_repository()
    logger = logging.getLogger('SENSORS_REPORT_GENERATOR')
    logger.info('Iniciando o gerador de relatórios dos sensores')
    while not args.stop_flag.is_set():
        sensors = sensors_repository.get_all_sensors()
        today = datetime.datetime.now(datetime.UTC).date()
        now_clock = time.monotonic()
        tolerance = args.sensors_tolerance
        summary = []
        for sensor in sensors:
            readings = sensors_repository.get_sensor_readings(sensor.id)
            try:
                last_reading = readings[-1]
            except IndexError:
                continue
            is_online = (
                sensor.last_seen_date == today
                and (now_clock - sensor.last_seen_clock) <= tolerance
            )
            summary.append(SensorReading(
                device_name=f'{sensor.type}-{sensor.id}',
                reading_value=last_reading.value,
                timestamp=last_reading.timestamp.isoformat(),
                metadata=json.dumps(sensor.current_metadata),
                is_online=is_online,
            ))
        logger.debug(
            'Novo relatório gerado: %d sensores reportados',
            len(sensors),
        )
        report = SensorsReport(devices=summary).SerializeToString()
        with args.db_sensors_report_lock:
            args.sensors_report = report
        time.sleep(args.reports_gen_interval)


def sensors_listener(args):
    sensors_repository = get_sensor_repository()
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
            sensor = sensors_repository.get_sensor_by_ip_address(addrs[0])
            if sensor is None:
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
            timestamp = datetime.datetime.fromisoformat(reading.timestamp)
            sensors_repository.register_sensor_reading(
                sensor.ip_address, reading.reading_value, timestamp
            )
