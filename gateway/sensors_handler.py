import socket
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
    print(type(body))


def sensors_consumer(stop_flag, broker_ip, broker_port):
    def callback(ch, method, properties, body):
        if stop_flag.is_set():
            ch.stop_consuming()
        return register_reading(body)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=broker_ip,
            port=broker_port,
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
