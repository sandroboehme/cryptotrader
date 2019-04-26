import json
import os
import tempfile
import time
from abc import abstractmethod

from backtrader import Order, Strategy
from ccxt import InvalidOrder
from google.cloud import storage

from cryptotrader.serialization.serializable import JsonSerializable
from definitions import ROOT_PATH


class RestorableStrategy(Strategy):
    activated = True

    params = (
        ('state_folder_path', None),
        ('state_iteration_index', None),
        ('abs_param_file', None),
    )

    def __init__(self):
        self.live_next_run_already = False
        if self.activated and self.params.state_iteration_index > 0:
            self.setminperiod(0)
        self.data_status4trading = None

    def end_trade(self):
        with open(self.params.abs_param_file, 'r') as f:
            prev_data = json.load(f)
        prev_data['event_stop'] = True
        with open(self.params.abs_param_file, 'w') as outfile:
            json.dump(prev_data, outfile, indent=4)
        self.serialize()

    def deserialize(self):
        try:
            if self.activated \
                    and self.params.state_iteration_index > 0:
                if self.data_status4trading == 'LIVE':
                    previous_state_index = self.params.state_iteration_index - 1
                    self.load_candle_state(previous_state_index)
        except AttributeError:
            pass

    def load_candle_state(self, previous_state_index):
        json_file4loading = self.params.state_folder_path + str(previous_state_index) + '.json'
        print('deserializing state ' + str(previous_state_index) + ' from ' + json_file4loading)
        with open(json_file4loading, 'r') as f:
            self.deserialize_json(json.load(f))

    def serialize(self):
        self.store_candle_state(self.params.state_iteration_index)

    def store_candle_state(self, state_iteration_index):
        json_file4save = self.params.state_folder_path + str(self.params.state_iteration_index) + '.json'
        with open(json_file4save, 'w') as outfile:
            print('serializing to ' + json_file4save)
            serialized_json = self.serialize_json()
            json.dump(serialized_json, outfile, indent=4)
            print('tfile: ' + outfile.name)

    def next(self, dt=None):
        if self.activated and self.live_next_run_already:
            self.serialize()
            self.env.runstop()
        else:
            self.restorable_next(dt)
        if self.activated and self.data_status4trading == 'LIVE':
            self.live_next_run_already = True

    def notify_data(self, data, status, *args, **kwargs):
        self.log('Data: {}, Data Status: {}, Order Status: {}'.format(data, data._getstatusname(status), status))
        self.data_status4trading = data._getstatusname(status)
        if self.activated and self.data_status4trading == 'LIVE':
            self.deserialize()
