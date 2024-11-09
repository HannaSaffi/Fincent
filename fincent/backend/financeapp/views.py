# financeapp/views.py
import weasyprint
from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import requests
import os
import joblib
import numpy as np
import json
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from .models import StockData, PredictedStockData
import pandas as pd
from .backtesting import load_stock_data, calculate_moving_averages, simulate_trading_strategy, plot_backtest

# Set Matplotlib to use the Agg backend
plt.switch_backend('Agg')


def fetch_stock_data(symbol):
    """
    Fetches stock data from Alpha Vantage API and updates or creates entries in the StockData model.
    """
    api_key = settings.ALPHA_VANTAGE_API_KEY  # Ensure this is set in your .env file
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}'

    response = requests.get(url)
    data = response.json()

    # Check if response contains the time series data
    if 'Time Series (Daily)' in data:
        time_series = data['Time Series (Daily)']
        for date, daily_data in time_series.items():
            StockData.objects.update_or_create(
                symbol=symbol,
                date=date,
                defaults={
                    'open_price': daily_data['1. open'],
                    'high_price': daily_data['2. high'],
                    'low_price': daily_data['3. low'],
                    'close_price': daily_data['4. close'],
                    'volume': daily_data['6. volume'],
                }
            )
    else:
        print("Error fetching data:", data.get("Error Message", "Unknown error"))

def fetch_data_view(request, symbol):
    """
    API view to fetch stock data for a specific symbol.
    """
    fetch_stock_data(symbol)
    return JsonResponse({"status": "Data fetched successfully"})

def backtest_view(request, symbol, initial_investment=10000):
    """
    API view to run backtesting on stock data for a specific symbol.
    """
    # Load and process the data
    df = load_stock_data(symbol)
    df = calculate_moving_averages(df)

    # Run the backtesting strategy
    trades, final_value, total_return, max_drawdown, num_trades = simulate_trading_strategy(df, initial_investment)

    # Prepare the response data
    result = {
        "symbol": symbol,
        "initial_investment": initial_investment,
        "final_value": f"{final_value:.2f}",
        "total_return": f"{total_return:.2f}%",
        "max_drawdown": f"{max_drawdown:.2f}%",
        "num_trades": num_trades,
        "trades": trades
    }
    return JsonResponse(result)

def load_model():
    """
    Loads the pre-trained model from a .pkl file.
    """
    # Correct path to stock_price_model.pkl directly within financeapp
    model_path = os.path.join(settings.BASE_DIR, 'financeapp', 'stock_price_model.pkl')
    model = joblib.load(model_path)
    return model
def backtest_report_view(request, symbol, initial_investment=10000):
    """
    API view that generates a backtest report with a plot of the stock price and buy/sell points.
    """
    # Load data and run backtest
    df = load_stock_data(symbol)
    df = calculate_moving_averages(df)
    trades, final_value, total_return, max_drawdown, num_trades = simulate_trading_strategy(df, initial_investment)

    # Generate plot
    plot_image = plot_backtest(df, trades)

    # Prepare response data
    report_data = {
        "symbol": symbol,
        "initial_investment": initial_investment,
        "final_value": f"{final_value:.2f}",
        "total_return": f"{total_return:.2f}%",
        "max_drawdown": f"{max_drawdown:.2f}%",
        "num_trades": num_trades,
        "trades": trades,
        "plot_image": plot_image,  # Encoded plot image
    }
    return JsonResponse(report_data)

@csrf_exempt
def generate_backtest_report(request, symbol, initial_investment=10000):
    """
    API view to generate a performance report with visualizations for backtesting results.
    """
    # Load stock data and perform backtesting
    df = load_stock_data(symbol)
    df = calculate_moving_averages(df)
    trades, final_value, total_return, max_drawdown, num_trades = simulate_trading_strategy(df, initial_investment)

    # Plot the backtest results
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.plot(df.index, df['close_price'], label='Close Price', color='blue')
    ax.plot(df.index, df['50_MA'], label='50-Day MA', color='orange', linestyle='--')
    ax.plot(df.index, df['200_MA'], label='200-Day MA', color='red', linestyle='--')

    for trade in trades:
        if trade['action'] == 'buy':
            ax.plot(trade['date'], trade['price'], marker='^', color='green', label='Buy')
        elif trade['action'] == 'sell':
            ax.plot(trade['date'], trade['price'], marker='v', color='red', label='Sell')

    ax.set_title(f"Backtest Report for {symbol}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()

    # Save the plot to an in-memory buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    # Send the plot as an HTTP response
    return HttpResponse(buffer, content_type='image/png')
@csrf_exempt
def predict_and_store_prices(request, symbol):
    """
    API view to predict stock prices for the next 30 days and store them.
    """
    if request.method == "POST":
        try:
            # Load the model
            model = load_model()

            # Predict and store prices for the next 30 days
            today = datetime.today()
            predictions = []
            
            for day in range(1, 31):
                # Prepare input for prediction with the correct feature name
                X_new = pd.DataFrame([[day]], columns=["day"])  # Match the training feature name
                predicted_price = model.predict(X_new)[0]

                # Calculate the date for the prediction
                prediction_date = today + timedelta(days=day)

                # Store the prediction in the database
                PredictedStockData.objects.update_or_create(
                    symbol=symbol,
                    date=prediction_date,
                    defaults={'predicted_close_price': round(predicted_price, 2)}
                )

                # Append the prediction result for the response
                predictions.append({
                    "date": prediction_date.strftime("%Y-%m-%d"),
                    "predicted_price": round(predicted_price, 2)
                })

            # Return the predictions in the response
            return JsonResponse({
                "symbol": symbol,
                "predictions": predictions
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
def generate_pdf_report(request, symbol):
    # Load stock data and calculate moving averages
    df = load_stock_data(symbol)
    df = calculate_moving_averages(df)

    # Run the backtesting strategy to get trades and metrics
    trades, final_value, total_return, max_drawdown, num_trades = simulate_trading_strategy(df)

    # Render the HTML content
    html_content = render_to_string('financeapp/report_template.html', {
        'symbol': symbol,
        'final_value': final_value,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades,
        'trades': trades,
        'df': df
    })

    # Generate the PDF using WeasyPrint
    pdf_file = weasyprint.HTML(string=html_content).write_pdf()

    # Return the PDF as an HTTP response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{symbol}_backtest_report.pdf"'
    return response

