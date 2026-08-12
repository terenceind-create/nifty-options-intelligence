# test_ltp.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()

token = os.getenv('UPSTOX_ACCESS_TOKEN')
print(f"Token: {token[:30]}...")

# Try different symbol formats
symbols_to_try = [
    "RELIANCE",
    "NSE_EQ:RELIANCE", 
    "BSE_EQ:RELIANCE",
    "NSE_FO:RELIANCE",
    "RELIANCE-EQ"
]

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

for symbol in symbols_to_try:
    url = f'https://api.upstox.com/v2/market-quote/ltp?symbol={symbol}'
    r = requests.get(url, headers=headers)
    print(f"\n{symbol}: HTTP {r.status_code}")
    if r.status_code == 200:
        print(f"  ✅ SUCCESS: {r.json()}")
        break
    else:
        print(f"  ❌ {r.text[:100]}")