import os
import time
import datetime as dt

import backtrader as bt

from ccxtbt import CCXTFeed

from cryptotrader.CTCerebro import CTCerebro
from definitions import ROOT_PATH


class TestStrategy(bt.Strategy):

    def next(self, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('next-start')
        print('%s open: %s' % (dt.isoformat(), self.datas[0].open[0]))
        print('%s high: %s' % (dt.isoformat(), self.datas[0].high[0]))
        print('%s low: %s' % (dt.isoformat(), self.datas[0].low[0]))
        print('%s close: %s' % (dt.isoformat(), self.datas[0].close[0]))
        print('next-end')
        self.env.runstop()


def main():

    cerebro = CTCerebro(preload=False)
    # cerebro = CTCerebro(preload=False)

    cerebro.addstrategy(TestStrategy)
    hist_start_date = dt.datetime.utcnow() - dt.timedelta(seconds=10)

    # Add the feed
    cerebro.adddata(CCXTFeed(exchange='binance',
                             dataname='BNB/USDT',
                             timeframe=bt.TimeFrame.Minutes,
                             #fromdate=hist_start_date,
                             #todate=dt.datetime.utcnow(),
                             fromdate=hist_start_date,
                             compression=1,
                             ohlcv_limit=2,
                             currency='BNB',
                             retries=5,
                             debug=True,

                             # 'apiKey' and 'secret' are skipped
                             config={'enableRateLimit': True, 'nonce': lambda: str(int(time.time() * 1000))}))

    try:
        # Run the strategy
        cerebro.run()
    except KeyboardInterrupt:
        print("finished by user.")
        cerebro.runstop()
        # abs_chart_file_path = os.path.join(os.path.dirname(ROOT_PATH), 'test.png')
        # cerebro.plotToFile(style='candlestick', path=abs_chart_file_path)

    # abs_chart_file_path = os.path.join(os.path.dirname(ROOT_PATH), 'test.png')
    # print(abs_chart_file_path)
    # cerebro.plotToFile(style='candlestick', path=abs_chart_file_path)


if __name__ == '__main__':
    main()
