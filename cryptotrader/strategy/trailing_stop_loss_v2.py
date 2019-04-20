from backtrader import Order, Strategy
from ccxt import InvalidOrder

from cryptotrader.indicator.ParabolicSLv2 import ParabolicSLv2


class TrailingStopLossV2(Strategy):
    params = (
        ('buy_pos_size', None),
        ('slippage', None),
        ('buy_limit', None),
        ('fallback_stop_loss', None),
        ('data_status4trading', 'DELAYED'),
    )

    def __init__(self):
        self.bought = False
        self.buy_order = None
        self.sell_order = None
        self.finished = False
        self.psar = ParabolicSLv2(self.datas[0], position=self.position,
                                fallback_stop_loss=self.params.fallback_stop_loss)
        self.params.data_status4trading = 'DELAYED' if not self.params.data_status4trading \
            else self.params.data_status4trading

    def next(self):
        self.log(f'next() '
                 f'Open: {self.datas[0].open[0]}, '
                 f'High: {self.datas[0].high[0]}, '
                 f'Low: {self.datas[0].low[0]}, '
                 f'Close: {self.datas[0].close[0]}, '
                 f'PSAR: {self.psar[0]} in next()')

        if self.data_status4trading == self.params.data_status4trading:
            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.bought:
                try:
                    self.cancel(self.sell_order)
                    self.log(f'Order #{self.sell_order.ref} canceled '
                             f'in next()')

                    prev_sell_order_price = self.sell_order.params.price
                    limit_price = self.psar.lines.psar[0] - self.params.slippage
                    # send a sell order with the updated psar as stopPrice
                    self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                                                stopPrice=self.psar.lines.psar[0],
                                                price=limit_price)
                    # self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                    #                             price=self.psar.lines.psar[0],
                    #                             plimit=limit_price)
                    self.log(
                        f'Order #{self.sell_order.ref} submitting stop limit sell raise '
                        f'from trigger price {-1 if prev_sell_order_price == None else round(prev_sell_order_price, 4)} '
                        f'to trigger price {round(self.psar.lines.psar[0], 4)} (limit price {limit_price})'
                    )
                except InvalidOrder as invalid_order:
                    self.log(f'Invalid order: {invalid_order}')

            elif not self.buy_order:
                # use limit buy order and interrupt the program if the market price is below the order price
                self.buy_order = self.buy(size=self.params.buy_pos_size,
                                          price=self.params.buy_limit,
                                          exectype=Order.Limit)
                self.log(f'submitted buy order for {self.params.buy_limit} at {self.datas[0].close[0]}')
                # self.initial_stop_limit_sell()

    def sigstop(self):
        print('Plotting the chart and then stopping Backtrader')
        self.env.runstop()

    def notify_data(self, data, status, *args, **kwargs):
        self.log('Data: {}, Data Status: {}, Order Status: {}'.format(data, data._getstatusname(status), status))
        self.data_status4trading = data._getstatusname(status)

    def notify_order(self, order, *args, **kwargs):
        self.log(f'Order #{order.ref} {Order.Status[order.status]}')
        if self.sell_order and self.sell_order.ref == order.ref and order.status in [order.Completed]:
            self.log(f'Order #{order.ref} Hit p_sl ().  Sold at: .')
            self.sigstop()
        if self.buy_order.ref == order.ref and order.status in [order.Completed] and not self.initial_sl_set:
            self.bought = True
            self.initial_stop_limit_sell()
        # if self.sell_order and self.sell_order.ref == order.ref:
        #     if order.status == 5:  # Order canceled
        #         prev_sell_order_price = self.sell_order.params.price
        #         limit_price = self.psar.lines.psar[0] - self.params.slippage
        #         # send a sell order with the updated psar as stopPrice
        #         self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
        #                                     stopPrice=self.psar.lines.psar[0],
        #                                     price=limit_price)
        #         # self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
        #         #                             price=self.psar.lines.psar[0],
        #         #                             plimit=limit_price)
        #         self.log(
        #             f'Order #{self.sell_order.ref} submitting stop limit sell raise '
        #             f'from trigger price {-1 if prev_sell_order_price == None else round(prev_sell_order_price, 4)} '
        #             f'to trigger price {round(self.psar.lines.psar[0], 4)} (limit price {limit_price})'
        #         )
        #         self.sell_order_canceled = False

    def notify_trade(self, trade, *args, **kwargs):
        self.log(f'Trade #{trade.ref} {trade.status_names[trade.status]}')
        if self.buy_order.ref == trade.ref and trade.long:
            if trade.isopen:  # opened long trade
                self.log('Bought {} at {}'.format(trade.size, trade.price))
                self.initial_stop_limit_sell()
            elif trade.isclosed:
                self.log('Trade closed. Hit p_sl ({}). Sold at: {}.'.format(
                    self.sell_order.price, self.sell_order.plimit
                ))
                self.sigstop()

        if self.sell_order and self.sell_order.ref == trade.ref:
            self.log('Hit p_sl ({}). Sold at: {}.'.format(
                self.psar.lines.psar[0], trade.price
            ))
            self.sigstop()

    def initial_stop_limit_sell(self):

        self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                                    stopPrice=self.params.fallback_stop_loss,
                                    price=self.params.fallback_stop_loss - self.params.slippage)
        # self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
        #                             price=self.params.fallback_stop_loss,
        #                             plimit=self.params.fallback_stop_loss - self.params.slippage)
        self.log(
            f'Order #{self.sell_order.ref} submitting initial stop limit sell order '
            f'from trigger price {self.params.fallback_stop_loss} '
            f'to trigger price {self.params.fallback_stop_loss - self.params.slippage}'
        )

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        try:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        except IndexError:
            print('%s' % txt)
