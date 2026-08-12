# get_token.py
"""
Get Upstox Access Token
Uses SDK v2.28.0 token() method
"""
import os
from dotenv import load_dotenv
from src.data.upstox_auth import UpstoxAuth

load_dotenv()

def main():
    print("\n" + "="*60)
    print("🔑 UPSTOX TOKEN GENERATOR (SDK v2.28.0)")
    print("="*60)
    
    # Check if API credentials exist
    api_key = os.getenv('UPSTOX_API_KEY')
    api_secret = os.getenv('UPSTOX_API_SECRET')
    
    if not api_key or not api_secret:
        print("\n❌ API credentials not found in .env file!")
        print("Please add UPSTOX_API_KEY and UPSTOX_API_SECRET to your .env file")
        print("\nGet them from: https://upstox.com/developer/apps")
        return
    
    print(f"\n✅ API Key found: {api_key[:10]}...")
    
    # Initialize auth
    auth = UpstoxAuth()
    
    # Get authorization URL
    auth_url = auth.get_auth_url()
    
    if auth_url:
        print("\n" + "-"*60)
        print("STEP 1: Authorize the Application")
        print("-"*60)
        print("\n1️⃣  Open this URL in your browser:")
        print(f"\n   {auth_url}\n")
        
        print("2️⃣  Log in to your Upstox account")
        print("3️⃣  Click 'Authorize'")
        print("4️⃣  You'll be redirected to a page that may say 'This site can't be reached'")
        print("    → This is NORMAL (we're not running a server on localhost:8000)")
        print("5️⃣  Copy the ENTIRE URL from your browser's address bar\n")
        
        redirect_url = input("📋 Paste the full redirect URL here: ").strip()
        
        # Extract authorization code from URL
        if 'code=' in redirect_url:
            auth_code = redirect_url.split('code=')[1].split('&')[0]
            
            print(f"\n✅ Authorization code extracted: {auth_code[:10]}...")
            print("\n" + "-"*60)
            print("STEP 2: Exchange Code for Token")
            print("-"*60)
            print("\n🔄 Requesting access token...")
            
            token = auth.generate_token_from_code(auth_code)
            
            if token:
                print(f"\n✅ SUCCESS! Access token generated")
                print(f"   Token: {token[:20]}...")
                print(f"   Token saved to .env file")
                
                # Test the token
                print("\n" + "-"*60)
                print("STEP 3: Verify Connection")
                print("-"*60)
                print("\n🔄 Testing connection...")
                
                profile = auth.get_profile()
                if profile:
                    print(f"✅ Connected to Upstox successfully!")
                    print(f"   User: {profile.user_name}")
                    print(f"   Email: {profile.email}")
                    print(f"\n🎉 You're all set! Run 'python run_collector.py' to start live data collection")
                else:
                    print("⚠️ Token generated but connection test failed")
                    print("   Try running 'python run_collector.py' anyway")
            else:
                print("\n❌ Failed to generate access token")
                print("   Check that your API Secret is correct in .env file")
        else:
            print("\n❌ Could not find authorization code in URL")
            print("   Make sure the URL contains 'code=' parameter")
            print(f"   Your URL: {redirect_url[:50]}...")
    else:
        print("\n❌ Failed to generate authorization URL")

if __name__ == "__main__":
    main()