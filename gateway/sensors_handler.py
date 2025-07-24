import logging
import datetime
import pika
from db.repositories import get_sensors_repository
from messages_pb2 import SensorReading


def register_reading(body):
    reading = SensorReading()
    reading.ParseFromString(body)
    sensor_category, sensor_id = reading.device_name.split('-')
    sensor_id = int(sensor_id)
    sensors_repository = get_sensors_repository()
    sensors_repository.register_sensor_reading(
        sensor_id=sensor_id,
        sensor_category=sensor_category,
        reading_value=reading.reading_value,
        reading_timestamp=datetime.datetime.fromisoformat(reading.timestamp),
    )


def sensors_consumer(stop_flag, broker_ip, broker_port, publish_exchange):
    logger = logging.getLogger('SENSORS_CONSUMER')
    def callback(ch, method, properties, body):
        logger.debug('Processando nova mensagem do Broker')
        try:
            register_reading(body)
        except Exception:
            logger.error('Falha ao processar mensagem')
        if stop_flag.is_set():
            logger.info('Parando consumo de mensagens...')
            ch.stop_consuming()
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=broker_ip,
            port=broker_port,
            socket_timeout=1.0,
        )
    )
    channel = connection.channel()
    try:
        channel.exchange_declare(
            exchange=publish_exchange,
            exchange_type='fanout',
        )
        result = channel.queue_declare(queue='', exclusive=True)
        exclusive_queue = result.method.queue
        channel.queue_bind(exchange=publish_exchange, queue=exclusive_queue)
        channel.basic_consume(
            queue=exclusive_queue,
            on_message_callback=callback,
            auto_ack=True,
        )
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()
