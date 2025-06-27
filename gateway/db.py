import os
import time
import pickle
import datetime
from sortedcontainers import SortedList


class Database:

    def __init__(self, db_file='db.pickle', clear=False):
        self.db_file = db_file
        if clear and os.path.isfile(self.db_file):
            os.remove(self.db_file)
        if os.path.isfile(self.db_file):
            with open(self.db_file, mode='br') as db:
                self.db = pickle.load(db)
        else:
            self.db = ({}, {})

    def register_sensor(self, name, address, metadata):
        sensor = self.db[0].setdefault(name, {'name': name})
        sensor['address'] = address
        sensor['metadata'] = metadata
        sensor['last_seen'] = (datetime.date.today(), time.monotonic())
        sensor.setdefault('data', SortedList())

    def register_actuator(self, name, address, state, metadata, timestamp):
        actuator = self.db[1].setdefault(name, {'name': name})
        actuator['address'] = address
        actuator['state'] = state
        actuator['metadata'] = metadata
        actuator['timestamp'] = timestamp
        actuator['online'] = True
        actuator['last_seen'] = (datetime.date.today(), time.monotonic())

    def persist(self):
        with open(self.db_file, mode='bw') as db:
            pickle.dump(self.db, db)
    
    def get_sensor(self, name):
        try:
            return self.db[0][name]
        except KeyError:
            return None
    
    def get_actuator(self, name):
        try:
            return self.db[1][name]
        except KeyError:
            return None
    
    def get_actuator_by_address(self, address):
        for actuator in self.db[1].values():
            if actuator['address'] == address:
                return actuator
        return None

    def add_sensor_reading(self, name, value, metadata, timestamp):
        try:
            sensor = self.db[0][name]
        except KeyError:
            return False
        sensor['data'].add((timestamp, value))
        if sensor['data'][-1][0] == timestamp:
            sensor['metadata'] = metadata
            sensor['last_seen'] = (datetime.date.today(), time.monotonic())
        return True
    
    def add_actuator_update(self, name, state, metadata, timestamp):
        try:
            actuator = self.db[1][name]
        except KeyError:
            return False
        actuator['state'] = state
        actuator['metadata'] = metadata
        actuator['timestamp'] = timestamp
        actuator['online'] = True
        actuator['last_seen'] = (datetime.date.today(), time.monotonic())
        return True

    def mark_actuator_as_offline(self, name):
        try:
            self.db[1][name]['online'] = False
            return True
        except KeyError:
            return False

    def get_sensors_summary(self):
        summary = []
        for sensor, sensor_data in self.db[0].items():
            try:
                timestamp, reading_value = sensor_data['data'][-1]
            except IndexError:
                continue
            summary.append({
                'device_name': sensor,
                'reading_value': reading_value,
                'timestamp': timestamp,
                'metadata': sensor_data['metadata'],
                'last_seen': sensor_data['last_seen'],
            })
        return summary
