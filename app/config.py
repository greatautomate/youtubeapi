import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
    API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # YouTube API Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    
    # Google Credentials - Individual components (legacy support)
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    
    # Google Credentials - Full JSON (preferred)
    GOOGLE_CLIENT_SECRET_JSON = os.getenv('GOOGLE_CLIENT_SECRET_JSON', '')
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    
    # File Paths
    BASE_DIR = Path(__file__).parent.parent
    CREDENTIALS_DIR = BASE_DIR / 'credentials'
    SESSION_DIR = BASE_DIR / 'session'
    TEMP_DIR = BASE_DIR / 'temp'
    
    # Credential files (created from env vars)
    CLIENT_SECRET_FILE = CREDENTIALS_DIR / 'client_secret.json'
    SERVICE_ACCOUNT_FILE = CREDENTIALS_DIR / 'service_account.json'
    TOKEN_FILE = CREDENTIALS_DIR / 'token.json'
    
    # Upload Settings
    YOUTUBE_PRIVACY_STATUS = os.getenv('YOUTUBE_PRIVACY_STATUS', 'unlisted')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 2 * 1024 * 1024 * 1024))  # 2GB
    MAX_VIDEO_DURATION = int(os.getenv('MAX_VIDEO_DURATION', 7200))  # 2 hours
    
    # App Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        # Required Telegram variables
        required_vars = [
            ('TELEGRAM_API_ID', cls.API_ID),
            ('TELEGRAM_API_HASH', cls.API_HASH),
            ('TELEGRAM_BOT_TOKEN', cls.BOT_TOKEN)
        ]
        
        # Check Google authentication methods
        has_oauth_json = bool(cls.GOOGLE_CLIENT_SECRET_JSON)
        has_oauth_components = bool(cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET)
        has_service_account = bool(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
        
        if not (has_oauth_json or has_oauth_components or has_service_account):
            required_vars.append(('Google Authentication (OAuth or Service Account)', False))
        
        missing = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing.append(var_name)
        
        if missing:
            print("\n❌ Missing required environment variables:")
            for var in missing:
                print(f"   • {var}")
            
            print("\n📋 Required variables:")
            print("   • TELEGRAM_API_ID")
            print("   • TELEGRAM_API_HASH") 
            print("   • TELEGRAM_BOT_TOKEN")
            print("\n🔐 Google Authentication (choose one):")
            print("   • GOOGLE_CLIENT_SECRET_JSON (full OAuth JSON)")
            print("   • GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET (OAuth components)")
            print("   • GOOGLE_SERVICE_ACCOUNT_JSON (service account JSON)")
            
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Create directories
        for directory in [cls.CREDENTIALS_DIR, cls.SESSION_DIR, cls.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create credential files from environment variables
        cls.setup_credential_files()
    
    @classmethod
    def setup_credential_files(cls):
        """Create credential files from environment variables"""
        # Setup OAuth client secret
        if cls.GOOGLE_CLIENT_SECRET_JSON:
            try:
                client_secret_data = json.loads(cls.GOOGLE_CLIENT_SECRET_JSON)
                with open(cls.CLIENT_SECRET_FILE, 'w') as f:
                    json.dump(client_secret_data, f, indent=2)
                print(f"✅ Created client_secret.json from GOOGLE_CLIENT_SECRET_JSON")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_CLIENT_SECRET_JSON: {e}")
            except Exception as e:
                raise ValueError(f"Failed to create client_secret.json: {e}")
        
        elif cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET:
            # Create from individual components
            client_config = {
                "installed": {
                    "client_id": cls.GOOGLE_CLIENT_ID,
                    "client_secret": cls.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            with open(cls.CLIENT_SECRET_FILE, 'w') as f:
                json.dump(client_config, f, indent=2)
            print(f"✅ Created client_secret.json from GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET")
        
        # Setup Service Account
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                service_account_data = json.loads(cls.GOOGLE_SERVICE_ACCOUNT_JSON)
                with open(cls.SERVICE_ACCOUNT_FILE, 'w') as f:
                    json.dump(service_account_data, f, indent=2)
                print(f"✅ Created service_account.json from GOOGLE_SERVICE_ACCOUNT_JSON")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
            except Exception as e:
                raise ValueError(f"Failed to create service_account.json: {e}")


