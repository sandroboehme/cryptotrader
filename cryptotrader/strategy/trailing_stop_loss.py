from backtrader import Order, Strategy


class TrailingStopLoss(Strategy):
    params = (
        ('buy_pos_size', None),
        ('slippage', None),
        ('buy_limit', None),
        ('fallback_stop_loss', None),
        ('data_status4trading', 'DELAYED'),
    )

    def __init__(self):
        self.ordered = False
        from cryptotrader.indicator.ParabolicSL import ParabolicSL
        self.psar = ParabolicSL(self.datas[0], position=self.position,
                                fallback_stop_loss=self.params.fallback_stop_loss)
        self.params.data_status4trading = 'DELAYED' if not self.params.data_status4trading else self.params.data_status4trading

    def next(self):
        self.log('Close, %.4f psar: %.4f' % (self.datas[0].close[0], self.psar[0]))

        if self.data_status4trading == self.params.data_status4trading:
            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.ordered:
                self.log('check if {} <= {}'.format(self.datas[0].close[0], self.psar.lines.psar[0]))
                parabolic_sl_hit = self.datas[0].close[0] <= self.psar.lines.psar[0]
                if parabolic_sl_hit:
                    sell_limit_order_price = self.datas[0].close[0] - self.params.slippage
                    self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.Limit,
                                               price=sell_limit_order_price)
                    self.log(
                        'Hit p_sl ({}). Price: {}. Tradeid: {}'.format(self.psar.lines.psar[0], self.sell_order.price, self.sell_order.tradeid))
                    self.sigstop()
            elif self.datas[0].close[0] < self.params.buy_limit:
                # use limit buy order and interrupt the program if the market price is below the order price
                self.buy_order = self.buy(valid=None, size=self.params.buy_pos_size, exectype=Order.Market)
                self.ordered = True
                self.log('submitted buy order {} at {}'.format(self.buy_order, self.datas[0].close[0]))

    def sigstop(self):
        print('Plotting the chart and then stopping Backtrader')
        self.env.runstop()

    def notify_data(self, data, status, *args, **kwargs):
        self.log('Data: {}, Data Status: {}, Order Status: {}'.format(data, data._getstatusname(status), status))
        self.data_status4trading = data._getstatusname(status)

    def notify_order(self, order, *args, **kwargs):
        self.log('order: {}'.format(order))

    def notify_trade(self, trade, *args, **kwargs):
        self.log('trade: {}'.format(trade))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        try:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        except IndexError:
            print('%s' % (txt))