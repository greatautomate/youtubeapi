
import os
import json
import logging
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from .config import Config

logger = logging.getLogger(__name__)

class AuthHandler:
    def __init__(self):
        self.client_secret_file = Config.CLIENT_SECRET_FILE
        self.token_file = Config.TOKEN_FILE
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube'
        ]
        
        # Ensure credentials directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _ensure_client_secret_file(self):
        """Ensure client_secret.json exists"""
        if not self.client_secret_file.exists():
            # Try to create from environment variables
            if Config.GOOGLE_CLIENT_SECRET_JSON:
                try:
                    client_secret_data = json.loads(Config.GOOGLE_CLIENT_SECRET_JSON)
                    with open(self.client_secret_file, 'w') as f:
                        json.dump(client_secret_data, f, indent=2)
                    logger.info("Created client_secret.json from GOOGLE_CLIENT_SECRET_JSON")
                except Exception as e:
                    logger.error(f"Failed to create client_secret.json from env var: {e}")
                    raise
            elif Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
                # Create from individual components
                client_config = {
                    "installed": {
                        "client_id": Config.GOOGLE_CLIENT_ID,
                        "client_secret": Config.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
                
                with open(self.client_secret_file, 'w') as f:
                    json.dump(client_config, f, indent=2)
                logger.info("Created client_secret.json from GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET")
            else:
                logger.error("No Google client secret configuration found")
                raise FileNotFoundError(
                    "client_secret.json not found and no Google client credentials in environment.\n"
                    "Please set either:\n"
                    "• GOOGLE_CLIENT_SECRET_JSON (full JSON)\n"
                    "• GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET (components)"
                )
        
    async def get_auth_url(self) -> str:
        """Get OAuth authorization URL"""
        try:
            # Ensure client secret file exists
            self._ensure_client_secret_file()
            
            # Create flow from client secret file
            flow = Flow.from_client_secrets_file(
                str(self.client_secret_file),
                scopes=self.scopes,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store flow state for later use
            self._flow = flow
            
            logger.info("Authorization URL generated successfully")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to get auth URL: {e}")
            return None
    
    async def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token"""
        try:
            if not hasattr(self, '_flow'):
                logger.error("No flow state found. Generate auth URL first.")
                return False
            
            logger.info("Exchanging authorization code for token")
            
            # Exchange code for token
            self._flow.fetch_token(code=code)
            
            credentials = self._flow.credentials
            
            # Save credentials to token file
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as f:
                f.write(credentials.to_json())
            
            logger.info("OAuth credentials saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return False
    
    def get_credentials_info(self) -> dict:
        """Get information about saved credentials"""
        try:
            if not self.token_file.exists():
                return {
                    'exists': False,
                    'valid': False,
                    'expired': False,
                    'has_refresh_token': False
                }
            
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file), self.scopes
            )
            
            return {
                'exists': True,
                'valid': credentials.valid,
                'expired': credentials.expired,
                'has_refresh_token': bool(credentials.refresh_token),
                'token_file': str(self.token_file)
            }
            
        except Exception as e:
            logger.error(f"Failed to get credentials info: {e}")
            return {
                'exists': False,
                'valid': False,
                'expired': False,
                'has_refresh_token': False,
                'error': str(e)
            }


