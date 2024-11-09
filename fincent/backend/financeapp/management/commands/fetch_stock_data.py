# financeapp/management/commands/fetch_stock_data.py

import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from financeapp.models import StockData
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch stock data from Alpha Vantage API and store it in the database'

    def add_arguments(self, parser):
        parser.add_argument('symbol', type=str, help='Stock symbol to fetch data for (e.g., AAPL)')
        parser.add_argument('--verbose', action='store_true', help='Enable verbose output for each saved entry')

    def handle(self, *args, **kwargs):
        symbol = kwargs['symbol']
        verbose = kwargs['verbose']
        api_key = settings.ALPHA_VANTAGE_API_KEY
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}'

        max_retries = 3  # Set the maximum number of retries
        retry_delay = 5  # Delay in seconds between retries
        wait_time_if_limited = 60  # Wait time (in seconds) if API rate limit is reached

        for attempt in range(max_retries):
            try:
                response = requests.get(url)
                data = response.json()

                # Check for rate limit message
                if 'Note' in data:
                    self.stdout.write(self.style.WARNING("API rate limit reached. Waiting before retrying..."))
                    time.sleep(wait_time_if_limited)
                    continue

                # Check for expected 'Time Series (Daily)' data
                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    for date_str, daily_data in time_series.items():
                        try:
                            date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            StockData.objects.update_or_create(
                                symbol=symbol,
                                date=date,
                                defaults={
                                    'open_price': float(daily_data['1. open']),
                                    'high_price': float(daily_data['2. high']),
                                    'low_price': float(daily_data['3. low']),
                                    'close_price': float(daily_data['4. close']),
                                    'volume': int(daily_data['5. volume']),
                                }
                            )
                            if verbose:
                                self.stdout.write(self.style.SUCCESS(f"Saved data for {symbol} on {date}"))
                        except (ValueError, KeyError) as e:
                            self.stdout.write(self.style.ERROR(f"Data validation error for {symbol} on {date_str}: {e}"))
                            continue

                    self.stdout.write(self.style.SUCCESS(f"Successfully fetched and saved data for {symbol}"))
                    break  # Exit loop if successful

                else:
                    # Log detailed response for unknown errors
                    error_message = data.get("Error Message", "Unknown error")
                    self.stdout.write(self.style.ERROR(f"Error fetching data: {error_message}. Full response: {data}"))
                    break  # Exit loop on unrecoverable error

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network error: {e}. Retrying in {retry_delay} seconds..."))
                time.sleep(retry_delay)  # Wait before retrying

        else:
            # If the loop completes without success
            self.stdout.write(self.style.ERROR("Failed to fetch data after multiple attempts."))
