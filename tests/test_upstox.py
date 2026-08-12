# tests/test_upstox.py
from src.data.upstox_auth import UpstoxAuthenticator
from config.settings import settings

def test_connection():
    """Test Upstox API connection"""
    auth = UpstoxAuthenticator()
    
    if not auth.access_token:
        print("No access token found. Running authentication flow...")
        auth.generate_access_token()
    
    if auth.initialize_client():
        print("\n✅ Upstox client ready!")
        
        # Test fetching data for Reliance
        print("\nFetching Reliance data...")
        data = auth.get_live_data('RELIANCE')
        
        if data:
            print(f"✅ Data received!")
            print(f"   Option chain available: {data['option_chain'] is not None}")
            print(f"   Live quote available: {data['quote'] is not None}")
        else:
            print("❌ Failed to fetch data")
    else:
        print("❌ Client initialization failed")

if __name__ == "__main__":
    test_connection()