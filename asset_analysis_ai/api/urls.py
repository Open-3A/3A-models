from django.urls import path
from .views import get_dividend_history, get_average_annual_return, get_dividend_growth_rate, calculate_coe, calculate_fair_value

urlpatterns = [
    path('dividends/<str:ticker>/', get_dividend_history, name='get_dividend_history'),
    path('average-annual-return/', get_average_annual_return, name='get_average_annual_return'),
    path('dividend-growth-rate/<str:ticker>/', get_dividend_growth_rate, name='get_dividend_growth_rate'),
    path('coe/<str:ticker>/', calculate_coe, name='calculate_coe'),
    path('fair-value/<str:ticker>/', calculate_fair_value, name='calculate_fair_value'),
]
