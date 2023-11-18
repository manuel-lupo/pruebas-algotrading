import datetime
import os.path
import sys

import backtrader as bt


class CrossStrategies(bt.Strategy):
    params = (
        ('small_period', 50),
        ('long_period', 200)
    )

    def log(self, txt, dt=None):
        dt = dt or self.data0.datetime.date(0)
        print("{}, {}".format(dt.isoformat(), txt))

    def __init__(self):
        ##close del primer dia del datafeed
        self.dataclose = self.data0.close
        ##Tracking de las ordenes
        self.order = None

        ##Agrego indicadores
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data0, period=self.params.long_period
        )

        self.small_sma = bt.indicators.SimpleMovingAverage(
            self.data0, period=self.params.small_period
        )
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            ##Si la orden queda colgando la cancelamos
            self.cancel(order)
        
        if order.status in [order.Completed]:
            if order.isbuy(): #es compra
                self.log(
                    "Se concreto la compra, Precio: {}, Costo: {}, Comm {}"
                    .format(order.executed.price, order.executed.value, order.executed.comm)
                )
            else: # es venta
                self.log(
                    "Se concreto la venta, Precio: {}, Costo: {}, Comm {}"
                    .format(order.executed.price, order.executed.value, order.executed.comm)
                )
            
            self.bar_executed = len(self)
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Orden cancelada o rechazada")         
        
        self.order = None
        
        
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
      
    def buy_signal(self):
        signal = False
        if self.small_sma[-1] and self.long_sma[-1]:
            signal = (self.long_sma[-1] > self.small_sma[-1]) and (self.small_sma[0] > self.long_sma[0])
        return signal
    
    def sell_signal(self):
        signal = False
        if self.small_sma[-1] and self.long_sma[-1]:
            signal = (self.small_sma[-1] > self.long_sma[-1]) and (self.long_sma[0] > self.small_sma[0])
        return signal
            
    def next(self):
        if not self.position: ##Si no hay una posicion tenemos tenencia del instrumento
            if self.buy_signal():
                ##Se da la condicion de compra
                self.log("Creada orden de compra: {}".format(self.dataclose[0]))
                self.order = self.buy()
                
        else:
            ##No tenemos instrumento podriamos comprar
            if self.sell_signal():
                self.log("Creada orden de venta, {}".format(self.dataclose[0]))
                self.sell()
                
if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(CrossStrategies)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../TSLA.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(1000.0)


    # Set the commission
    cerebro.broker.setcommission(commission=0.1)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()

    # Print out the final result