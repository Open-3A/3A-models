import os

import numpy as np
from django.http import JsonResponse

np.float_ = np.float64

import yfinance as yf
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt


class FinanceService:
    @staticmethod
    def get_dividend_history(ticker):
        stock = yf.Ticker(ticker)
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

        ticker_info = yf.Ticker(ticker).info
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

        info = yf.Ticker(ticker).info

        mean_price = info["targetMeanPrice"]
        current_price = info["currentPrice"]

        return mean_price if fair_value > current_price * 1.3 else fair_value

    @staticmethod
    def calculate_recommendation(current_price, intrinsic_value):
        return "COMPRAR" if current_price <= intrinsic_value else "AGUARDAR"

    @staticmethod
    def calculate_risk(ticker):
        data = yf.Ticker(ticker).history(period="5y")
        std_dev = np.std(data['Close'])

        # Normalize the risk to a scale of 0 to 100
        max_std_dev = 50  # Define a maximum standard deviation for scaling purposes
        risk = min(std_dev / max_std_dev * 100, 100)  # Ensure risk does not exceed 100

        return risk

    @staticmethod
    def calculate_safety_margin_price(current_price, intrinsic_value):
        return round((1 - current_price / intrinsic_value) * 100, 2)

    @staticmethod
    def plot_stock_history(ticker):
        # Cria a pasta 'assets' se não existir
        if not os.path.exists('assets'):
            os.makedirs('assets')

        # Obtém os dados históricos dos últimos 5 anos
        data = yf.Ticker(ticker).history(period="5y")

        # Cria o gráfico de linha
        plt.figure(figsize=(10, 6))
        plt.plot(data.index, data['Close'], label='Preço de Fechamento', color='blue')

        # Adiciona títulos e rótulos
        plt.title(f'Histórico de Preços de Fechamento - {ticker}')
        plt.xlabel('Data')
        plt.ylabel('Preço de Fechamento (R$)')
        plt.legend()
        plt.grid(True)

        # Salva o gráfico na pasta 'assets'
        file_path = os.path.join('assets', f'{ticker}_historico.png')
        plt.savefig(file_path)
        plt.close()

        return file_path


def ticker_info(request, ticker):
    ticker = f"{ticker}.SA"

    current_price = yf.Ticker(ticker).info["regularMarketPreviousClose"]
    intrinsic_value = FinanceService.calculate_fair_value(ticker)
    safety_margin = FinanceService.calculate_safety_margin_price(current_price, intrinsic_value)
    risk = FinanceService.calculate_risk(ticker)
    recommendation = FinanceService.calculate_recommendation(current_price, intrinsic_value)

    response_data = {
        'current_price': round(current_price, 2),
        'intrinsic_value': round(intrinsic_value, 2),
        'safety_margin': safety_margin,
        'risk': round(risk, 2),
        'recommendation': recommendation,
    }

    FinanceService.plot_stock_history(ticker)

    return JsonResponse(response_data)
