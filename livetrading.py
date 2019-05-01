import json
import os
import time
import datetime as dt

import backtrader as bt
import sys

from ccxtbt import CCXTStore
from cryptotrader.CTCerebro import CTCerebro
from cryptotrader.persistence.persistence_factory import PersistenceFactory
from cryptotrader.persistence.persistence_type import PersistenceType
from cryptotrader.strategy.trailing_stop_loss_v3 import TrailingStopLossV3
from definitions import ROOT_PATH, CONFIG_PATH


def get_candle_state_index(cs_persistence):
    last_file_id = cs_persistence.get_last_file_id()
    return 0 if last_file_id is None else last_file_id


def get_cs_persistence(trade_setup):
    persistence_type = PersistenceType(trade_setup['candle_state_persistence_type'])
    trade_parameter = dict(exchange=trade_setup['exchange'],
                           pair=trade_setup['symbol'],
                           year=trade_setup['fromdate']['year'],
                           month=trade_setup['fromdate']['month'],
                           day=trade_setup['fromdate']['day'],
                           trade_id=trade_setup['name'])
    cs_persistence = PersistenceFactory.get_cs_persistance(persistence_type, **trade_parameter, root_path=ROOT_PATH)
    return cs_persistence


def main(path, name, persistence_type=PersistenceType.GOOGLE_FIRESTORE):
    """
    Please provide the parameter file name with a path relative to the project root.
    """
    cerebro = CTCerebro(preload=False)

    try:
        trade_setup_persistence = PersistenceFactory.get_persistance(persistence_type,
                                                                     path,
                                                                     name,
                                                                     root_path=ROOT_PATH)
        trade_setup = trade_setup_persistence.get_setup()
    except:
        print('Please provide the parameter file name.')
        sys.exit(1)  # abort

    cs_persistence = get_cs_persistence(trade_setup)

    cerebro.broker.setcash(trade_setup['initial_cash'])

    abs_param_file = os.path.join(ROOT_PATH, 'trade_setups/backtestBNBPsarSL.json')
    cerebro.addstrategy(TrailingStopLossV3,
                        buy_pos_size=trade_setup['buy_pos_size'],
                        slippage=trade_setup['slippage'],
                        buy_limit=trade_setup['buy_limit'],
                        fallback_stop_loss=trade_setup['fallback_stop_loss'],
                        data_status4trading=trade_setup.get('data_status4trading'),
                        state_iteration_index=get_candle_state_index(cs_persistence),
                        cs_persistence=cs_persistence,
                        trade_setup_persistence=trade_setup_persistence,
                        # state_bucket_folder=...
                        abs_param_file=abs_param_file
                        )

    with open(CONFIG_PATH, 'r') as f:
        runtime_config = json.load(f)

    store_config = {'apiKey': runtime_config["keys"]["binance"]["apikey"],
                    'secret': runtime_config["keys"]["binance"]["secret"],
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
        exchange=trade_setup['exchange'],
        currency=trade_setup['currency'],
        config=store_config,
        retries=5,
        debug=True)

    broker = store.getbroker()
    cerebro.setbroker(broker)

    if trade_setup.get('fromdate'):
        fromdate = dt.datetime(
            trade_setup['fromdate']['year'],
            trade_setup['fromdate']['month'],
            trade_setup['fromdate']['day'],
            trade_setup['fromdate']['hour'],
            trade_setup['fromdate']['minute'])
    else:
        fromdate = None

    # Get our data
    # Drop newest will prevent us from loading partial data from incomplete candles
    data = store.getdata(exchange=trade_setup['exchange'],
                         dataname=trade_setup['symbol'],
                         timeframe=tframes[trade_setup['timeframe']],
                         fromdate=fromdate,
                         compression=trade_setup['compression'],
                         ohlcv_limit=2,  # required to make calls to binance exchange work
                         currency=trade_setup['currency'],
                         config=store_config,
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

    # abs_chart_file_path = os.path.join(os.path.dirname(abs_param_file), trade_setup['chartFileName'])
    # cerebro.plotToFile(style='candlestick', path=abs_chart_file_path)


if __name__ == '__main__':
    sys_args = sys.argv[1:]
    main(sys_args)
