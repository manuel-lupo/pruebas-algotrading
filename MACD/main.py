import os.path
import backtrader as bt
import datetime
import sys

class GraficarMACD(bt.Strategy):
    params =(
        ('macd_period1', 12),
        ('macd_period2', 9),
        ('macd_sigperiod', 26),
        ('small_period', 50),
        ('long_period', 200)
    )
    
    def log(self, txt, dt=None):
        dt = dt or self.data0.datetime.date(0)
        print("{}, {}".format(dt.isoformat(), txt))
    
    def __init__(self):
        self.dataclose = self.data0.close
        
        self.macd = bt.indicators.MACD(
            self.data0,
            period_me1=self.params.macd_period1,
            period_signal=self.params.macd_sigperiod)
        
        self.rsi_inf = bt.indicators.RSI(self.data0)
        
        self.cross_ind = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
                
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
     ##Controlando que el valor del MACD sea menor a 0 en la compra y mayor a 0 en la venta los resultados muestran profit con menos trades negativos 
    def buy_signal(self):
        signal = False
        if self.small_sma[-1] and self.long_sma[-1]:
            signal= ((self.cross_ind == 1 and self.macd < 0) or ((self.long_sma[-1] > self.small_sma[-1]) and (self.small_sma[0] > self.long_sma[0]))and self.rsi_inf[0] >= 70)
        return signal
    
    def sell_signal(self):
        signal = False
        if self.small_sma[-1] and self.long_sma[-1]:
            signal= (((self.cross_ind == -1 and self.macd > 0) or ((self.long_sma[-1] < self.small_sma[-1]) and (self.small_sma[0] < self.long_sma[0]))) and self.rsi_inf[0] <= 30)
        return signal
            
    def next(self):
        if not self.position:
            if self.buy_signal():
                ##Se da la condicion de compra
                self.log("Creada orden de compra: {}".format(self.dataclose[0]))
                self.order = self.buy()
                
        else:
            ##No tenemos instrumento podriamos comprar
            if self.sell_signal():
                self.log("Creada orden de venta, {}".format(self.dataclose[0]))
                self.order = self.sell()

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    initial_cash= 10000

    # Add a strategy
    cerebro.addstrategy(GraficarMACD)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../DATA FEEDS/orcl-1995-2014.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(initial_cash)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addsizer(bt.sizers.PercentSizer, percents= 50)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()
    
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Final Cash Value: %.2f' % cerebro.broker.getcash())
    print('Portfolio profit percentage: {percentage}%'.format(percentage = ((cerebro.broker.getvalue()*100)-initial_cash)/initial_cash))
    print('Only cash profit percentage: {percentage}%'.format(percentage = ((cerebro.broker.getcash()*100)-initial_cash)/initial_cash))
    print('Yearly profit rate: {}%'.format((((cerebro.broker.getcash()*100)-initial_cash)/initial_cash)/20))
    cerebro.plot()