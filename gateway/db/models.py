import datetime
from sqlalchemy import Integer, Float, String, JSON, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class Sensor(Base):
    __tablename__ = 'sensors'

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_type: Mapped[str] = mapped_column(String(40), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False)

    readings: Mapped[list['Reading']] = relationship(back_populates='sensor')


class UTCDateTime(TypeDecorator):

    impl = DateTime

    def process_bind_param(self, value, dialect):
        return value.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=datetime.UTC)


class Reading(Base):
    __tablename__ = 'sensors_readings'

    timestamp: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    sensor: Mapped['Sensor'] = relationship(back_populates='readings')


class Actuator(Base):
    __tablename__ = 'actuators'

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_type: Mapped[str] = mapped_column(String(40), nullable=False)
    current_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_update: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)
