from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

def xor(a, b):
    return (a and not b) or (not a and b)

# Create a Stratey
class Stratmk2(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.boll_band = bt.ind.BollingerBands(self.data0, period= 30, devfactor=2)
        self.rsi = bt.indicators.RSI(self.data0, period=12)
        self.wma = bt.indicators.SimpleMovingAverage(self.data0, period = 16)
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def buy_signal(self):
        isBuy=False
        isBuy = (self.data0.close[0] < self.boll_band.bot) and self.rsi <= 35 and self.data0.close < self.wma
        return isBuy
    def sell_signal(self):
        isSell = False
        isSell = (self.data0.close[0] >= self.boll_band.top and self.rsi > 75) and (self.data0.close >= self.wma)
        return isSell
   

   #def sell_signal(self):
   #    isSell = False
   #    if self.data0.close[0] >= self.boll_band.mid:
   #        isSell = xor(self.rsi_aum() , (self.data0.close[0] >= self.boll_band.top and self.rsi > 75)) and self.data0.close >= self.wma
   #    return isSell
   #
   #def rsi_aum(self, period = 5):
   #    return self.rsi < self.rsi
            
           
    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.data0.close[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            if self.buy_signal():
                self.order = self.buy()
        else:
            if self.sell_signal():
                self.order = self.sell()

        
    

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    initial_cash = 10000
    
    # Add a strategy
    cerebro.addstrategy(Stratmk2)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../DATA FEEDS/orcl-1995-2014.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,

        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(initial_cash)


    # Set the commission
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addsizer(bt.sizers.PercentSizer, percents=60)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Profit percentage: {percentage}%'.format(percentage = cerebro.broker.getvalue()/initial_cash))
    cerebro.plot()

    # Print out the final result
    
    #Esta estrategia no hace demasiados trades y pierde una sola vez, pero no aprovecha la tendencia mas alcista que presenta el grafico