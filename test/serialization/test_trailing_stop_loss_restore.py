import json
import os
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

import datetime as dt

import backtrader as bt
import ccxt

import livetrading
from test.serialization import testing_with_live_exchange
from definitions import ROOT_PATH


class TestTrailingStopLossRestore(unittest.TestCase):

    def setUp(self):
        self.param_file_path_prefix = 'test/serialization/'
        self.test_folder_prefix = os.path.join(ROOT_PATH, 'test/serialization/')

    def test_previousPsarStopLossUsed(self):
        iteration = 0
        call_count = 0
        last_iteration = 0
        last_stop_price = None
        with open(self.test_folder_prefix + 'ccxt_order_result/limit/limit_buy.json', 'r') as f:
            buy_order_result = json.load(f)
            # binance_create_order_mock.return_value = buy_order_result

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

        abs_param_file = os.path.join(ROOT_PATH, 'trade_setups/backtestBNBPsarSL.json')
        self.restart_trade(abs_param_file)

        with mock.patch.object(ccxt.binance, 'cancel_order', side_effect=binance_cancel_order):
            with mock.patch.object(ccxt.binance, 'create_order', side_effect=binance_create_order):
                with mock.patch.object(ccxt.binance, 'fetch_order', side_effect=binance_fetch_order):
                    finished = False
                    iteration_index = 0
                    while not finished:
                        last_iteration = iteration
                        iteration = iteration_index

                        trade_setup = self.set_fromdate_for_iteration(
                            abs_param_file,
                            iteration_index)

                        trade_setup['candle_state']['path'] = os.path.join(os.path.dirname(abs_param_file), 'generated/state/')

                        livetrading.main([trade_setup])

                        with open(abs_param_file, 'r') as f:
                            finished = json.load(f).get('event_stop')

                        assert iteration <= 20
                        abs_candle_state_file = trade_setup['candle_state']['path'] + str(iteration) + '.json'

                        with open(abs_candle_state_file, 'r') as f:
                            trade_state = json.load(f)
                            if iteration == 0:
                                assert trade_state.get('ohlc') == {
                                    "open": 6.7299,
                                    "high": 6.7299,
                                    "low": 6.681,
                                    "close": 6.681,
                                    "volume": 35286.44
                                }, 'The testing environment didn\'t return the correct ohlc value.'
                                assert trade_state.get('time') == '2019-01-28T04:15:00'
                                assert trade_state.get('psar') == 6.907896
                                assert trade_state.get('buy_order') is not None
                                assert trade_state.get('sar') is not None
                                assert trade_state.get('sell_order') is None
                            elif iteration == 1:
                                assert trade_state.get('ohlc') == {
                                    "open": 6.6872,
                                    "high": 6.6872,
                                    "low": 6.665,
                                    "close": 6.6703,
                                    "volume": 29960.3
                                }, 'The testing environment didn\'t return the correct ohlc value.'
                                assert trade_state.get('time') == '2019-01-28T04:30:00'
                                assert trade_state.get('psar') == 6.8814853056
                                assert trade_state.get('buy_order') is not None
                                assert trade_state.get('sar') is not None
                                assert trade_state.get('sell_order') is None
                            elif iteration == 7:
                                assert trade_state.get('ohlc') == {
                                    "open": 6.5028,
                                    "high": 6.5184,
                                    "low": 6.3723,
                                    "close": 6.4399,
                                    "volume": 138693.53
                                }, 'The testing environment didn\'t return the correct ohlc value.'
                                assert trade_state.get('time') == '2019-01-28T06:00:00'
                                assert trade_state.get('psar') == 6.63879136
                                assert trade_state.get('buy_order') is not None
                                assert trade_state.get('sar') is not None
                                assert trade_state.get('sell_order') is None
                            elif iteration == 8:
                                assert trade_state.get('ohlc') == {
                                    "open": 6.4399,
                                    "high": 6.5562,
                                    "low": 6.426,
                                    "close": 6.5147,
                                    "volume": 49548.23
                                }, 'The testing environment didn\'t return the correct ohlc value.'
                                assert trade_state.get('time') == '2019-01-28T06:15:00'
                                assert trade_state.get('psar') == 6.5787
                                assert trade_state.get('buy_order') is not None
                                assert trade_state.get('sar') is not None
                                so = trade_state.get('sell_order')
                                assert so is not None
                                assert so["symbol"] == 'BNB/USDT'
                                assert so["type"] == 'stop_loss_limit'
                                assert so["side"] == 'sell'
                                assert so["price"] == 6.3100000000000005
                                assert so["amount"] == 10.0
                            elif iteration == 19:
                                assert trade_state.get('ohlc') == {
                                    "open": 6.6506,
                                    "high": 6.6509,
                                    "low": 6.6244,
                                    "close": 6.6456,
                                    "volume": 16550.96
                                }, 'The testing environment didn\'t return the correct ohlc value.'
                                assert trade_state.get('time') == '2019-01-28T09:00:00'
                                assert trade_state.get('psar') == 6.77766888
                                assert trade_state.get('buy_order') is not None
                                assert trade_state.get('sar') is not None
                                so = trade_state.get('sell_order')
                                assert so is not None
                                assert so["symbol"] == 'BNB/USDT'
                                assert so["type"] == 'stop_loss_limit'
                                assert so["side"] == 'sell'
                                assert so["price"] == 6.680456
                                assert so["amount"] == 10.0

                        iteration_index += 1

    def set_fromdate_for_iteration(self, abs_param_file, iteration_index):
        with open(abs_param_file, 'r') as f:
            trade_setup = json.load(f)
        fromdate = dt.datetime(
            trade_setup['fromdate']['year'],
            trade_setup['fromdate']['month'],
            trade_setup['fromdate']['day'],
            trade_setup['fromdate']['hour'],
            trade_setup['fromdate']['minute'])
        # This moves the fromdate forward depending on the timeframe and
        # how many iterations have been passed already.
        # e.g. for the 5th iteration of 15min timeframes: {'minutes': 5 * 15}
        fromdate = fromdate + bt.datetime.timedelta(**{
            trade_setup['timeframe']: iteration_index * trade_setup['compression']
        })
        ts_from = trade_setup['fromdate']
        ts_from['year'] = fromdate.year
        ts_from['month'] = fromdate.month
        ts_from['day'] = fromdate.day
        ts_from['hour'] = fromdate.hour
        ts_from['minute'] = fromdate.minute
        return trade_setup

    def restart_trade(self, abs_param_file):
        with open(abs_param_file, 'r') as f:
            prev_data = json.load(f)
        prev_data['event_stop'] = False
        with open(abs_param_file, 'w') as outfile:
            json.dump(prev_data, outfile)


if __name__ == '__main__':
    unittest.main()
