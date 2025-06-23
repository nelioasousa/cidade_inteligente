import os
import time
import json
import datetime


def default_parser(obj):
    try:
        return obj.isoformat()
    except ArithmeticError:
        return str(obj)


class Database:

    def __init__(self, clean=False, db_file='db.json'):
        self.db_file = db_file
        if clean:
            self.db = {}
        else:
            if os.path.isfile(db_file):
                with open(db_file, mode='r') as f:
                    self.db = json.load(f)
                for device in self.db:
                    self.db[device]['address'] = tuple(self.db[device]['address'])
                    self.db[device]['data'] = [
                        (datetime.datetime.fromisoformat(ts), vl)
                        for ts, vl in self.db[device]['data']
                    ]
            else:
                self.db = {}
    
    def register_decive(self, name, address, state_json, metadata_json):
        device = self.db.setdefault(name, {'name': name})
        device['address'] = address
        device['state'] = state_json
        device['metadata'] = metadata_json
        device['last_seen'] = time.monotonic()
        device['online'] = True
        device.setdefault('data', [])
    
    def unregister_device(self, name):
        return self.db.pop(name, {})
    
    def persist(self):
        with open(self.db_file, mode='w') as db:
            json.dump(self.db, db, default=default_parser)
    
    def get_device(self, name):
        try:
            return self.db[name]
        except KeyError:
            return None
    
    def get_device_data(self, name):
        try:
            return self.db[name]['data']
        except KeyError:
            return None
    
    def insert_data_item(self, name, data_item, sork_key=None):
        device = self.db[name]
        device['data'].append(data_item)
        device['last_seen'] = time.monotonic()
        device['online'] = True
        if sork_key is not None:
            device['data'].sort(key=sork_key)
    
    def has_data(self):
        return bool(self.db)
    
    def is_device_registered(self, name):
        return name in self.db
