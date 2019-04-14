import json
import os
import unittest
from unittest.mock import patch
import time
import datetime as dt

from backtrader import Cerebro, Strategy, TimeFrame
from backtrader.indicators import ParabolicSAR
from ccxtbt import CCXTFeed

# from cryptotrader.indicator.ParabolicSL import ParabolicSL
from cryptotrader.indicator.ParabolicSLv2 import ParabolicSLv2
from definitions import ROOT_PATH

class TestStrategy(Strategy):

    def __init__(self):
        self.psar = ParabolicSLv2(self.datas[0], fallback_stop_loss=6.41)

    def next(self, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('next-start')
        print('%s open: %s' % (dt.isoformat(), self.datas[0].open[0]))
        print('%s high: %s' % (dt.isoformat(), self.datas[0].high[0]))
        print('%s low: %s' % (dt.isoformat(), self.datas[0].low[0]))
        print('%s close: %s' % (dt.isoformat(), self.datas[0].close[0]))
        print('%s psar: %s' % (dt.isoformat(), self.psar[0]))
        print('next-end')


class TestTrailingStopLossRestore(unittest.TestCase):

    def test_simple(self):

        cerebro = Cerebro()

        cerebro.addstrategy(TestStrategy)

        # 'apiKey' and 'secret' are skipped
        config = {'enableRateLimit': True, 'nonce': lambda: str(int(time.time() * 1000))}

        feed = CCXTFeed(exchange='binance',
                        dataname='BNB/USDT',
                        # valid values are:
                        # ticks, microseconds, seconds, minutes, daily, weekly, monthly
                        timeframe=TimeFrame.Minutes,
                        fromdate=dt.datetime(2019,1,28,3,30),
                        todate=dt.datetime(2019,1,28,10,00),
                        compression=15,
                        ohlcv_limit=2,  # required to make calls to binance exchange work
                        currency='BNB',
                        config=config,
                        retries=5,
                        # drop_newest=True,
                        # historical=False,
                        debug=True,
                        )

        # Add the feed
        cerebro.adddata(feed)

        # Run the strategy
        cerebro.run()

if __name__ == '__main__':
    unittest.main()
