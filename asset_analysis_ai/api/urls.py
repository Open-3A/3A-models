from django.urls import path

from .services import ticker_info
from .views import calculate_fair_value

urlpatterns = [
    path('fair-value/<str:ticker>/', calculate_fair_value, name='calculate_fair_value'),
    path('ticker/<str:ticker>/', ticker_info, name='ticker_info'),
]
