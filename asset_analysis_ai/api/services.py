import numpy as np

np.float_ = np.float64

import yfinance as yf
from prophet import Prophet
import pandas as pd


class FinanceService:
    @staticmethod
    def get_dividend_history(ticker):
        stock = yf.Ticker(ticker.strip() + ".SA")
        dividends = stock.dividends

        if dividends.empty:
            return pd.DataFrame(columns=['date', 'dividend'])

        dividends = dividends.reset_index()
        dividends.columns = ['date', 'dividend']
        dividends['date'] = pd.to_datetime(dividends['date']).dt.tz_localize(None)

        return dividends

    @staticmethod
    def get_average_annual_return(index_ticker='^BVSP', period='10y'):
        index_data = yf.Ticker(index_ticker).history(period=period)

        index_data['Year'] = index_data.index.year
        annual_mean = index_data.groupby('Year')['Close'].mean()
        average_annual_return = annual_mean.pct_change().mean()

        return average_annual_return

    @staticmethod
    def get_dividend_growth_rate(ticker):
        dividends = FinanceService.get_dividend_history(ticker)
        dividends.columns = ['ds', 'y']

        model = Prophet(growth='linear', yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(dividends)

        future = model.make_future_dataframe(periods=1, freq='YE')
        forecast = model.predict(future)

        annual_forecast = forecast.groupby(pd.Grouper(key='ds', freq='YE')).sum()['yhat']
        growth_rate = annual_forecast[annual_forecast > 0].pct_change().median()

        new_dividends = forecast[['ds', 'yhat']]
        new_dividends.columns = ['date', 'dividend']

        return new_dividends, growth_rate

    @staticmethod
    def calculate_coe(ticker):
        market_return = FinanceService.get_average_annual_return()
        risk_free_rate = 0.03
        market_risk_premium = market_return - risk_free_rate

        ticker_info = yf.Ticker(ticker.strip() + ".SA").info
        beta = ticker_info.get("beta", 1)  # Use 1 as default if beta is not available

        coe = round(beta * market_risk_premium + risk_free_rate, 4)
        return coe

    @staticmethod
    def calculate_fair_value(ticker):
        coe = FinanceService.calculate_coe(ticker)
        dividends, dividend_growth_rate = FinanceService.get_dividend_growth_rate(ticker)

        current_date = dividends['date'].max()
        filter_last_12_months = (dividends['date'] >= current_date - pd.DateOffset(months=12))
        last_12_months_dividends = dividends[filter_last_12_months]

        total_dividends_last_12_months = last_12_months_dividends['dividend'].sum()

        fair_value = total_dividends_last_12_months * (1 + dividend_growth_rate) / abs(coe - dividend_growth_rate)

        return fair_value
