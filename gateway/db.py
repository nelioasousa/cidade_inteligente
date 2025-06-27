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
        device = self.db[0].setdefault(name, {'name': name})
        device['address'] = address
        device['metadata'] = metadata
        device['last_seen'] = (datetime.date.today(), time.monotonic())
        device.setdefault('data', SortedList())

    def register_actuator(self, name, address, state, metadata):
        device = self.db[1].setdefault(name, {'name': name})
        device['address'] = address
        device['state'] = state
        device['metadata'] = metadata
        device['last_seen'] = (datetime.date.today(), time.monotonic())
        device.setdefault('data', SortedList())

    def persist(self):
        with open(self.db_file, mode='bw') as db:
            pickle.dump(self.db, db)
    
    def get_sensor(self, name):
        try:
            return self.db[0][name]
        except KeyError:
            return None
    
    def get_sensor_data(self, name):
        try:
            return self.db[0][name]['data']
        except KeyError:
            return None
    
    def get_actuator(self, name):
        try:
            return self.db[1][name]
        except KeyError:
            return None
    
    def get_actuator_data(self, name):
        try:
            return self.db[1][name]['data']
        except KeyError:
            return None
    
    def add_sensor_reading(self, name, value, timestamp, metadata):
        try:
            sensor = self.db[0][name]
        except KeyError:
            return False
        sensor['data'].add((timestamp, value))
        if sensor['data'][-1][0] == timestamp:
            sensor['metadata'] = metadata
            sensor['last_seen'] = (datetime.date.today(), time.monotonic())
        return True
    
    def add_actuator_update(self, name, value, timestamp, state, metadata):
        try:
            actuator = self.db[1][name]
        except KeyError:
            return False
        actuator['data'].add((timestamp, value))
        if actuator['data'][-1][0] == timestamp:
            actuator['state'] = state
            actuator['metadata'] = metadata
            actuator['last_seen'] = (datetime.date.today(), time.monotonic())
        return True

    def count_sensor_readings(self, name):
        return len(self.db[0][name]['data'])

    def sensors_count(self):
        return len(self.db[0])
    
    def is_sensor_registered(self, name):
        return name in self.db[0]

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
