import time
import datetime
from flask import Flask
from flask_restful import Api, Resource
from db.repositories import get_sensors_repository, get_actuators_repository


app = Flask(__name__)
api = Api(app)


sensors_repository = get_sensors_repository()
actuators_repository = get_actuators_repository()


class Sensors(Resource):
    def get(self):
        sensors = sensors_repository.get_all_sensors()
        today = datetime.datetime.now(datetime.UTC).date()
        now_clock = time.monotonic()
        response = []
        for sensor in sensors:
            is_online = (
                sensor.last_seen_date == today
                and (now_clock - sensor.last_seen_clock) <= 6.0
            )
            last_reading = sensors_repository.get_sensor_last_reading(sensor.id, sensor.category)
            response.append({
                'deviceId': sensor.id,
                'deviceCategory': sensor.category,
                'isOnline': is_online,
                'lastReading': dict() if last_reading is None else {
                    'timestamp': last_reading.timestamp.isoformat(),
                    'value': last_reading.value,
                },
                'metadata': sensor.device_metadata,
            })
        return response


api.add_resource(Sensors, '/sensors')
