# test_prices.py
from src.data.upstox_auth import UpstoxAuth
from upstox_client import MarketQuoteApi
from config.settings import settings

auth = UpstoxAuth()
api = MarketQuoteApi(auth.api_client)

keys = ','.join(settings.INSTRUMENT_KEYS.values())
r = api.ltp(symbol=keys, api_version='2.0')

for k, v in r.data.items():
    if hasattr(v, 'last_price'):
        price = v.last_price
    elif isinstance(v, dict):
        price = v.get('last_price', 0)
    else:
        price = 0
    print(f'{k}: Rs{price}')