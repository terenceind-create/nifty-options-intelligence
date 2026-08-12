# src/data/upstox_auth.py
import os
from loguru import logger
from dotenv import load_dotenv
import upstox_client
from upstox_client.rest import ApiException

# Load .env file first
load_dotenv()

class UpstoxAuth:
    """Upstox Authentication Manager"""
    
    def __init__(self):
        # Load from environment
        self.api_key = os.getenv('UPSTOX_API_KEY')
        self.api_secret = os.getenv('UPSTOX_API_SECRET')
        self.redirect_uri = os.getenv('UPSTOX_REDIRECT_URI', 'https://localhost:8000/callback')
        self.access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
        
        # Debug token status
        if self.access_token:
            logger.debug(f"Token loaded: {self.access_token[:20]}...")
        else:
            logger.warning("No access token found in environment")
        
        # Create configuration with token
        self.config = upstox_client.Configuration()
        if self.access_token:
            self.config.access_token = self.access_token
        
        # Create API client
        self.api_client = upstox_client.ApiClient(self.config)
    
    def get_auth_url(self):
        """Get the authorization URL"""
        auth_url = (
            f"https://api.upstox.com/v2/login/authorization/dialog?"
            f"client_id={self.api_key}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code"
        )
        logger.info("🔗 Authorization URL generated")
        return auth_url
    
    def generate_token_from_code(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            login_api = upstox_client.LoginApi()
            
            logger.info("🔄 Requesting access token from Upstox...")
            
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
                
                # Save to .env
                self._save_token_to_env(self.access_token)
                
                # Update configuration
                self.config.access_token = self.access_token
                self.api_client = upstox_client.ApiClient(self.config)
                
                logger.success("✅ Access token generated successfully!")
                return self.access_token
            else:
                logger.error(f"Unexpected response: {token_response}")
                return None
                
        except ApiException as e:
            logger.error(f"API Error [{e.status}]: {e.body}")
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def _save_token_to_env(self, token):
        """Save access token to .env file"""
        try:
            env_path = '.env'
            
            # Read existing .env
            lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            
            # Update or add token
            token_found = False
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('UPSTOX_ACCESS_TOKEN='):
                        f.write(f'UPSTOX_ACCESS_TOKEN={token}\n')
                        token_found = True
                    else:
                        f.write(line)
                
                if not token_found:
                    f.write(f'\nUPSTOX_ACCESS_TOKEN={token}\n')
            
            # Update environment
            os.environ['UPSTOX_ACCESS_TOKEN'] = token
            self.access_token = token
            
            logger.info("💾 Token saved to .env file")
            
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    def get_profile(self):
        """Get user profile to verify token"""
        try:
            user_api = upstox_client.UserApi(self.api_client)
            profile = user_api.get_profile(api_version='2.0')
            
            if profile and hasattr(profile, 'data'):
                user_data = profile.data
                logger.success(f"✅ Connected as: {user_data.user_name}")
                return user_data
            else:
                logger.error("Could not get profile data")
                return None
                
        except Exception as e:
            logger.error(f"Profile error: {e}")
            return None
    
    def is_token_valid(self):
        """Check if token is valid"""
        if not self.access_token:
            logger.error("No access token available")
            return False
        
        profile = self.get_profile()
        return profile is not None