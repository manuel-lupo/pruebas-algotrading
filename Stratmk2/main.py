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
    params = (
        ('small_period', 30),
        ('long_period', 200)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.boll_band = bt.ind.BollingerBands(self.data0, period= 30, devfactor=2)
        self.rsi = bt.indicators.RSI(self.data0, period=12)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data0, period=self.params.long_period
        )
        self.small_sma = bt.indicators.SimpleMovingAverage(
            self.data0, period=self.params.small_period
        )
        self.crossover = bt.indicators.CrossOver(self.long_sma, self.small_sma)
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
        isBuy = ((self.crossover == -1) or (self.data0.close < self.boll_band.bot)) and ((self.rsi <= 30) or (self.long_sma < self.boll_band.mid)) 
        return isBuy
    def sell_signal(self):
        isSell = False
        isSell = ((self.crossover == 1) or (self.data0.close > self.boll_band.top)) and ((self.rsi >= 75) or (self.boll_band_hold_sell()) or (self.long_sma > self.boll_band.top))
        return isSell
   
    #FUNCIONES IMPLEMENTADAS EN BASE A LOS INDICADORES
    
    #esta funcion detecta una caida en el rsi al dia de hoy, cruzando por debajo del 75%
    #intentamos predecir una caida en el precio de la accion por medio del rsi, por lo que el bot debera vender antes de que baje aun mas
    #problema ante falsas señales bajistas
    
    def rsi_cross_down(self, treshold=75):
        flag=False
        if (self.rsi[-1] > treshold):
            flag= self.rsi[0] < treshold
        return flag     
    
    #esta funcion aplica para la venta, devuelve true si el precio de cierre se mantuvo por arriba del top de la banda de bollinger durantes 3 dias
    #al mantenerse el precio de cierre por arriba del top, intentamos predecir tendencias alcistas y vender lo mas caro posible
    #no funciona correctamente en caso de que el precio siga aumentando los dias siguientes

    def boll_band_hold_sell(self, period=2):
        flag=True
        for i in range(period):
            flag= self.data0.close[-i] > self.boll_band.top[-i]
            if not flag:
                break   
        return flag
    
    def boll_band_hold_buy(self, period=2):
        flag=True
        for i in range(period):
            flag= self.data0.close[-i] < self.boll_band.bot[-i]
            if not flag:
                break   
        return flag
               
    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.data0.close[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        print(self.rsi[-1])
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
    
    cerebro.addsizer(bt.sizers.PercentSizer, percents=35)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Final Cash Value: %.2f' % cerebro.broker.getcash())
 
    cerebro.plot()

    # Print out the final result
    
    #Esta estrategia no hace demasiados trades y pierde una sola vez, pero no aprovecha la tendencia mas alcista que presenta el grafico