import json
import socket
import logging
from datetime import datetime
from google.protobuf import message
from messages_pb2 import SensorReading


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
