import json
import time
from datetime import datetime

import backtrader as bt
import sys

from ccxtbt import CCXTFeed, CCXTStore
from cryptotrader.CTCerebro import CTCerebro
from cryptotrader.strategy.trailing_stop_loss import TrailingStopLoss

cerebro = CTCerebro(preload=False)

arguments = sys.argv[1:]

parameterFile = './liveBacktesting.json' if len(arguments) == 0 else arguments[0]

with open(parameterFile, 'r') as f:
    ideaParams = json.load(f)

cerebro.broker.setcash(ideaParams['initial_cash'])

cerebro.addstrategy(TrailingStopLoss,
                    buy_pos_size=ideaParams['buy_pos_size'],
                    slippage=ideaParams['slippage'],
                    buy_limit=ideaParams['buy_limit'],
                    fallback_stop_loss=ideaParams['fallback_stop_loss'],
                    data_status4trading=ideaParams.get('data_status4trading'),
                    )

with open(ideaParams['api_key_file_location'], 'r') as f:
    params = json.load(f)

config = {'apiKey': params["binance"]["apikey"],
          'secret': params["binance"]["secret"],
          'enableRateLimit': True,
          'nonce': lambda: str(int(time.time() * 1000)),
          }

tframes = dict(
    ticks=bt.TimeFrame.Ticks,
    microseconds=bt.TimeFrame.MicroSeconds,
    seconds=bt.TimeFrame.Seconds,
    minutes=bt.TimeFrame.Minutes,
    daily=bt.TimeFrame.Days,
    weekly=bt.TimeFrame.Weeks,
    monthly=bt.TimeFrame.Months)


if ideaParams.get('fromdate'):
    fromdate = datetime(
        ideaParams['fromdate']['year'],
        ideaParams['fromdate']['month'],
        ideaParams['fromdate']['day'],
        ideaParams['fromdate']['hour'],
        ideaParams['fromdate']['minute'])
else:
    fromdate = None

store = CCXTStore(
    exchange=ideaParams['exchange'],
    currency=ideaParams['currency'],
    config=config,
    retries=5,
    debug=True)

# Get the broker and pass any kwargs if needed.
# ----------------------------------------------
# Broker mappings have been added since some exchanges expect different values
# to the defaults. Case in point, Kraken vs Bitmex. NOTE: Broker mappings are not
# required if the broker uses the same values as the defaults in CCXTBroker.
broker_mapping = {
    'order_types': {
        bt.Order.Market: 'market',
        bt.Order.Limit: 'limit',
        bt.Order.Stop: 'stop-loss',  # stop-loss for kraken, stop for bitmex
        bt.Order.StopLimit: 'stop limit'
    },
    'mappings': {
        'closed_order': {
            'key': 'status',
            'value': 'closed'
        },
        'canceled_order': {
            'key': 'result',
            'value': 1}
    }
}

broker = store.getbroker(broker_mapping=broker_mapping)
cerebro.setbroker(broker)

# Get our data
# Drop newest will prevent us from loading partial data from incomplete candles
data = store.getdata(exchange=ideaParams['exchange'],
                dataname=ideaParams['symbol'],
                # valid values are:
                # ticks, microseconds, seconds, minutes, daily, weekly, monthly
                timeframe=tframes[ideaParams['timeframe']],
                fromdate=fromdate,
                compression=ideaParams['compression'],
                ohlcv_limit=2,  # required to make calls to binance exchange work
                currency=ideaParams['currency'],
                config=config,
                retries=5
                , drop_newest=False
                              # , historical=True
                , backfill_start=False
                , backfill=False
                # debug=True,
                )
# Add the feed
cerebro.adddata(data)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run the strategy
cerebro.run()

# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plotToFile(style='candlestick', path=ideaParams['chartFileName'])
