import socket
import logging
import datetime
import pika
from db.repositories import get_sensors_repository
from messages_pb2 import SensorReading


def register_reading(body):
    print(type(body))


def sensors_consumer(stop_flag, message_broker_ip, message_broker_port):
    def callback(ch, method, properties, body):
        if stop_flag.is_set():
            ch.stop_consuming()
            return
        return register_reading(body)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=message_broker_ip,
            port=message_broker_port,
            socket_timeout=1.0,
        )
    )
    channel = connection.channel()
    try:
        channel.exchange_declare(exchange='readings', exchange_type='fanout')
        result = channel.queue_declare(queue='', exclusive=True)
        exclusive_queue = result.method.queue
        channel.queue_bind(exchange='readings', queue=exclusive_queue)
        channel.basic_consume(
            queue=exclusive_queue,
            on_message_callback=callback,
            auto_ack=True,
        )
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()


def sensors_listener(stop_flag, sensors_port):
    sensors_repository = get_sensors_repository()
    logger = logging.getLogger('SENSORS_LISTENER')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', sensors_port))
        logger.info(
            'Escutando por dados sensoriais na porta %d',
            sensors_port,
        )
        sock.settimeout(1.0)
        while not stop_flag.is_set():
            try:
                msg, addrs = sock.recvfrom(1024)
            except TimeoutError:
                continue
            reading = SensorReading()
            reading.ParseFromString(msg)
            sensor_category, sensor_id = reading.device_name.split('-')
            sensor_id = int(sensor_id)
            sensor = sensors_repository.get_sensor(sensor_id, sensor_category)
            if sensor is None:
                logger.warning(
                    'Recebendo leituras de um sensor '
                    'não registrado localizado em %s',
                    addrs[0],
                )
                continue
            logger.debug(
                'Leitura de sensor recebida: (%s, %s, %.6f)',
                reading.timestamp,
                reading.device_name,
                reading.reading_value,
            )
            timestamp = datetime.datetime.fromisoformat(reading.timestamp)
            sensors_repository.register_sensor_reading(
                sensor.id, sensor.category, reading.reading_value, timestamp,
            )
