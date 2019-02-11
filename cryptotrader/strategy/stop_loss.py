from backtrader import Order, Strategy


class StopLoss(Strategy):
    params = (
        ('buy_pos_size', None),
        ('slippage', None),
        ('buy_limit', None),
        ('fallback_stop_loss', None),
        ('data_status4trading', 'DELAYED'),
    )

    def __init__(self):
        self.ordered = False
        self.buy_order = None
        self.sell_order = None
        from cryptotrader.indicator.ParabolicSL import ParabolicSL
        self.psar = ParabolicSL(self.datas[0], position=self.position,
                                fallback_stop_loss=self.params.fallback_stop_loss)
        self.params.data_status4trading = 'DELAYED' if not self.params.data_status4trading else self.params.data_status4trading

    def next(self):
        self.log('Close, %.4f psar: %.4f' % (self.datas[0].close[0], self.psar[0]))

        if not self.ordered:
            self.buy_order = self.buy(size=self.params.buy_pos_size,
                                      price=self.params.buy_limit,
                                      exectype=Order.Limit)
            self.ordered = True

    def sigstop(self):
        print('Plotting the chart and then stopping Backtrader')
        self.env.runstop()

    def notify_trade(self, trade, *args, **kwargs):
        # self.log('trade: {}'.format(trade))
        if self.buy_order.ref == trade.ref and trade.long:
            if trade.isopen: # opened long trade
                self.log('Bought {} at {}'.format(trade.size, trade.price))
                self.sell_order = self.sell(size=self.params.buy_pos_size, exectype=Order.StopLimit,
                                            # stopPrice=self.params.fallback_stop_loss,
                                            # price=self.params.fallback_stop_loss - self.params.slippage)
                                            price=self.params.fallback_stop_loss,
                                            plimit=self.params.fallback_stop_loss - self.params.slippage,
                                            pricelimit=self.params.fallback_stop_loss - self.params.slippage
                                            )
            elif trade.isclosed:
                self.log('Sell order matched. Sold at: {}.'.format(
                    trade.price
                ))
                self.sigstop()

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        try:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        except IndexError:
            print('%s' % (txt))