from backtrader import Order, Strategy


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
        self.sell_order_canceled = False
        from cryptotrader.indicator.ParabolicSL import ParabolicSL
        self.psar = ParabolicSL(self.datas[0], position=self.position,
                                fallback_stop_loss=self.params.fallback_stop_loss)
        self.params.data_status4trading = 'DELAYED' if not self.params.data_status4trading \
            else self.params.data_status4trading

    def next(self):
        self.log('Close, %.4f psar: %.4f' % (self.datas[0].close[0], self.psar[0]))

        if self.data_status4trading == self.params.data_status4trading:
            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.bought:
                if self.sell_order \
                        and not self.sell_order_canceled\
                        and self.sell_order.status == 2: # if accepted
                    self.cancel(self.sell_order)
                    self.sell_order_canceled = True
                    self.log('canceled sell order {}'.format(self.sell_order.ref))

            elif not self.buy_order and self.datas[0].close[0] < self.params.buy_limit:
                # use limit buy order and interrupt the program if the market price is below the order price
                self.buy_order = self.buy(size=self.params.buy_pos_size,
                                          price=self.params.buy_limit,
                                          exectype=Order.Limit)
                self.log('submitted buy at {}'.format(self.datas[0].close[0]))

    def sigstop(self):
        print('Plotting the chart and then stopping Backtrader')
        self.env.runstop()

    def notify_data(self, data, status, *args, **kwargs):
        self.log('Data: {}, Data Status: {}, Order Status: {}'.format(data, data._getstatusname(status), status))
        self.data_status4trading = data._getstatusname(status)

    def notify_order(self, order, *args, **kwargs):
        if self.sell_order and self.sell_order.ref == order.ref:
            if order.status == 5: # Order canceled
                self.log('notify canceled sell order {}'.format(self.sell_order.ref))
                prev_sell_order_price = self.sell_order.params.price
                # send a sell order with the updated psar as stopPrice
                self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                                            price=self.psar.lines.psar[0],
                                            plimit=self.psar.lines.psar[0] - self.params.slippage,
                                            pricelimit=self.psar.lines.psar[0] - self.params.slippage)
                self.sell_order_canceled = False
                self.log('Raised stop limit sell from {} to {} with ref {}'.format(
                    prev_sell_order_price,
                    self.psar.lines.psar[0],
                    self.sell_order.ref)
                )

    def notify_trade(self, trade, *args, **kwargs):
        if self.buy_order.ref == trade.ref and trade.long:
            if trade.isopen:  # opened long trade
                self.bought = True
                self.log('Bought {} at {}'.format(trade.size, trade.price))
                self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                                            price=self.params.fallback_stop_loss,
                                            plimit=self.params.fallback_stop_loss - self.params.slippage)
            elif trade.isclosed:
                self.log('Trade closed. Hit p_sl ({}). Sold at: {}.'.format(
                    self.psar.lines.psar[0], trade.price
                ))
                self.sigstop()

        if self.sell_order and self.sell_order.ref == trade.ref:
            self.log('Hit p_sl ({}). Sold at: {}.'.format(
                self.psar.lines.psar[0], trade.price
            ))
            self.sigstop()

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        try:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        except IndexError:
            print('%s' % txt)
