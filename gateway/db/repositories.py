from contextlib import contextmanager
from sqlalchemy import select, update, insert
from sqlalchemy.orm import Session
from sessions import get_session
from models import Sensor, Actuator


@contextmanager
def get_sensor_repository():
    session = get_session()
    try:
        yield SensorRepository(session)
    finally:
        session.close()


@contextmanager
def get_actuator_repository():
    session = get_session()
    try:
        yield ActuatorRepository(session)
    finally:
        session.close()


class SensorRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_sensor(self, sensor_id: int, sensor_type: str, metadata: dict):
        sensor = self.get_sensor(sensor_id, sensor_type)
        if sensor is None:
            stmt = insert(Sensor).values(
                device_id=sensor_id,
                device_type=sensor_type,
                metadata=metadata,
            )
        else:
            stmt = update(Sensor).where(
                Sensor.device_id == sensor_id,
                Sensor.device_type == sensor_type,
            ).values(metadata=metadata)
        with self.session.begin():
            self.session.execute(stmt)
        return self.get_sensor(sensor_id, sensor_type)

    def get_sensor(self, sensor_id: int, sensor_type: str):
        stmt = select(Sensor).where(
            Sensor.device_id == sensor_id,
            Sensor.device_type == sensor_type,
        )
        return self.session.scalars(stmt).first()

    def get_all_sensors(self):
        return self.session.scalars(select(Sensor)).all()

    def get_sensors_by_type(self, sensor_type: str):
        stmt = select(Sensor).where(Sensor.device_type == sensor_type)
        return self.session.scalars(stmt).all()


class ActuatorRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_actuator(
        self,
        actuator_id: int,
        actuator_type: str,
        current_state: dict,
        metadata: dict
    ):
        actuator = self.get_actuator(actuator_id, actuator_type)
        if actuator is None:
            stmt = insert(Actuator).values(
                device_id=actuator_id,
                device_type=actuator_type,
                current_state=current_state,
                metadata=metadata,
            )
        else:
            stmt = update(Actuator).where(
                Actuator.device_id == actuator_id,
                Actuator.device_type == actuator_type,
            ).values(current_state=current_state, metadata=metadata)
        with self.session.begin():
            self.session.execute(stmt)
        return self.get_actuator(actuator_id, actuator_type)

    def get_actuator(self, actuator_id: int, actuator_type: str):
        stmt = select(Actuator).where(
            Actuator.device_id == actuator_id,
            Actuator.device_type == actuator_type,
        )
        return self.session.scalars(stmt).first()

    def get_all_actuators(self):
        return self.session.scalars(select(Actuator)).all()

    def get_actuators_by_type(self, actuator_type: str):
        stmt = select(Actuator).where(Actuator.device_type == actuator_type)
        return self.session.scalars(stmt).all()
