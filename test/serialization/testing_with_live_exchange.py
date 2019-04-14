import json
import os
import time
import datetime as dt

import backtrader as bt
import sys

from ccxtbt import CCXTStore
from cryptotrader.CTCerebro import CTCerebro
from cryptotrader.strategy.trailing_stop_loss_v2 import TrailingStopLossV2
from cryptotrader.strategy.trailing_stop_loss_v3 import TrailingStopLossV3
from cryptotrader.strategy.trailing_stop_loss_v3_back import TrailingStopLossV3Back
from definitions import ROOT_PATH, CONFIG_PATH


def main(arguments):
    """
    Please provide the parameter file name with a path relative to the project root.
    """
    cerebro = CTCerebro(preload=False)

    try:
        rel_param_file = arguments[0]
        state_iteration_index = arguments[1]
    except:
        print('Please provide the parameter file name and the state iteration index.')
        sys.exit(1)  # abort
    abs_param_file = os.path.join(ROOT_PATH, rel_param_file)
    with open(abs_param_file, 'r') as f:
        ideaParams = json.load(f)

    if ideaParams.get('event_stop') is None or not ideaParams.get('event_stop'):
        cerebro.broker.setcash(ideaParams['initial_cash'])

        cerebro.addstrategy(TrailingStopLossV3,
                            buy_pos_size=ideaParams['buy_pos_size'],
                            slippage=ideaParams['slippage'],
                            buy_limit=ideaParams['buy_limit'],
                            fallback_stop_loss=ideaParams['fallback_stop_loss'],
                            data_status4trading=ideaParams.get('data_status4trading'),
                            state_folder_path=os.path.join(os.path.dirname(abs_param_file), 'generated/state/'),
                            state_iteration_index=state_iteration_index,
                            abs_param_file=abs_param_file
                            )

        with open(CONFIG_PATH, 'r') as f:
            params = json.load(f)

        # No api keys are used to avoid unintentially sending orders to the exchange.
        config = {'enableRateLimit': True,
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

        broker = store.getbroker()
        cerebro.setbroker(broker)


        if ideaParams.get('fromdate'):
            fromdate = dt.datetime(
                ideaParams['fromdate']['year'],
                ideaParams['fromdate']['month'],
                ideaParams['fromdate']['day'],
                ideaParams['fromdate']['hour'],
                ideaParams['fromdate']['minute'])
            # This moves the fromdate forward depending on the timeframe and
            # how many iterations have been passed already.
            # e.g. for the 5th iteration of 15min timeframes: {'minutes': 5 * 15}
            fromdate = fromdate + bt.datetime.timedelta(**{
                ideaParams['timeframe']: state_iteration_index * ideaParams['compression']
            })
        else:
            fromdate = None

        # Get our data
        # Drop newest will prevent us from loading partial data from incomplete candles
        data = store.getdata(exchange=ideaParams['exchange'],
                             dataname=ideaParams['symbol'],
                             timeframe=tframes[ideaParams['timeframe']],
                             fromdate=fromdate,
                             compression=ideaParams['compression'],
                             ohlcv_limit=2,  # required to make calls to binance exchange work
                             currency=ideaParams['currency'],
                             config=config,
                             retries=5,
                             drop_newest=False,
                             # historical=True,
                             backfill_start=False,
                             backfill=False,
                             debug=True,
                             )
        # Add the feed
        cerebro.adddata(data)

        # Print out the starting conditions
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Run the strategy
        cerebro.run()

        # Print out the final result
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())


if __name__ == '__main__':
    sys_args = sys.argv[1:]
    main(sys_args)
