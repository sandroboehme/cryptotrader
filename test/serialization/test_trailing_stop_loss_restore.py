import json
import os
import unittest
from unittest import mock

import datetime as dt

import backtrader as bt
import ccxt

import livetrading
from cryptotrader.persistence.persistence import Persistence
from cryptotrader.persistence.persistence_factory import PersistenceFactory
from cryptotrader.persistence.persistence_type import PersistenceType

from definitions import ROOT_PATH


class TestTrailingStopLossRestore(unittest.TestCase):

    def setUp(self):
        self.param_file_path_prefix = 'test/serialization/'
        self.test_folder_prefix = os.path.join(ROOT_PATH, 'test/serialization/')

    def test_previousPsarStopLoss_fs(self):
        self.previousPsarStopLossUsed_test(PersistenceType.FS, PersistenceType.FS)

    def test_previousPsarStopLossUsed_gcloud_storage(self):
        self.previousPsarStopLossUsed_test(PersistenceType.GOOGLE_CLOUD_STORAGE, PersistenceType.GOOGLE_FIRESTORE)

    def previousPsarStopLossUsed_test(self, persistence_type, trade_setup_persistence_type):
        trade_setup_path = Persistence.get_path('binance', 'bnb/usdt')
        setup_name = 'backtestBNBPsarSL'
        trade_setup_persistence = PersistenceFactory.get_persistance(trade_setup_persistence_type,
                                                                     trade_setup_path,
                                                                     name=setup_name,
                                                                     root_path=ROOT_PATH)

        iteration = 0
        call_count = 0
        last_iteration = 0
        last_stop_price = None

        with open(self.test_folder_prefix + 'ccxt_order_result/limit/limit_buy.json', 'r') as f:
            buy_order_result = json.load(f)

        with open(self.test_folder_prefix + 'ccxt_order_result/limit/limit_buy_fetch_order.json', 'r') as f:
            limit_buy_fetch_order_result = json.load(f)

        with open(self.test_folder_prefix + 'ccxt_order_result/limit/limit_buy_fetch_order_filled.json', 'r') as f:
            limit_buy_fetch_order_filled_result = json.load(f)

        with open(self.test_folder_prefix + 'ccxt_order_result/stop_limit/sl_fetch_order.json', 'r') as f:
            stop_limit_sell_fetch_order_result = json.load(f)

        with open(self.test_folder_prefix + 'ccxt_order_result/stop_limit/sl_fill_order.json', 'r') as f:
            stop_limit_sell_fill_order_result = json.load(f)

        with open(self.test_folder_prefix + 'ccxt_order_result/cancel.json', 'r') as f:
            cancel_order_result = json.load(f)

        def binance_create_order(*args, **kwargs):
            nonlocal last_stop_price
            # return initially the buy order and later the stop-limit-sell order
            if kwargs['type'] == 'limit' and kwargs['side'] == 'buy':
                return buy_order_result
            if kwargs['type'] == 'STOP_LOSS_LIMIT' and kwargs['side'] == 'sell':
                last_stop_price = kwargs['price']
                stop_limit_sell_fetch_order_result['price'] = last_stop_price
                return stop_limit_sell_fetch_order_result
            return None

        def binance_fetch_order(*args, **kwargs):
            nonlocal iteration
            nonlocal call_count
            nonlocal last_iteration
            nonlocal last_stop_price
            # call_count is 1-based
            call_count = (call_count + 1) if last_iteration == iteration else 1
            # 1. fetch_order in deserialize() (except on 0'th iteration where there is no deserialization)
            # 2. fetch_order is from before next()
            last_iteration = iteration
            print(iteration)
            order_id = args[0]
            if iteration == 8 and order_id == '87813927' and call_count >= 2:
                return limit_buy_fetch_order_filled_result
            if 8 <= iteration < 20 and order_id == '97799440':
                # call_count == 5 ?
                stop_limit_sell_fetch_order_result['price'] = last_stop_price
                return stop_limit_sell_fetch_order_result
            if iteration == 20 and order_id == '97799440':
                stop_limit_sell_fill_order_result['price'] = last_stop_price
                return stop_limit_sell_fill_order_result
            return limit_buy_fetch_order_result

        def binance_cancel_order(*args, **kwargs):
            order_id = args[0]
            if iteration >= 8 and order_id == '97799440':
                return cancel_order_result
            return None

        abs_param_file = os.path.join(ROOT_PATH, 'test/backtestBNBPsarSL.json')

        cs_persistence = self.initialize_test_data(abs_param_file, persistence_type, trade_setup_persistence)

        with mock.patch.object(ccxt.binance, 'cancel_order', side_effect=binance_cancel_order):
            with mock.patch.object(ccxt.binance, 'create_order', side_effect=binance_create_order):
                with mock.patch.object(ccxt.binance, 'fetch_order', side_effect=binance_fetch_order):
                    finished = False
                    iteration_index = 0
                    while not finished:
                        last_iteration = iteration
                        iteration = iteration_index

                        livetrading.main(trade_setup_path, setup_name, trade_setup_persistence_type)

                        trade_setup = self.set_fromdate_for_iteration(trade_setup_persistence)
                        finished = trade_setup.get('event_stop')

                        assert iteration <= 21
                        candle_state, path = cs_persistence.get_last_candle_state()
                        if iteration == 0:
                            assert candle_state.get('ohlc') == {
                                "open": 6.7299,
                                "high": 6.7299,
                                "low": 6.681,
                                "close": 6.681,
                                "volume": 35286.44
                            }, 'The testing environment didn\'t return the correct ohlc value.'
                            assert candle_state.get('time') == '2019-01-28T04:15:00'
                            assert candle_state.get('psar') == 6.907896
                            assert candle_state.get('buy_order') is not None
                            assert candle_state.get('sar') is not None
                            assert candle_state.get('sell_order') is None
                        elif iteration == 1:
                            assert candle_state.get('ohlc') == {
                                "open": 6.6872,
                                "high": 6.6872,
                                "low": 6.665,
                                "close": 6.6703,
                                "volume": 29960.3
                            }, 'The testing environment didn\'t return the correct ohlc value.'
                            assert candle_state.get('time') == '2019-01-28T04:30:00'
                            assert candle_state.get('psar') == 6.8814853056
                            assert candle_state.get('buy_order') is not None
                            assert candle_state.get('sar') is not None
                            assert candle_state.get('sell_order') is None
                        elif iteration == 7:
                            assert candle_state.get('ohlc') == {
                                "open": 6.5028,
                                "high": 6.5184,
                                "low": 6.3723,
                                "close": 6.4399,
                                "volume": 138693.53
                            }, 'The testing environment didn\'t return the correct ohlc value.'
                            assert candle_state.get('time') == '2019-01-28T06:00:00'
                            assert candle_state.get('psar') == 6.63879136
                            assert candle_state.get('buy_order') is not None
                            assert candle_state.get('sar') is not None
                            assert candle_state.get('sell_order') is None
                        elif iteration == 8:
                            assert candle_state.get('ohlc') == {
                                "open": 6.4399,
                                "high": 6.5562,
                                "low": 6.426,
                                "close": 6.5147,
                                "volume": 49548.23
                            }, 'The testing environment didn\'t return the correct ohlc value.'
                            assert candle_state.get('time') == '2019-01-28T06:15:00'
                            assert candle_state.get('psar') == 6.5787
                            assert candle_state.get('buy_order') is not None
                            assert candle_state.get('sar') is not None
                            so = candle_state.get('sell_order')
                            assert so is not None
                            assert so["symbol"] == 'BNB/USDT'
                            assert so["type"] == 'stop_loss_limit'
                            assert so["side"] == 'sell'
                            assert so["price"] == 6.3100000000000005
                            assert so["amount"] == 10.0
                        elif iteration == 19:
                            assert candle_state.get('ohlc') == {
                                "open": 6.6506,
                                "high": 6.6509,
                                "low": 6.6244,
                                "close": 6.6456,
                                "volume": 16550.96
                            }, 'The testing environment didn\'t return the correct ohlc value.'
                            assert candle_state.get('time') == '2019-01-28T09:00:00'
                            assert candle_state.get('psar') == 6.77766888
                            assert candle_state.get('buy_order') is not None
                            assert candle_state.get('sar') is not None
                            so = candle_state.get('sell_order')
                            assert so is not None
                            assert so["symbol"] == 'BNB/USDT'
                            assert so["type"] == 'stop_loss_limit'
                            assert so["side"] == 'sell'
                            assert so["price"] == 6.680456
                            assert so["amount"] == 10.0

                        iteration_index += 1

    def set_fromdate_for_iteration(self, trade_setup_persistence):
        trade_setup = trade_setup_persistence.get_setup()
        fromdate = dt.datetime(
            trade_setup['fromdate']['year'],
            trade_setup['fromdate']['month'],
            trade_setup['fromdate']['day'],
            trade_setup['fromdate']['hour'],
            trade_setup['fromdate']['minute'])
        # This moves the fromdate forward depending on the timeframe
        # e.g. for the 15min timeframes: {'minutes': 15}
        fromdate = fromdate + bt.datetime.timedelta(**{
            trade_setup['timeframe']: trade_setup['compression']
        })
        ts_from = {}
        ts_from['year'] = fromdate.year
        ts_from['month'] = fromdate.month
        ts_from['day'] = fromdate.day
        ts_from['hour'] = fromdate.hour
        ts_from['minute'] = fromdate.minute
        trade_setup_persistence.update_setup({'fromdate': ts_from})
        return trade_setup_persistence.get_setup()

    def initialize_test_data(self, abs_param_file, persistence_type, trade_setup_persistence):
        with open(abs_param_file, 'r') as f:
            prev_data = json.load(f)

        trade_parameter = dict(exchange=prev_data['exchange'],
                               pair=prev_data['symbol'],
                               year=prev_data['fromdate']['year'],
                               month=prev_data['fromdate']['month'],
                               day=prev_data['fromdate']['day'],
                               trade_id=prev_data['name'])
        cs_persistence = PersistenceFactory.get_cs_persistance(persistence_type,
                                                               **trade_parameter,
                                                               root_path=ROOT_PATH)
        cs_persistence.delete_trade_folder()

        trade_setup_persistence.delete_setup()
        prev_data['event_stop'] = False
        prev_data['candle_state_persistence_type'] = persistence_type.value


        # trade_setup_persistence.update_setup({'candle_state_persistence_type': persistence_type.value})
        trade_setup_persistence.save_setup(prev_data)

        return cs_persistence


if __name__ == '__main__':
    unittest.main()
