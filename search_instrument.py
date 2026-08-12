# search_instrument.py
from src.data.upstox_auth import UpstoxAuth
import upstox_client

auth = UpstoxAuth()
api = upstox_client.InstrumentsApi(auth.api_client)

# Search for Reliance equity
response = api.get_instruments()
print(type(response))
print(response)