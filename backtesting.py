import json
import os
import time
import datetime as dt

import backtrader as bt
import sys

from ccxtbt import CCXTFeed
from cryptotrader.strategy.trailing_stop_loss_v2 import TrailingStopLossV2
from cryptotrader.CTCerebro import CTCerebro
from cryptotrader.strategy.trailing_stop_loss_v3 import TrailingStopLossV3
from definitions import ROOT_PATH, CONFIG_PATH


class TestStrategy(bt.Strategy):

    def next(self, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('next-start')
        print('%s open: %s' % (dt.isoformat(), self.datas[0].open[0]))
        print('%s high: %s' % (dt.isoformat(), self.datas[0].high[0]))
        print('%s low: %s' % (dt.isoformat(), self.datas[0].low[0]))
        print('%s close: %s' % (dt.isoformat(), self.datas[0].close[0]))
        print('next-end')


def main(arguments):
    """
    Please provide the parameter file name with a path relative to the project root.
    """

    cerebro = CTCerebro(preload=False)

    try:
        rel_param_file = arguments[0]
    except:
        print('Please provide the parameter file name.')
        sys.exit(1)  # abort
    abs_param_file = os.path.join(ROOT_PATH, rel_param_file)
    with open(abs_param_file, 'r') as f:
        ideaParams = json.load(f)

    cerebro.broker.setcash(ideaParams['initial_cash'])

    abs_chart_file_path = os.path.join(os.path.dirname(abs_param_file), ideaParams['chartFileName'])
    cerebro.addstrategy(TrailingStopLossV3,
                        buy_pos_size=ideaParams['buy_pos_size'],
                        slippage=ideaParams['slippage'],
                        buy_limit=ideaParams['buy_limit'],
                        fallback_stop_loss=ideaParams['fallback_stop_loss'],
                        data_status4trading=ideaParams.get('data_status4trading'),
                        )

    # cerebro.addstrategy(TestStrategy)

    with open(CONFIG_PATH, 'r') as f:
        params = json.load(f)


    # 'apiKey' and 'secret' are skipped
    config = {'enableRateLimit': True, 'nonce': lambda: str(int(time.time() * 1000))}

    tframes = dict(
        ticks=bt.TimeFrame.Ticks,
        microseconds=bt.TimeFrame.MicroSeconds,
        seconds=bt.TimeFrame.Seconds,
        minutes=bt.TimeFrame.Minutes,
        daily=bt.TimeFrame.Days,
        weekly=bt.TimeFrame.Weeks,
        monthly=bt.TimeFrame.Months)


    if ideaParams.get('fromdate'):
        fromdate = dt.datetime(
            ideaParams['fromdate']['year'],
            ideaParams['fromdate']['month'],
            ideaParams['fromdate']['day'],
            ideaParams['fromdate']['hour'],
            ideaParams['fromdate']['minute'])
    else:
        fromdate = None

    # feed = CCXTFeed(exchange='binance',
    #                          dataname='BNB/USDT',
    #                          timeframe=bt.TimeFrame.Minutes,
    #                          #fromdate=hist_start_date,
    #                          #todate=dt.datetime.utcnow(),
    #                          fromdate=dt.datetime.utcnow(),
    #                          compression=1,
    #                          ohlcv_limit=2,
    #                          currency='BNB',
    #                          retries=5,
    #
    #                          # 'apiKey' and 'secret' are skipped
    #                          config={'enableRateLimit': True, 'nonce': lambda: str(int(time.time() * 1000))})

    feed = CCXTFeed(exchange=ideaParams['exchange'],
                    dataname=ideaParams['symbol'],
                    # valid values are:
                    # ticks, microseconds, seconds, minutes, daily, weekly, monthly
                    timeframe=tframes[ideaParams['timeframe']],
                    fromdate=fromdate, #dt.datetime.utcnow(),
                    compression=ideaParams['compression'],
                    ohlcv_limit=2,  # required to make calls to binance exchange work
                    currency=ideaParams['currency'],
                    config=config,
                    retries=5,
                    # drop_newest=True,
                    # historical=False,
                    debug=True,
                    )

    # Add the feed
    cerebro.adddata(feed)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run the strategy
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    abs_chart_file_path = os.path.join(os.path.dirname(abs_param_file), ideaParams['chartFileName'])
    cerebro.plotToFile(style='candlestick', path=abs_chart_file_path)


if __name__ == '__main__':
    sys_args = sys.argv[1:]
    main(sys_args)
