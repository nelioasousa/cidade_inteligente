import os
import time
import pickle
import json
from sortedcontainers import SortedList


def sensors_key(data_item):
    return data_item[0]


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
        device['last_seen'] = time.monotonic()
        device.setdefault('data', SortedList(key=sensors_key))
    
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
    
    def add_sensor_reading(self, name, value, timestamp, metadata_string):
        sensor = self.db[0][name]
        sensor['data'].add((timestamp, value))
        if sensor['data'][-1][0] == timestamp:
            sensor['metadata'] = json.loads(metadata_string)
        sensor['last_seen'] = time.monotonic()
    
    def count_sensor_readings(self, name):
        return len(self.db[0][name]['data'])

    def sensors_count(self):
        return len(self.db[0])
    
    def is_sensor_registered(self, name):
        return name in self.db[0]

    def get_sensors_readings(self):
        result = []
        for sensor, data in self.db[0].items():
            result.append({
                'sensor_name': sensor,
                'reading_value': data['data'][-1][1],
                'timestamp': data['data'][-1][0],
                'metadata': data['metadata'],
            })
        return result
