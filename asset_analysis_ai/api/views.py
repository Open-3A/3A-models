from django.http import JsonResponse
from rest_framework.decorators import api_view

from .services import FinanceService


@api_view(['GET'])
def get_dividend_history(request, ticker):
    dividends = FinanceService.get_dividend_history(ticker)

    if dividends.empty:
        return JsonResponse({'message': 'No dividends data found.'}, status=404)

    dividends_data = dividends.to_dict(orient='records')
    return JsonResponse(dividends_data, safe=False)


@api_view(['GET'])
def get_average_annual_return(request):
    average_annual_return = FinanceService.get_average_annual_return()
    return JsonResponse({'average_annual_return': average_annual_return})


@api_view(['GET'])
def get_dividend_growth_rate(request, ticker):
    dividends, growth_rate = FinanceService.get_dividend_growth_rate(ticker)
    new_dividends_data = dividends.to_dict(orient='records')
    return JsonResponse({'new_dividends': new_dividends_data, 'growth_rate': growth_rate})


@api_view(['GET'])
def calculate_coe(request, ticker):
    coe = FinanceService.calculate_coe(ticker)
    return JsonResponse({'coe': coe})


@api_view(['GET'])
def calculate_fair_value(request, ticker):
    fair_value = FinanceService.calculate_fair_value(ticker)
    return JsonResponse({'fair_value': fair_value})
