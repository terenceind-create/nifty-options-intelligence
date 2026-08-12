# find_instruments.py
from src.data.upstox_auth import UpstoxAuth
import upstox_client
import json

auth = UpstoxAuth()
api = upstox_client.InstrumentsApi(auth.api_client)

print("Searching for RELIANCE...")
response = api.search_instrument(query='RELIANCE')

if response and hasattr(response, 'data'):
    results = response.data
    print(f"Found {len(results)} results\n")
    
    for item in results[:5]:
        # It's a dict
        print(f"Instrument Key: {item.get('instrument_key')}")
        print(f"Trading Symbol: {item.get('tradingsymbol')}")
        print(f"Name: {item.get('name')}")
        print(f"Exchange: {item.get('exchange')}")
        print(f"Segment: {item.get('segment')}")
        print(f"Type: {item.get('instrument_type')}")
        print("-" * 40)