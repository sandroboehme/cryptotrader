import json
from backtrader import Order, Strategy

from cryptotrader.persistence.persistence_type import PersistenceType


class RestorableStrategy(Strategy):
    activated = True

    params = (
        ('candle_state_persistence_type', None),
        ('state_iteration_index', None),
        ('cs_persistence', None),
        ('abs_param_file', None),
    )

    def __init__(self):
        self.cs_persistence = PersistenceType(self.params.candle_state_persistence_type)
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
                    self.load_candle_state()
        except AttributeError:
            pass

    def load_candle_state(self):
        last_candle_state = self.params.cs_persistence.get_last_candle_state()[0]

        self.deserialize_json(last_candle_state)

    def serialize(self):
        self.store_candle_state()

    def store_candle_state(self):
        candle_state = self.serialize_json()
        self.params.cs_persistence.save_candle_state(candle_state)

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
