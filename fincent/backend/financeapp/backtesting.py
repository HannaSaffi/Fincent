from io import BytesIO
import base64
import pandas as pd
import matplotlib.pyplot as plt
from financeapp.models import StockData
import sys
import os


def load_stock_data(symbol):
    """
    Loads stock data for a specific symbol from the database and returns it as a Pandas DataFrame.
    """
    stock_data = StockData.objects.filter(symbol=symbol).order_by('date')
    data = list(stock_data.values('date', 'close_price'))
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def calculate_moving_averages(df):
    """
    Calculates the 50-day and 200-day moving averages for the given DataFrame.
    """
    df['50_MA'] = df['close_price'].rolling(window=50).mean()
    df['200_MA'] = df['close_price'].rolling(window=200).mean()
    return df

def calculate_max_drawdown(df):
    """
    Calculates the maximum drawdown for a given price series.
    """
    df['cum_max'] = df['close_price'].cummax()
    df['drawdown'] = (df['close_price'] - df['cum_max']) / df['cum_max']
    max_drawdown = df['drawdown'].min()
    return max_drawdown

def simulate_trading_strategy(df, initial_investment=10000):
    """
    Simulates a trading strategy where:
    - Buy when the price is below the 50-day moving average.
    - Sell when the price is above the 200-day moving average.
    """
    cash = initial_investment
    stock = 0
    trades = []
    portfolio_values = []

    for i in range(len(df)):
        current_price = df['close_price'].iloc[i]
        fifty_ma = df['50_MA'].iloc[i]
        two_hundred_ma = df['200_MA'].iloc[i]

        # Skip rows where moving averages are NaN
        if pd.isna(fifty_ma) or pd.isna(two_hundred_ma):
            portfolio_values.append(cash + stock * current_price)
            continue

        # Buy condition
        if current_price < fifty_ma and stock == 0:
            stock = cash // current_price
            cash -= stock * current_price
            trades.append({'action': 'buy', 'date': df.index[i], 'price': current_price, 'shares': stock})

        # Sell condition
        elif current_price > two_hundred_ma and stock > 0:
            cash += stock * current_price
            trades.append({'action': 'sell', 'date': df.index[i], 'price': current_price, 'shares': stock})
            stock = 0

        # Record the portfolio value
        portfolio_values.append(cash + stock * current_price)

    # Calculate final metrics
    final_value = cash + (stock * df['close_price'].iloc[-1])
    total_return = (final_value - initial_investment) / initial_investment * 100
    max_drawdown = calculate_max_drawdown(df)
    num_trades = len(trades)

    return trades, final_value, total_return, max_drawdown, num_trades

def plot_backtest(df, trades):
    """
    Creates a plot of the backtest results and returns it as a base64-encoded string.
    """
    plt.figure(figsize=(14, 8))
    
    # Plot the stock price and moving averages
    plt.plot(df.index, df['close_price'], label='Close Price', color='blue')
    plt.plot(df.index, df['50_MA'], label='50-Day MA', color='orange', linestyle='--')
    plt.plot(df.index, df['200_MA'], label='200-Day MA', color='red', linestyle='--')
    
    # Plot buy and sell points
    for trade in trades:
        if trade['action'] == 'buy':
            plt.scatter(trade['date'], trade['price'], color='green', marker='^', label='Buy')
        elif trade['action'] == 'sell':
            plt.scatter(trade['date'], trade['price'], color='red', marker='v', label='Sell')

    plt.title('Backtesting Results')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    
    # Save plot to a buffer and encode it in base64
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return image_base64
