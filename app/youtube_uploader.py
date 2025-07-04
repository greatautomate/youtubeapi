
import os
import asyncio
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import json
from pathlib import Path
import time

from .config import Config

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.credentials = None
        self.youtube_service = None
        self.auth_method = "None"
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube'
        ]
        self.max_retries = 3
        
    async def initialize(self):
        """Initialize YouTube service"""
        return await self.authenticate()
        
    async def authenticate(self):
        """Authenticate with Google (try service account first, then OAuth)"""
        try:
            # Try service account authentication first
            if await self._authenticate_service_account():
                self.auth_method = "Service Account"
                logger.info("Authenticated using service account")
                return True
            
            # Fall back to OAuth authentication
            if await self._authenticate_oauth():
                self.auth_method = "OAuth 2.0"
                logger.info("Authenticated using OAuth")
                return True
            
            self.auth_method = "None"
            logger.error("All authentication methods failed")
            return False
            
        except Exception as e:
            self.auth_method = "Error"
            logger.error(f"Authentication failed: {e}")
            return False

    async def _authenticate_service_account(self):
        """Authenticate using service account"""
        try:
            # Try from environment variable first
            if Config.GOOGLE_SERVICE_ACCOUNT_JSON:
                service_account_info = json.loads(Config.GOOGLE_SERVICE_ACCOUNT_JSON)
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.scopes
                )
                self.youtube_service = build('youtube', 'v3', credentials=self.credentials)
                logger.info("Service account authentication successful (from env var)")
                return True
            
            # Try from file
            if Config.SERVICE_ACCOUNT_FILE.exists():
                self.credentials = service_account.Credentials.from_service_account_file(
                    str(Config.SERVICE_ACCOUNT_FILE), scopes=self.scopes
                )
                self.youtube_service = build('youtube', 'v3', credentials=self.credentials)
                logger.info("Service account authentication successful (from file)")
                return True
            
            logger.debug("No service account credentials found")
            return False
            
        except Exception as e:
            logger.warning(f"Service account authentication failed: {e}")
            return False

    async def _authenticate_oauth(self):
        """Authenticate using OAuth"""
        try:
            # Load existing token
            if Config.TOKEN_FILE.exists():
                try:
                    self.credentials = Credentials.from_authorized_user_file(
                        str(Config.TOKEN_FILE), self.scopes
                    )
                    logger.info("Loaded existing OAuth credentials")
                except Exception as e:
                    logger.warning(f"Failed to load existing credentials: {e}")
                    self.credentials = None
            
            # Check if credentials are valid
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    try:
                        # Refresh expired credentials
                        self.credentials.refresh(Request())
                        
                        # Save refreshed credentials
                        Config.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                        with open(Config.TOKEN_FILE, 'w') as f:
                            f.write(self.credentials.to_json())
                            
                        logger.info("OAuth credentials refreshed successfully")
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        return False
                else:
                    logger.debug("No valid OAuth credentials found. Interactive setup required.")
                    return False
            
            # Build YouTube service
            self.youtube_service = build('youtube', 'v3', credentials=self.credentials)
            logger.info("OAuth authentication successful")
            return True
            
        except Exception as e:
            logger.warning(f"OAuth authentication failed: {e}")
            return False

    async def check_authentication(self):
        """Check if authentication is valid"""
        try:
            if not self.youtube_service:
                return await self.authenticate()
            
            # Test API call
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.youtube_service.channels().list(part='snippet', mine=True).execute()
            )
            
            if response and 'items' in response:
                return True
            else:
                return False
                
        except HttpError as e:
            if e.resp.status == 401:  # Unauthorized
                logger.warning("Authentication expired, attempting refresh")
                return await self.authenticate()
            else:
                logger.error(f"API error during auth check: {e}")
                return False
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return False

    async def get_auth_method(self):
        """Get current authentication method"""
        return self.auth_method

    async def upload_video(self, file_path: str, video_info: dict) -> str:
        """Upload video to YouTube"""
        try:
            if not self.youtube_service:
                if not await self.authenticate():
                    logger.error("Authentication required for upload")
                    return None
            
            # Validate file
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Video file not found: {file_path}")
            
            file_size = file_path_obj.stat().st_size
            logger.info(f"Uploading file: {file_path} ({file_size / (1024*1024):.1f} MB)")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': video_info['title'][:100],
                    'description': video_info['description'][:5000],
                    'tags': video_info.get('tags', [])[:500],
                    'categoryId': video_info.get('category_id', '22')
                },
                'status': {
                    'privacyStatus': video_info.get('privacy_status', Config.YOUTUBE_PRIVACY_STATUS),
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                file_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            # Execute upload
            request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._execute_upload, request
            )
            
            if response and 'id' in response:
                video_id = response['id']
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Video uploaded successfully: {youtube_url}")
                return youtube_url
            else:
                logger.error("Upload failed: No video ID in response")
                return None
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None
    
    def _execute_upload(self, request):
        """Execute the upload request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = None
                
                logger.info(f"Starting upload attempt {attempt + 1}")
                
                while response is None:
                    try:
                        status, response = request.next_chunk()
                        
                        if status:
                            progress = int(status.progress() * 100)
                            if progress % 10 == 0:  # Log every 10%
                                logger.info(f"Upload progress: {progress}%")
                        
                        if response is not None:
                            if 'id' in response:
                                logger.info(f"Video uploaded successfully. Video ID: {response['id']}")
                                return response
                            else:
                                logger.error(f"Upload failed: {response}")
                                raise Exception(f"Upload failed: {response}")
                                
                    except HttpError as e:
                        if e.resp.status in [500, 502, 503, 504]:
                            # Retryable errors
                            logger.warning(f"Retryable HTTP error: {e.resp.status}")
                            time.sleep(2 ** attempt)
                            continue
                        elif e.resp.status == 401:
                            # Unauthorized - need to re-authenticate
                            logger.error("Authentication expired during upload")
                            raise Exception("Authentication expired. Please re-authenticate.")
                        elif e.resp.status == 403:
                            # Forbidden - might be quota or permission issue
                            logger.error("Upload forbidden - check quotas and permissions")
                            raise Exception("Upload forbidden. Check YouTube API quotas and permissions.")
                        else:
                            # Non-retryable error
                            logger.error(f"Non-retryable HTTP error: {e}")
                            raise e
                            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Upload failed after {self.max_retries} attempts: {e}")
                    raise e
                    
        return None

    async def get_channel_info(self):
        """Get authenticated user's channel information"""
        try:
            if not self.youtube_service:
                if not await self.authenticate():
                    return None
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.youtube_service.channels().list(part='snippet,statistics', mine=True).execute()
            )
            
            if response and 'items' in response and response['items']:
                return response['items'][0]
            else:
                logger.warning("No channel found for authenticated user")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return None


