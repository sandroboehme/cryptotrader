import json
import os
import time

import backtrader as bt
import sys

from ccxtbt import CCXTStore
from cryptotrader.CTCerebro import CTCerebro
from cryptotrader.strategy.trailing_stop_loss_v2 import TrailingStopLossV2
from definitions import ROOT_PATH, CONFIG_PATH


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

    cerebro.addstrategy(TrailingStopLossV2,
                        buy_pos_size=ideaParams['buy_pos_size'],
                        slippage=ideaParams['slippage'],
                        buy_limit=ideaParams['buy_limit'],
                        fallback_stop_loss=ideaParams['fallback_stop_loss'],
                        data_status4trading=ideaParams.get('data_status4trading'),
                        )

    with open(CONFIG_PATH, 'r') as f:
        params = json.load(f)

    config = {'apiKey': params["keys"]["binance"]["apikey"],
              'secret': params["keys"]["binance"]["secret"],
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
            bt.Order.StopLimit: 'STOP_LOSS_LIMIT'
        },
        'mappings': {
            'closed_order': {
                'key': 'status',
                'value': 'closed'
            },
            'canceled_order': {
                'key': 'status',
                'value': 'canceled'}
        }
    }

    broker = store.getbroker(broker_mapping=broker_mapping)
    cerebro.setbroker(broker)

    # Get our data
    # Drop newest will prevent us from loading partial data from incomplete candles
    data = store.getdata(exchange=ideaParams['exchange'],
                         dataname=ideaParams['symbol'],
                         timeframe=tframes[ideaParams['timeframe']],
                         fromdate=None,
                         compression=ideaParams['compression'],
                         ohlcv_limit=2,  # required to make calls to binance exchange work
                         currency=ideaParams['currency'],
                         config=config,
                         retries=5,
                         drop_newest=False,
                         # historical=True,
                         backfill_start=False,
                         backfill=False
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

    abs_chart_file_path = os.path.join(os.path.dirname(abs_param_file), ideaParams['chartFileName'])
    cerebro.plotToFile(style='candlestick', path=abs_chart_file_path)


if __name__ == '__main__':
    sys_args = sys.argv[1:]
    main(sys_args)
