# src/utils/nifty_chart.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from loguru import logger
import upstox_client
from src.data.upstox_auth import UpstoxAuth


class NiftyChartData:
    """Fetch and process Nifty 50 intraday data with indicators"""
    
    NIFTY_KEY = "NSE_INDEX|Nifty 50"
    
    def __init__(self):
        self.auth = UpstoxAuth()
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def get_intraday_candles(self, interval='1minute'):
        """Get today's intraday candles"""
        try:
            api = upstox_client.HistoryApi(self.auth.api_client)
            response = api.get_intra_day_candle_data(
                instrument_key=self.NIFTY_KEY,
                interval=interval,
                api_version='2.0'
            )
            if hasattr(response, 'data') and response.data:
                return response.data.candles
            return []
        except Exception as e:
            logger.error(f"Nifty chart error: {e}")
            return []
    
    def get_today_candles_df(self):
        """Get today's 1-minute candles resampled to 5-min with indicators"""
        candles = self.get_intraday_candles('1minute')
        
        if not candles:
            return pd.DataFrame()
        
        # Parse candles
        rows = []
        for candle in candles:
            if len(candle) >= 5:
                rows.append({
                    'timestamp': pd.to_datetime(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                })
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Resample to 5-minute
        df_5min = df.resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        # Calculate 20 EMA
        df_5min['EMA_20'] = df_5min['close'].ewm(span=20, adjust=False).mean()
        
        # Calculate Pivot Points (Classic Floor Pivots)
        df_5min = self._add_pivot_points(df_5min)
        
        # Calculate Fibonacci Pivot Levels
        df_5min = self._add_fibonacci_pivots(df_5min)
        
        return df_5min
    
    def _add_pivot_points(self, df):
        """Add daily pivot points (recalculates each day)"""
        if df.empty:
            return df
        
        # Get yesterday's high, low, close for pivot calculation
        # For intraday, use previous day's data
        today = df.index[0].date()
        yesterday_data = df[df.index.date < today]
        
        if not yesterday_data.empty:
            prev_high = yesterday_data['high'].max()
            prev_low = yesterday_data['low'].min()
            prev_close = yesterday_data['close'].iloc[-1]
        else:
            # Use first candle data as fallback
            prev_high = df['high'].iloc[0]
            prev_low = df['low'].iloc[0]
            prev_close = df['close'].iloc[0]
        
        # Classic Pivot Point formula
        pivot = (prev_high + prev_low + prev_close) / 3
        
        df['Pivot'] = pivot
        df['R1'] = (2 * pivot) - prev_low
        df['R2'] = pivot + (prev_high - prev_low)
        df['R3'] = prev_high + 2 * (pivot - prev_low)
        df['S1'] = (2 * pivot) - prev_high
        df['S2'] = pivot - (prev_high - prev_low)
        df['S3'] = prev_low - 2 * (prev_high - pivot)
        
        return df
    
    def _add_fibonacci_pivots(self, df):
        """Add Fibonacci pivot levels"""
        if df.empty:
            return df
        
        today = df.index[0].date()
        yesterday_data = df[df.index.date < today]
        
        if not yesterday_data.empty:
            prev_high = yesterday_data['high'].max()
            prev_low = yesterday_data['low'].min()
        else:
            prev_high = df['high'].iloc[0]
            prev_low = df['low'].iloc[0]
        
        # Range
        range_val = prev_high - prev_low
        
        # Fibonacci Pivot Point
        fib_pivot = (prev_high + prev_low + df['close'].iloc[-1]) / 3
        
        df['Fib_Pivot'] = fib_pivot
        
        # Fibonacci Resistance Levels
        df['Fib_R1'] = fib_pivot + (range_val * 0.382)
        df['Fib_R2'] = fib_pivot + (range_val * 0.618)
        df['Fib_R3'] = fib_pivot + (range_val * 1.000)
        df['Fib_R4'] = fib_pivot + (range_val * 1.382)
        
        # Fibonacci Support Levels
        df['Fib_S1'] = fib_pivot - (range_val * 0.382)
        df['Fib_S2'] = fib_pivot - (range_val * 0.618)
        df['Fib_S3'] = fib_pivot - (range_val * 1.000)
        df['Fib_S4'] = fib_pivot - (range_val * 1.382)
        
        return df
    
    def get_latest_nifty_price(self):
        """Get current Nifty spot price"""
        try:
            api = upstox_client.MarketQuoteApi(self.auth.api_client)
            response = api.ltp(symbol=self.NIFTY_KEY, api_version='2.0')
            if hasattr(response, 'data') and response.data:
                for key, data in response.data.items():
                    if isinstance(data, dict):
                        return data.get('last_price', 0)
                    return getattr(data, 'last_price', 0)
        except:
            pass
        return None


# Global instance
nifty_chart = NiftyChartData()