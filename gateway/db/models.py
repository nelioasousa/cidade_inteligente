import time
import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, Float, String
from sqlalchemy import Date, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


def last_seen_date_factory():
    return datetime.datetime.now(datetime.UTC).date()


class Sensor(Base):
    __tablename__ = 'sensors'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False)

    last_seen_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default_factory=last_seen_date_factory,
    )
    last_seen_clock: Mapped[float] = mapped_column(
        Float, nullable=False, default_factory=time.monotonic,
    )

    readings: Mapped[list['Reading']] = relationship(back_populates='sensor')


class UTCDateTime(TypeDecorator):

    impl = DateTime

    def process_bind_param(self, value, dialect):
        return value.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=datetime.UTC)


class Reading(Base):
    __tablename__ = 'sensors_readings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)

    sensor_id: Mapped[int] = mapped_column(ForeignKey('sensors.id'), nullable=False)
    sensor: Mapped['Sensor'] = relationship(back_populates='readings')


class Actuator(Base):
    __tablename__ = 'actuators'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    communication_port: Mapped[int] = mapped_column(Integer, nullable=False)
    current_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)

    last_seen_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default_factory=last_seen_date_factory,
    )
    last_seen_clock: Mapped[float] = mapped_column(
        Float, nullable=False, default_factory=time.monotonic,
    )
