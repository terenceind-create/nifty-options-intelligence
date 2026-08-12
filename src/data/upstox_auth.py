# src/data/upstox_auth.py
import os
from loguru import logger
from dotenv import load_dotenv
import upstox_client
from upstox_client.rest import ApiException

load_dotenv()

class UpstoxAuth:
    """Upstox Authentication Manager with token expiry handling"""
    
    def __init__(self):
        self.api_key = os.getenv('UPSTOX_API_KEY')
        self.api_secret = os.getenv('UPSTOX_API_SECRET')
        self.redirect_uri = os.getenv('UPSTOX_REDIRECT_URI', 'https://localhost:8000/callback')
        self.access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
        
        if self.access_token:
            logger.debug(f"Token loaded: {self.access_token[:20]}...")
        else:
            logger.warning("No access token found")
        
        self.config = upstox_client.Configuration()
        if self.access_token:
            self.config.access_token = self.access_token
        self.api_client = upstox_client.ApiClient(self.config)
    
    def get_auth_url(self):
        """Get the authorization URL"""
        return (
            f"https://api.upstox.com/v2/login/authorization/dialog?"
            f"client_id={self.api_key}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code"
        )
    
    def generate_token_from_code(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            login_api = upstox_client.LoginApi()
            
            token_response = login_api.token(
                api_version='2.0',
                code=auth_code,
                client_id=self.api_key,
                client_secret=self.api_secret,
                redirect_uri=self.redirect_uri,
                grant_type='authorization_code'
            )
            
            if token_response and hasattr(token_response, 'access_token'):
                self.access_token = token_response.access_token
                self._save_token(token_response.access_token)
                self.config.access_token = self.access_token
                self.api_client = upstox_client.ApiClient(self.config)
                logger.success("✅ Token generated!")
                return self.access_token
            else:
                logger.error("Failed to get token")
                return None
                
        except ApiException as e:
            logger.error(f"API Error [{e.status}]: {e.body}")
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def _save_token(self, token):
        """Save token to .env file"""
        try:
            env_path = '.env'
            lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            
            with open(env_path, 'w') as f:
                token_found = False
                for line in lines:
                    if line.startswith('UPSTOX_ACCESS_TOKEN='):
                        f.write(f'UPSTOX_ACCESS_TOKEN={token}\n')
                        token_found = True
                    else:
                        f.write(line)
                if not token_found:
                    f.write(f'\nUPSTOX_ACCESS_TOKEN={token}\n')
            
            os.environ['UPSTOX_ACCESS_TOKEN'] = token
            self.access_token = token
            logger.info("💾 Token saved")
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    def get_profile(self):
        """Get user profile to verify token"""
        try:
            user_api = upstox_client.UserApi(self.api_client)
            profile = user_api.get_profile(api_version='2.0')
            if profile and hasattr(profile, 'data'):
                return profile.data
        except:
            pass
        return None
    
    def is_token_valid(self):
        """Check if current token is valid"""
        if not self.access_token:
            return False
        profile = self.get_profile()
        return profile is not None
    
    def ensure_valid_token(self):
        """
        Check token and prompt for re-authentication if expired.
        Returns True if token is valid (or was renewed), False if user skipped.
        """
        if self.is_token_valid():
            return True
        
        logger.warning("⚠️ Token expired or invalid!")
        print("\n" + "="*60)
        print("⚠️  UPSTOX TOKEN EXPIRED — RE-AUTHENTICATION REQUIRED")
        print("="*60)
        
        auto = input("\nAuto-regenerate token? (y/n): ").strip().lower()
        
        if auto == 'y':
            auth_url = self.get_auth_url()
            print(f"\n1. Open this URL:\n\n{auth_url}\n")
            print("2. Log in and authorize")
            print("3. Copy the FULL redirect URL from your browser\n")
            
            redirect_url = input("Paste redirect URL: ").strip()
            
            if 'code=' in redirect_url:
                auth_code = redirect_url.split('code=')[1].split('&')[0]
                token = self.generate_token_from_code(auth_code)
                
                if token:
                    print("✅ Token renewed successfully!")
                    return True
            
            print("❌ Failed to renew token")
            return False
        else:
            print("⚠️ Skipping authentication. Collector will not work.")
            return False