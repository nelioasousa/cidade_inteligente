import time
import datetime
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import Integer, Float, String
from sqlalchemy import Date, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


def get_utc_date():
    return datetime.datetime.now(datetime.UTC).date()


class Sensor(Base):
    __tablename__ = 'sensors'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    device_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)

    last_seen_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default=get_utc_date,
    )
    last_seen_clock: Mapped[float] = mapped_column(
        Float, nullable=False, default=time.monotonic,
    )

    readings: Mapped[list['Reading']] = relationship(back_populates='sensor')

    def mark_as_seen(self):
        self.last_seen_date = get_utc_date()
        self.last_seen_clock = time.monotonic()
        return


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

    sensor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sensor_category: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            columns=['sensor_id', 'sensor_category'],
            refcolumns=['sensors.id', 'sensors.category']
        ),
    )

    sensor: Mapped['Sensor'] = relationship(back_populates='readings')


class Actuator(Base):
    __tablename__ = 'actuators'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    communication_port: Mapped[int] = mapped_column(Integer, nullable=False)
    device_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    device_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(UTCDateTime, nullable=False)

    last_seen_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default=get_utc_date,
    )
    last_seen_clock: Mapped[float] = mapped_column(
        Float, nullable=False, default=time.monotonic,
    )

    def mark_as_seen(self):
        self.last_seen_date = get_utc_date()
        self.last_seen_clock = time.monotonic()
        return
