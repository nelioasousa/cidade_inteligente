import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from .sessions import SessionMaker
from .models import Sensor, Actuator, Reading


def get_sensors_repository():
    return SensorRepository(SessionMaker)


def get_actuators_repository():
    return ActuatorRepository(SessionMaker)


class SensorRepository:
    def __init__(self, session_maker: sessionmaker):
        self.session_maker = session_maker

    def add_sensor(
        self,
        sensor_id: int,
        sensor_category: str,
        ip_address: str,
        device_metadata: dict[str, Any],
        availability_tolerance: float = 10.0,
    ):
        sensor = self.get_sensor(sensor_id, sensor_category)
        if sensor is None:
            with self.session_maker.begin() as session:
                sensor = Sensor(
                    id=sensor_id,
                    category=sensor_category,
                    ip_address=ip_address,
                    device_metadata=device_metadata,
                    availability_tolerance=availability_tolerance,
                )
                session.add(sensor)
        else:
            with self.session_maker.begin() as session:
                sensor = session.merge(sensor)
                sensor.ip_address = ip_address
                sensor.device_metadata = device_metadata
                sensor.availability_tolerance = availability_tolerance
                sensor.mark_as_seen()
        return sensor

    def get_sensor(self, sensor_id: int, sensor_category: str):
        with self.session_maker() as session:
            return session.get(Sensor, (sensor_id, sensor_category))

    def get_sensor_readings(self, sensor_id: int, sensor_category: str):
        with self.session_maker() as session:
            sensor = session.get(Sensor, (sensor_id, sensor_category))
            if sensor is None:
                return None
            readings = sensor.readings
        readings.sort(key=(lambda x: x.timestamp))
        return readings

    def get_sensor_last_reading(self, sensor_id: int, sensor_category: str):
        stmt = select(Reading).where(
            Reading.sensor_id == sensor_id,
            Reading.sensor_category == sensor_category,
        ).order_by(Reading.timestamp.desc()).limit(1)
        with self.session_maker() as session:
            return session.scalars(stmt).first()

    def get_all_sensors(self):
        stmt = select(Sensor)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def get_sensors_by_category(self, sensor_category: str):
        stmt = select(Sensor).where(Sensor.category == sensor_category)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def mark_sensor_as_seen(self, sensor_id: int, sensor_category: str):
        with self.session_maker.begin() as session:
            sensor = session.get(Sensor, (sensor_id, sensor_category))
            if sensor is None:
                return False
            sensor.mark_as_seen()
            return True

    def register_sensor_reading(
        self,
        sensor_id: int,
        sensor_category: str,
        reading_value: float,
        reading_timestamp: datetime.datetime,
    ):
        sensor = self.get_sensor(sensor_id, sensor_category)
        if sensor is None:
            return False
        with self.session_maker.begin() as session:
            sensor = session.merge(sensor)
            reading = Reading(
                value=reading_value,
                timestamp=reading_timestamp,
                sensor_id=sensor_id,
                sensor_category=sensor_category,
            )
            session.add(reading)
            sensor.mark_as_seen()
            return True


class ActuatorRepository:
    def __init__(self, session_maker: sessionmaker):
        self.session_maker = session_maker

    def add_actuator(
        self,
        actuator_id: int,
        actuator_category: str,
        ip_address: str,
        communication_port: int,
        device_state: dict[str, Any],
        device_metadata: dict[str, Any],
        timestamp: datetime.datetime,
        availability_tolerance: float = 10.0,
    ):
        actuator = self.get_actuator(actuator_id, actuator_category)
        if actuator is None:
            with self.session_maker.begin() as session:
                actuator = Actuator(
                    id=actuator_id,
                    category=actuator_category,
                    ip_address=ip_address,
                    communication_port=communication_port,
                    device_state=device_state,
                    device_metadata=device_metadata,
                    timestamp=timestamp,
                    availability_tolerance=availability_tolerance,
                )
                session.add(actuator)
        else:
            with self.session_maker.begin() as session:
                actuator = session.merge(actuator)
                actuator.ip_address = ip_address
                actuator.communication_port = communication_port
                actuator.device_state = device_state
                actuator.device_metadata = device_metadata
                actuator.timestamp = timestamp
                actuator.availability_tolerance = availability_tolerance
        return actuator

    def get_actuator(self, actuator_id: int, actuator_category: str):
        with self.session_maker() as session:
            return session.get(Actuator, (actuator_id, actuator_category))

    # def get_actuator_by_address(self, ip_address: str, communication_port: int):
    #     stmt = select(Actuator).where(
    #         Actuator.ip_address == ip_address,
    #         Actuator.communication_port == communication_port,
    #     ).limit(1)
    #     with self.session_maker() as session:
    #         return session.scalars(stmt).first()

    def get_all_actuators(self):
        stmt = select(Actuator)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def get_actuators_by_category(self, actuator_category: str):
        stmt = select(Actuator).where(Actuator.category == actuator_category)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def mark_actuator_as_seen(self, actuator_id: int, actuator_category: str):
        with self.session_maker.begin() as session:
            actuator = session.get(Actuator, (actuator_id, actuator_category))
            if actuator is None:
                return False
            actuator.mark_as_seen()
            return True

    def register_actuator_update(
        self,
        actuator_id: int,
        actuator_category: str,
        device_state: dict[str, Any],
        device_metadata: dict[str, Any],
        timestamp: datetime.datetime,
    ):
        with self.session_maker.begin() as session:
            actuator = session.get(Actuator, (actuator_id, actuator_category))
            if actuator is None:
                return False
            if timestamp > actuator.timestamp:
                actuator.device_state = device_state
                actuator.device_metadata = device_metadata
                actuator.timestamp = timestamp
                actuator.mark_as_seen()
            return True
