# find_all_keys.py
from src.data.upstox_auth import UpstoxAuth
import upstox_client

auth = UpstoxAuth()
api = upstox_client.InstrumentsApi(auth.api_client)

stocks_to_find = {
    'RELIANCE': 'RELIANCE INDUSTRIES LTD',
    'HDFCBANK': 'HDFC BANK LTD',
    'ICICIBANK': 'ICICI BANK LTD',
    'INFY': 'INFOSYS LTD',
    'AXISBANK': 'AXIS BANK LTD'
}

print("Finding instrument keys for all 5 stocks...\n")

for symbol, full_name in stocks_to_find.items():
    response = api.search_instrument(query=symbol)
    
    if response and hasattr(response, 'data'):
        results = response.data
        
        # Find the NSE equity match
        for item in results:
            if (item.get('segment') == 'NSE_EQ' and 
                item.get('name', '').upper().startswith(full_name.split(' LTD')[0])):
                print(f"{symbol}: {item.get('instrument_key')}")
                print(f"  Name: {item.get('name')}")
                print(f"  Exchange: {item.get('exchange')}, Segment: {item.get('segment')}")
                print()
                break