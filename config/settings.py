# config/settings.py
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings:
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    
    UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY", "")
    UPSTOX_API_SECRET = os.getenv("UPSTOX_API_SECRET", "")
    UPSTOX_REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI", "https://localhost:8000/callback")
    UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/nifty_brain.db")
    
    TRACKING_SYMBOLS = [
        'RELIANCE', 'HDFCBANK', 'ICICIBANK', 'INFY', 'AXISBANK',
        'TCS', 'KOTAKBANK', 'LT', 'SBIN', 'BAJFINANCE',
        'ITC', 'BHARTIARTL', 'HINDUNILVR', 'SUNPHARMA', 'MARUTI',
        'TITAN', 'ASIANPAINT', 'HCLTECH', 'WIPRO', 'NESTLE'
    ]
    
    NIFTY_WEIGHTS = {
        'HDFCBANK': 14.0, 'RELIANCE': 10.0, 'ICICIBANK': 8.0,
        'INFY': 6.0, 'TCS': 4.5, 'KOTAKBANK': 4.0, 'LT': 4.0,
        'SBIN': 3.5, 'ITC': 3.5, 'BAJFINANCE': 3.0, 'BHARTIARTL': 3.0,
        'AXISBANK': 2.5, 'HINDUNILVR': 2.5, 'SUNPHARMA': 2.0,
        'MARUTI': 2.0, 'TITAN': 1.8, 'ASIANPAINT': 1.8,
        'HCLTECH': 1.8, 'WIPRO': 1.5, 'NESTLE': 1.5
    }
    
    INSTRUMENT_KEYS = {
        'RELIANCE': 'NSE_EQ|INE002A01018',
        'HDFCBANK': 'NSE_EQ|INE040A01034',
        'ICICIBANK': 'NSE_EQ|INE090A01021',
        'INFY': 'NSE_EQ|INE009A01021',
        'AXISBANK': 'NSE_EQ|INE238A01034',
        'TCS': 'NSE_EQ|INE467B01029',
        'KOTAKBANK': 'NSE_EQ|INE237A01036',
        'LT': 'NSE_EQ|INE018A01030',
        'SBIN': 'NSE_EQ|INE062A01020',
        'BAJFINANCE': 'NSE_EQ|INE296A01032',
        'ITC': 'NSE_EQ|INE154A01025',
        'BHARTIARTL': 'NSE_EQ|INE397D01024',
        'HINDUNILVR': 'NSE_EQ|INE030A01027',
        'SUNPHARMA': 'NSE_EQ|INE044A01036',
        'MARUTI': 'NSE_EQ|INE585B01010',
        'TITAN': 'NSE_EQ|INE280A01028',
        'ASIANPAINT': 'NSE_EQ|INE021A01026',
        'HCLTECH': 'NSE_EQ|INE236A01020',
        'WIPRO': 'NSE_EQ|INE075A01022',
        'NESTLE': 'NSE_EQ|INE239A01024',
    }
    
    MARKET_OPEN = "09:15"
    MARKET_CLOSE = "15:30"
    RISK_FREE_RATE = 0.065
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))
    
    # Refresh intervals in seconds
    REFRESH_OPTIONS = [180, 300, 900]  # 3min, 5min, 15min
    DEFAULT_REFRESH = int(os.getenv("REFRESH_INTERVAL_SECONDS", 300))
    
    @property
    def REFRESH_INTERVAL(self):
        return self.DEFAULT_REFRESH

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)