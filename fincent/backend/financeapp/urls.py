# financeapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('backtest-report/<str:symbol>/', views.generate_backtest_report, name='backtest_report'),
    path('fetch-data/<str:symbol>/', views.fetch_data_view, name='fetch_data'),
    path('backtest/<str:symbol>/', views.backtest_view, name='backtest'),
    path('backtest/<str:symbol>/<int:initial_investment>/', views.backtest_view, name='backtest_with_investment'),
    path('predict/', views.predict_and_store_prices, name='predict_stock_price'),
    path('predict/<str:symbol>/', views.predict_and_store_prices, name='predict_and_store_prices'),
    path('backtest-report-pdf/<str:symbol>/', views.generate_pdf_report, name='backtest_report_pdf')

]
