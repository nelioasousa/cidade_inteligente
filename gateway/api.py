import json
from types import SimpleNamespace
from flask import Flask, request
from flask_restful import Api, Resource, abort
from actuators_handler import send_actuator_command
from db.repositories import get_sensors_repository, get_actuators_repository
from messages_pb2 import CommandType, ComplyStatus


app = Flask(__name__)
api = Api(app)


sensors_repository = get_sensors_repository()
actuators_repository = get_actuators_repository()


class Sensors(Resource):

    def get(self):
        sensors = sensors_repository.get_all_sensors()
        response = []
        for sensor in sensors:
            last_reading = sensors_repository.get_sensor_last_reading(
                sensor.id,
                sensor.category,
            )
            response.append({
                'deviceId': sensor.id,
                'deviceCategory': sensor.category,
                'isOnline': sensor.is_online(),
                'lastReading': dict() if last_reading is None else {
                    'timestamp': last_reading.timestamp.isoformat(),
                    'value': last_reading.value,
                },
                'metadata': sensor.device_metadata,
            })
        return response


class SensorsByCategory(Resource):

    def get(self, sensors_category: str):
        sensors = sensors_repository.get_sensors_by_category(sensors_category)
        response = []
        for sensor in sensors:
            last_reading = sensors_repository.get_sensor_last_reading(
                sensor.id,
                sensor.category,
            )
            response.append({
                'deviceId': sensor.id,
                'deviceCategory': sensor.category,
                'isOnline': sensor.is_online(),
                'lastReading': dict() if last_reading is None else {
                    'timestamp': last_reading.timestamp.isoformat(),
                    'value': last_reading.value,
                },
                'metadata': sensor.device_metadata,
            })
        return response


class Sensor(Resource):

    def get(self, sensor_category: str, sensor_id: int):
        sensor = sensors_repository.get_sensor(sensor_id, sensor_category)
        if sensor is None:
            abort(404, message=f'Sensor {sensor_category}-{sensor_id} not found')
        readings = [
            {
                'timestamp': reading.timestamp.isoformat(),
                'value': reading.value,
            }
            for reading in sensors_repository.get_sensor_readings(
                sensor.id,
                sensor.category,
            )
        ]
        return {
            'deviceId': sensor.id,
            'deviceCategory': sensor.category,
            'isOnline': sensor.is_online(),
            'readings': readings,
            'lastReading': readings[-1] if readings else {},
            'metadata': sensor.device_metadata,
        }


class Actuators(Resource):

    def get(self):
        return [
            {
                'deviceId': actuator.id,
                'deviceCategory': actuator.category,
                'isOnline': actuator.is_online(),
                'lastUpdate': actuator.timestamp.isoformat(),
                'currentState': actuator.device_state,
                'metadata': actuator.device_metadata,
            }
            for actuator in actuators_repository.get_all_actuators()
        ]


class ActuatorsByCategory(Resource):

    def get(self, actuators_category: str):
        return [
            {
                'deviceId': actuator.id,
                'deviceCategory': actuator.category,
                'isOnline': actuator.is_online(),
                'lastUpdate': actuator.timestamp.isoformat(),
                'currentState': actuator.device_state,
                'metadata': actuator.device_metadata,
            }
            for actuator in actuators_repository.get_actuators_by_category(actuators_category)
        ]


class Actuator(Resource):

    def get(self, actuator_category: str, actuator_id: int):
        actuator = actuators_repository.get_actuator(actuator_id, actuator_category)
        if actuator is None:
            abort(404, message=f'Actuator {actuator_category}-{actuator_id} not found')
        return {
            'deviceId': actuator.id,
            'deviceCategory': actuator.category,
            'isOnline': actuator.is_online(),
            'lastUpdate': actuator.timestamp.isoformat(),
            'currentState': actuator.device_state,
            'metadata': actuator.device_metadata,
        }

    def put(self, actuator_category: str, actuator_id: int):
        data = request.get_json()
        response = send_actuator_command(
            actuator_id=actuator_id,
            actuator_category=actuator_category,
            command_type=CommandType.CT_SET_STATE,
            command_body=json.dumps(data),
        )
        if response is None:
            abort(404, message=f'Actuator {actuator_category}-{actuator_id} not found')
        if response.status is ComplyStatus.CS_INVALID_STATE:
            abort(400, message='Invalid state supplied')
        if response.status is not ComplyStatus.CS_OK:
            abort(500, message='Something went wrong')
        return {"message": "OK"}, 200

    def post(self, actuator_category: str, actuator_id: int):
        data = request.get_json()
        if 'action' not in data:
            abort(400, message='No "action" was specified')
        response = send_actuator_command(
            actuator_id=actuator_id,
            actuator_category=actuator_category,
            command_type=CommandType.CT_ACTION,
            command_body=data['action'],
        )
        if response is None:
            abort(404, message=f'Actuator {actuator_category}-{actuator_id} not found')
        if response.status is ComplyStatus.CS_UNKNOWN_ACTION:
            abort(400, message=f'Unknown action "{data['action']}"')
        if response.status is not ComplyStatus.CS_OK:
            abort(500, message='Something went wrong')
        return {"message": "OK"}, 200


# Sensors
api.add_resource(Sensors, '/sensors')
api.add_resource(SensorsByCategory, '/sensors/<string:sensors_category>')
api.add_resource(Sensor, '/sensors/<string:sensor_category>/<int:sensor_id>')

# Actuators
api.add_resource(Actuators, '/actuators')
api.add_resource(ActuatorsByCategory, '/actuators/<string:actuators_category>')
api.add_resource(Actuator, '/actuators/<string:actuator_category>/<int:actuator_id>')
