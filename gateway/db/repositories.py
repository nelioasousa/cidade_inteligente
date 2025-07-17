from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sessions import SessionMaker
from models import Sensor, Actuator


def get_sensor_repository():
    return SensorRepository(SessionMaker)


def get_actuator_repository():
    return ActuatorRepository(SessionMaker)


class SensorRepository:
    def __init__(self, session_maker: sessionmaker):
        self.session_maker = session_maker

    def add_sensor(
        self,
        sensor_type: str,
        ip_address: str,
        metadata: dict[str, Any]
    ):
        sensor = self.get_sensor_by_ip_address(ip_address)
        if sensor is None:
            with self.session_maker.begin() as session:
                sensor = Sensor(
                    type=sensor_type,
                    ip_address=ip_address,
                    metadata=metadata,
                )
                session.add(sensor)
        else:
            with self.session_maker.begin() as session:
                sensor = session.merge(sensor)
                sensor.type = sensor_type
                sensor.metadata = metadata
        return sensor

    def get_sensor_by_id(self, sensor_id: int):
        stmt = select(Sensor).where(Sensor.id == sensor_id).limit(1)
        with self.session_maker() as session:
            return session.scalars(stmt).first()

    def get_sensor_by_ip_address(self, ip_address: str):
        stmt = select(Sensor).where(Sensor.ip_address == ip_address).limit(1)
        with self.session_maker() as session:
            return session.scalars(stmt).first()

    def get_all_sensors(self):
        stmt = select(Sensor)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def get_sensors_by_type(self, sensor_type: str):
        stmt = select(Sensor).where(Sensor.type == sensor_type)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def mark_sensor_as_seen(self, sensor_id: int):
        with self.session_maker.begin() as session:
            sensor = session.get(Sensor, sensor_id)
            if sensor is None:
                return False
            sensor.mark_as_seen()
            return True


class ActuatorRepository:
    def __init__(self, session_maker: sessionmaker):
        self.session_maker = session_maker

    def add_actuator(
        self,
        actuator_type: str,
        ip_address: str,
        communication_port: int,
        current_state: dict[str, Any],
        metadata: dict[str, Any]
    ):
        actuator = self.get_actuator_by_address(ip_address, communication_port)
        if actuator is None:
            with self.session_maker.begin() as session:
                actuator = Actuator(
                    type=actuator_type,
                    ip_address=ip_address,
                    communication_port=communication_port,
                    current_state=current_state,
                    metadata=metadata,
                )
                session.add(actuator)
        else:
            with self.session_maker.begin() as session:
                actuator = session.merge(actuator)
                actuator.type = actuator_type
                actuator.current_state = current_state
                actuator.metadata = metadata
        return actuator

    def get_actuator_by_id(self, actuator_id: int):
        stmt = select(Actuator).where(Actuator.id == actuator_id).limit(1)
        with self.session_maker() as session:
            return session.scalars(stmt).first()

    def get_actuator_by_address(self, ip_address: str, communication_port: int):
        stmt = select(Actuator).where(
            Actuator.ip_address == ip_address,
            Actuator.communication_port == communication_port,
        ).limit(1)
        with self.session_maker() as session:
            return session.scalars(stmt).first()

    def get_all_actuators(self):
        stmt = select(Actuator)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def get_actuators_by_type(self, actuator_type: str):
        stmt = select(Actuator).where(Actuator.type == actuator_type)
        with self.session_maker() as session:
            return session.scalars(stmt).all()

    def mark_actuator_as_seen(self, actuator_id: int):
        with self.session_maker.begin() as session:
            actuator = session.get(Actuator, actuator_id)
            if actuator is None:
                return False
            actuator.mark_as_seen()
            return True

    def register_actuator_update(
        self,
        actuator_id: int,
        current_state: dict[str, Any],
        metadata: dict[str, Any],
    ):
        with self.session_maker.begin() as session:
            actuator = session.get(Actuator, actuator_id)
            if actuator is None:
                return False
            actuator.current_state = current_state
            actuator.metadata = metadata
            return True
