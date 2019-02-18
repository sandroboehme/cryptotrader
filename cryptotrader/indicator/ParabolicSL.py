from backtrader.indicators import PeriodN


class _SarStatus(object):
    sar = None
    tr = None
    af = 0.0
    ep = 0.0
    inPosition = False

    def __str__(self):
        txt = []
        txt.append('sar: {}'.format(self.sar))
        txt.append('tr: {}'.format(self.tr))
        txt.append('af: {}'.format(self.af))
        txt.append('ep: {}'.format(self.ep))
        return '\n'.join(txt)


class ParabolicSL(PeriodN):
    """
    Parabolic Stop Loss

    This is a Parabolic SAR indicator that can be initialized after a buy or sell order
    has been filled to set a stop loss or to trigger a stop buy order.

    The Parabolic SAR has been defined by J. Welles Wilder, Jr. in 1978 in his book
    *"New Concepts in Technical Trading Systems"* for the RSI

    SAR stands for *Stop and Reverse* and the indicator was meant as a signal
    for entry (and reverse)

    How to select the 1st signal is left unspecified in the book and the
    increase/decrease of bars

    See:
      - https://en.wikipedia.org/wiki/Parabolic_SAR
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:parabolic_sar
    """
    alias = ('PSAR',)
    lines = ('psar',)
    params = (
        ('position', None),
        ('fallback_stop_loss', None),
        ('period', 2),  # when to start showing values
        ('af', 0.02),
        ('afmax', 0.20),
    )

    plotinfo = dict(subplot=False)
    plotlines = dict(
        psar=dict(
            marker='.', markersize=4.0, color='black', fillstyle='full', ls=''
        ),
    )

    def prenext(self):
        if len(self) == 1:
            self._status = []  # empty status
            return  # not enough data to do anything

        elif len(self) == 2:
            self.nextstart()  # kickstart calculation
        else:
            self.next()  # regular calc

        self.lines.psar[0] = float('NaN')  # no return yet still prenext

    def nextstart(self):
        if self._status:  # some states have been calculated
            self.next()  # delegate
            return

        # Prepare a status holding array, for current and previous lengths
        self._status = [_SarStatus(), _SarStatus()]

        # Start by looking if price has gone up/down (close) in the 2nd day to
        # get an *entry* signal and configure the values as they would have
        # been in the previous trend, including a sar value which is
        # immediately invalidated in next, which reverses and sets the trend to
        # the actual up/down value calculated with the close
        # Put the 4 status variables in a Status holder
        plenidx = (len(self) - 1) % 2  # previous length index (0 or 1)
        status = self._status[plenidx]

        # Calculate the status for previous length
        status.sar = (self.data.high[0] + self.data.low[0]) / 2.0

        status.af = self.p.af
        if self.data.close[0] >= self.data.close[-1]:  # uptrend
            status.tr = not True  # uptrend when reversed
            status.ep = self.data.low[-1]  # ep from prev trend
        else:
            status.tr = not False  # downtrend when reversed
            status.ep = self.data.high[-1]  # ep from prev trend

        # With the fake prev trend in place and a sar which will be invalidated
        # go to next to get the calculation done
        self.next()

    def next(self):
        dt = self.datas[0].datetime.datetime(0)

        # The high of the current candle
        hi = self.data.high[0]

        # The low of the current candle
        lo = self.data.low[0]
        self.log(f'PSAR High: {hi} Low: {lo}')

        plenidx = (len(self) - 1) % 2  # previous length index (0 or 1)
        status = self._status[plenidx]  # use prev status for calculations

        # as soon as the buy order has been triggered there is a position size
        size = self._owner.position.size
        inPositionOnExchange = size > 0

        # status.inPosition signals if the psar algorithm assumes to be in a position (psar below market price)
        # or not in a position (psar above the market price)
        justBought = inPositionOnExchange and not status.inPosition

        tr = status.tr
        sar = status.sar

        # Check if the sar penetrated the price to switch the trend
        if (tr and sar >= lo) or (not tr and sar <= hi) or justBought:
            tr = not tr  # reverse the trend
            tr = True if justBought else tr
            # new sar is prev SIP (Significant price)
            # take the previous extreme point or the fallback stop loss if it's lower and I just bought
            justBoughtAndFallbackIsLower = justBought and self.p.fallback_stop_loss < status.ep
            sar = self.p.fallback_stop_loss if justBoughtAndFallbackIsLower else status.ep
            ep = hi if tr else lo  # select new SIP / Extreme Price
            print('Trend switched. Sar: {} (fbsl: {}, prev. ep: {})'.format(sar, self.p.fallback_stop_loss, status.ep))
            # ep = ep if not self.p.fallback_stop_loss else self.p.fallback_stop_loss
            af = self.p.af  # reset acceleration factor

        else:  # use the precalculated values
            ep = status.ep
            af = status.af

        # Update sar value for today
        self.lines.psar[0] = sar

        # Update ep and af if needed
        if tr:  # long trade
            if hi > ep:
                ep = hi
                af = min(af + self.p.af, self.p.afmax)

        else:  # downtrend
            if lo < ep:
                ep = lo
                af = min(af + self.p.af, self.p.afmax)

        sar = sar + af * (ep - sar)  # calculate the sar for tomorrow

        # make sure sar doesn't go into hi/lows
        # Wikipedia:
        # If the next period’s SAR value is inside (or beyond) the current period or the previous period’s price range,
        # the SAR must be set to the closest price bound.
        # For example, if in an upward trend, the new SAR value is calculated
        # and if it results to be more than today’s or yesterday’s lowest price,
        # it must be set equal to that lower boundary.

        if tr:  # long trade
            lo1 = self.data.low[-1]
            if sar > lo or sar > lo1:
                sar = min(lo, lo1)  # sar not above last 2 lows -> lower
        else:
            hi1 = self.data.high[-1]
            if sar < hi or sar < hi1:
                sar = max(hi, hi1)  # sar not below last 2 highs -> highest

        # new status has been calculated, keep it in current length
        # will be used when length moves forward
        newstatus = self._status[not plenidx]
        newstatus.tr = tr
        newstatus.sar = sar
        newstatus.ep = ep
        newstatus.af = af
        newstatus.inPosition = size > 0

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        try:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        except IndexError:
            print('%s' % txt)
