import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime

class EMATrendRSIStrategy(bt.Strategy):
    params = dict(
        trend_period=200,
        entry_period=50,
        rsi_period=14,
        atr_period=14,
        atr_mult=3.0,
        risk_per_trade=0.01,
        target1=2.0,
        target2=4.0,
    )

    def __init__(self):
        self.h1 = self.datas[0]
        self.d1 = self.datas[1]

        self.daily_ema = bt.ind.EMA(self.d1.close, period=self.p.trend_period)
        self.hourly_ema = bt.ind.EMA(self.h1.close, period=self.p.entry_period)
        self.hourly_atr = bt.ind.ATR(self.h1, period=self.p.atr_period)
        self.daily_atr = bt.ind.ATR(self.d1, period=self.p.atr_period)
        self.rsi = bt.ind.RSI(self.h1.close, period=self.p.rsi_period)

        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.at_target1 = False

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.stop_price = self.entry_price - self.p.atr_mult * self.hourly_atr[0]
            elif order.issell():
                self.entry_price = None
                self.stop_price = None
                self.at_target1 = False
        self.order = None

    def next(self):
        trend = self.d1.close[0] > self.daily_ema[0]
        price_above_ema = self.h1.close[0] > self.hourly_ema[0]
        volatility_ok = self.daily_atr[0] / self.d1.close[0] > 0.008
        rsi_ok = self.rsi[0] < 70

        if not self.position:
            if self.order is None and trend and price_above_ema and volatility_ok and rsi_ok:
                risk_value = self.broker.getvalue() * self.p.risk_per_trade
                risk_per_share = self.p.atr_mult * self.hourly_atr[0]
                if risk_per_share > 0:
                    size = risk_value / risk_per_share
                    self.order = self.buy(size=size)
        else:
            cp = self.h1.close[0]
            if self.stop_price is not None and cp <= self.stop_price:
                self.close()
            else:
                if (
                    self.entry_price is not None
                    and not self.at_target1
                    and cp >= self.entry_price + self.p.target1 * self.hourly_atr[0]
                ):
                    self.sell(size=self.position.size / 2)
                    self.at_target1 = True
                    self.stop_price = self.entry_price
                if self.at_target1:
                    self.stop_price = max(self.stop_price, cp - self.p.atr_mult * self.hourly_atr[0])
                if (
                    self.entry_price is not None
                    and cp >= self.entry_price + self.p.target2 * self.hourly_atr[0]
                ):
                    self.close()

    def stop(self):
        print(f'Final value: {self.broker.getvalue():.2f}')


def fetch_data(symbol, start, end, interval):
    df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df


def main():
    start = '2024-01-01'
    end = '2025-12-31'

    hourly = fetch_data('AAVE-USD', start, end, '1h')
    daily = fetch_data('AAVE-USD', start, end, '1d')
    if hourly.empty or daily.empty:
        print('No data downloaded')
        return

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000)
    cerebro.broker.setcommission(commission=0.001)

    hourly_feed = bt.feeds.PandasData(dataname=hourly, timeframe=bt.TimeFrame.Minutes, compression=60)
    daily_feed = bt.feeds.PandasData(dataname=daily, timeframe=bt.TimeFrame.Days)

    cerebro.adddata(hourly_feed)
    cerebro.adddata(daily_feed)
    cerebro.addstrategy(EMATrendRSIStrategy)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    results = cerebro.run()
    strat = results[0]
    print('Sharpe ratio:', strat.analyzers.sharpe.get_analysis().get('sharperatio'))
    ta = strat.analyzers.trades.get_analysis()
    total_trades = ta.get('total', {}).get('closed', 0)
    print('Total trades:', total_trades)

if __name__ == '__main__':
    main()
