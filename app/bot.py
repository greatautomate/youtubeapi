import os
import asyncio
import logging
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime

from .config import Config
from .youtube_uploader import YouTubeUploader
from .video_downloader import VideoDownloader
from .auth_handler import AuthHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TelegramYouTubeBot:
    def __init__(self):
        self.app = Client(
            "youtube_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workdir=str(Config.SESSION_DIR)
        )
        
        self.youtube_uploader = YouTubeUploader()
        self.video_downloader = VideoDownloader()
        self.auth_handler = AuthHandler()
        
        # Track processing states
        self.processing_users = set()
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📺 Check YouTube Auth", callback_data="check_auth")],
                [InlineKeyboardButton("🔐 Setup OAuth", callback_data="setup_oauth")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
            ])
            
            await message.reply_text(
                "🎥 <strong>YouTube Uploader Bot</strong>\n\n"
                "Welcome! I can help you upload videos to YouTube.\n\n"
                "<strong>Features:</strong>\n"
                "• Upload video files (up to 2GB)\n"
                "• Download and upload from video URLs\n"
                "• OAuth 2.0 + Service Account authentication\n"
                "• Multiple video formats support\n\n"
                "<strong>Supported Platforms:</strong>\n"
                "• YouTube, Vimeo, TikTok, Instagram\n"
                "• Facebook, Twitter, Dailymotion\n\n"
                "<strong>Authentication Status:</strong>\n"
                f"🔒 <strong>Privacy Mode:</strong> {Config.YOUTUBE_PRIVACY_STATUS}",
                reply_markup=keyboard
            )

        @self.app.on_callback_query()
        async def callback_handler(client, callback_query: CallbackQuery):
            data = callback_query.data
            
            try:
                if data == "check_auth":
                    await self.handle_check_auth(callback_query)
                elif data == "setup_oauth":
                    await self.handle_setup_oauth(callback_query)
                elif data == "help":
                    await self.handle_help(callback_query)
                elif data == "back_to_main":
                    await self.handle_back_to_main(callback_query)
                    
            except Exception as e:
                logger.error(f"Callback handler error: {e}")
                await callback_query.answer("❌ An error occurred. Please try again.")

        @self.app.on_message(filters.video | filters.document)
        async def handle_media(client, message: Message):
            if message.document and not (message.document.mime_type and message.document.mime_type.startswith("video/")):
                await message.reply_text("📎 <strong>Document received</strong>\n\nPlease send video files only.")
                return
            
            await self.process_video_file(message)

        @self.app.on_message(filters.text & ~filters.command("start"))
        async def handle_text_message(client, message: Message):
            text = message.text.strip()
            user_id = message.from_user.id
            
            # Prevent multiple simultaneous processing
            if user_id in self.processing_users:
                await message.reply_text("⏳ <strong>Processing in progress</strong>\n\nPlease wait for the current operation to complete.")
                return
            
            # Check if it\'s an OAuth code
            if len(text) > 20 and '/' not in text and 'http' not in text.lower() and ' ' not in text:
                await self.handle_oauth_code(message, text)
            elif self.is_video_url(text):
                await self.process_video_url(message, text)
            else:
                await message.reply_text(
                    "❓ <strong>Unrecognized Input</strong>\n\n"
                    "Please send:\n"
                    "• A video file (MP4, AVI, MOV, etc.)\n"
                    "• A video URL (YouTube, Vimeo, etc.)\n"
                    "• An OAuth authorization code\n\n"
                    "Use /start to see available options."
                )

        @self.app.on_message(filters.command("auth"))
        async def auth_command(client, message: Message):
            await self.handle_auth_command(message)

    async def handle_check_auth(self, callback_query: CallbackQuery):
        """Handle authentication check"""
        try:
            auth_status = await self.youtube_uploader.check_authentication()
            auth_method = await self.youtube_uploader.get_auth_method()
            
            if auth_status:
                channel_info = await self.youtube_uploader.get_channel_info()
                channel_name = "Unknown"
                if channel_info:
                    channel_name = channel_info.get("snippet", {}).get("title", "Unknown")
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ])
                
                await callback_query.message.edit_text(
                    f"✅ <strong>YouTube Authentication Active</strong>\n\n"
                    f"📺 <strong>Channel:</strong> {channel_name}\n"
                    f"🔐 <strong>Method:</strong> {auth_method}\n"
                    f"🔒 <strong>Privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
                    "You can now upload videos! Send me:\n"
                    "• A video file\n"
                    "• A video URL\n\n"
                    "The bot will handle the rest!",
                    reply_markup=keyboard
                )
            else:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔐 Setup OAuth", callback_data="setup_oauth")],
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ])
                
                await callback_query.message.edit_text(
                    "❌ <strong>YouTube Authentication Required</strong>\n\n"
                    "Authentication methods available:\n"
                    "• <strong>Service Account</strong> (automatic if configured)\n"
                    "• <strong>OAuth 2.0</strong> (interactive setup)\n\n"
                    "Click Setup OAuth for interactive authentication.",
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Auth check error: {e}")
            await callback_query.answer("❌ Error checking authentication")

    async def handle_setup_oauth(self, callback_query: CallbackQuery):
        """Handle OAuth setup"""
        try:
            auth_url = await self.auth_handler.get_auth_url()
            
            if auth_url:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ])
                
                await callback_query.message.edit_text(
                    "🔐 <strong>OAuth Setup Process</strong>\n\n"
                    "<strong>Steps:</strong>\n"
                    "1. Click the link below to authorize\n"
                    "2. Grant permissions to your YouTube channel\n"
                    "3. Copy the authorization code\n"
                    "4. Send it back to me as a message\n\n"
                    f"<strong>Authorization URL:</strong>\n{auth_url}\n\n"
                    "⚠️ <strong>Important:</strong>\n"
                    "• This gives the bot access to your YouTube channel\n"
                    "• Only you can authorize your own channel\n"
                    "• The code expires in 10 minutes",
                    reply_markup=keyboard
                )
            else:
                await callback_query.message.edit_text(
                    "❌ <strong>OAuth Setup Failed</strong>\n\n"
                    "Could not generate authorization URL.\n"
                    "Possible issues:\n"
                    "• Missing Google client credentials\n"
                    "• Invalid client secret configuration\n\n"
                    "Please check the bot configuration."
                )
        except Exception as e:
            logger.error(f"OAuth setup error: {e}")
            await callback_query.answer("❌ Error setting up OAuth")

    async def handle_help(self, callback_query: CallbackQuery):
        """Handle help command"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
        ])
        
        await callback_query.message.edit_text(
            "📋 <strong>How to Use YouTube Upload Bot</strong>\n\n"
            "<strong>1. Authentication:</strong>\n"
            "• Service Account: Automatic (if configured)\n"
            "• OAuth 2.0: Manual setup via 'Setup OAuth'\n\n"
            "<strong>2. Upload Videos:</strong>\n"
            "• Send video files directly\n"
            "• Send video URLs from supported platforms\n\n"
            "<strong>3. Supported Formats:</strong>\n"
            "• <strong>Files:</strong> MP4, AVI, MOV, MKV, FLV, WebM\n"
            "• <strong>URLs:</strong> YouTube, Vimeo, TikTok, Instagram\n\n"
            "<strong>4. Limits:</strong>\n"
            f"• <strong>File size:</strong> {Config.MAX_FILE_SIZE // (1024*1024)} MB max\n"
            f"• <strong>Duration:</strong> {Config.MAX_VIDEO_DURATION // 60} minutes max\n\n"
            "<strong>5. Privacy:</strong>\n"
            f"• <strong>Default privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n"
            "• Videos are uploaded to your authorized channel\n\n"
            "<strong>6. Commands:</strong>\n"
            "• <code>/start</code> - Show main menu\n"
            "• <code>/auth</code> - Quick authentication check",
            reply_markup=keyboard
        )

    async def handle_back_to_main(self, callback_query: CallbackQuery):
        """Handle back to main menu"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📺 Check YouTube Auth", callback_data="check_auth")],
            [InlineKeyboardButton("🔐 Setup OAuth", callback_data="setup_oauth")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await callback_query.message.edit_text(
            "🎥 <strong>YouTube Uploader Bot</strong>\n\n"
            "Welcome! I can help you upload videos to YouTube.\n\n"
            "<strong>Features:</strong>\n"
            "• Upload video files (up to 2GB)\n"
            "• Download and upload from video URLs\n"
            "• OAuth 2.0 + Service Account authentication\n"
            "• Multiple video formats support\n\n"
            f"<strong>Privacy Mode:</strong> {Config.YOUTUBE_PRIVACY_STATUS}",
            reply_markup=keyboard
        )

    async def handle_oauth_code(self, message: Message, code: str):
        """Handle OAuth authorization code"""
        user_id = message.from_user.id
        
        try:
            self.processing_users.add(user_id)
            status_msg = await message.reply_text("🔐 <strong>Processing authorization code...</strong>")
            
            success = await self.auth_handler.exchange_code_for_token(code)
            
            if success:
                await self.youtube_uploader.initialize()
                
                channel_info = await self.youtube_uploader.get_channel_info()
                channel_name = "Unknown"
                if channel_info:
                    channel_name = channel_info.get("snippet", {}).get("title", "Unknown")
                
                await status_msg.edit_text(
                    f"✅ <strong>Authentication Successful!</strong>\n\n"
                    f"📺 <strong>Channel:</strong> {channel_name}\n"
                    f"🔐 <strong>Method:</strong> OAuth 2.0\n"
                    f"🔒 <strong>Privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
                    "You can now upload videos to YouTube!\n"
                    "Send me a video file or URL to get started."
                )
            else:
                await status_msg.edit_text(
                    "❌ <strong>Authentication Failed</strong>\n\n"
                    "The authorization code may be:\n"
                    "• Invalid or expired\n"
                    "• Already used\n"
                    "• From wrong Google account\n\n"
                    "Please try the OAuth setup process again.\n"
                    "Use /start → Setup OAuth to get a new code."
                )
                
        except Exception as e:
            logger.error(f"OAuth code handling failed: {e}")
            await message.reply_text(f"❌ <strong>Error:</strong> {str(e)}")
        finally:
            self.processing_users.discard(user_id)
            # Cleanup
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass

    def is_video_url(self, text: str) -> bool:
        """Check if the text is a valid video URL"""
        video_patterns = [
            'youtube.com/watch', 'youtu.be/', 'vimeo.com/', 'dailymotion.com/',
            'twitch.tv/', 'facebook.com/', 'instagram.com/', 'tiktok.com/',
            'twitter.com/', 'reddit.com/', 'streamable.com/'
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in video_patterns)

    async def process_video_file(self, message: Message):
        """Process uploaded video file"""
        user_id = message.from_user.id
        
        if user_id in self.processing_users:
            await message.reply_text("⏳ <strong>Processing in progress</strong>\n\nPlease wait for the current operation to complete.")
            return
        
        try:
            self.processing_users.add(user_id)
            
            # Check authentication first
            auth_status = await self.youtube_uploader.check_authentication()
            if not auth_status:
                await message.reply_text(
                    "❌ <strong>Authentication Required</strong>\n\n"
                    "Please authenticate with YouTube first.\n\n"
                    "<strong>Options:</strong>\n"
                    "• Service Account (automatic if configured)\n"
                    "• OAuth 2.0: Use /start → Setup OAuth"
                )
                return

            video = message.video or message.document
            file_size = video.file_size
            file_name = getattr(video, 'file_name', None) or f"video_{video.file_unique_id}"
            
            # Check file size
            if file_size > Config.MAX_FILE_SIZE:
                await message.reply_text(
                    f"❌ <strong>File Too Large</strong>\n\n"
                    f"📁 <strong>Size:</strong> {file_size / (1024*1024):.1f} MB\n"
                    f"📏 <strong>Limit:</strong> {Config.MAX_FILE_SIZE / (1024*1024):.1f} MB\n\n"
                    "Please send a smaller file."
                )
                return

            # Check duration for video files
            if hasattr(video, 'duration') and video.duration:
                if video.duration > Config.MAX_VIDEO_DURATION:
                    await message.reply_text(
                        f"❌ <strong>Video Too Long</strong>\n\n"
                        f"⏱️ <strong>Duration:</strong> {video.duration // 60} minutes\n"
                        f"⏰ <strong>Limit:</strong> {Config.MAX_VIDEO_DURATION // 60} minutes\n\n"
                        "Please send a shorter video."
                    )
                    return

            status_msg = await message.reply_text("⏬ <strong>Downloading video...</strong>")
            
            # Create unique file path
            file_extension = Path(file_name).suffix or '.mp4'
            file_path = Config.TEMP_DIR / f"{video.file_unique_id}{file_extension}"
            
            # Download video file
            await message.download(file_path)
            
            await status_msg.edit_text("🔍 <strong>Preparing for upload...</strong>")
            
            # Prepare video metadata
            video_title = Path(file_name).stem
            if len(video_title) > 100:
                video_title = video_title[:100]
            
            video_info = {
                'title': video_title,
                'description': f"Uploaded via Telegram Bot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nOriginal filename: {file_name}\nFile size: {file_size / (1024*1024):.1f} MB\nUploaded by: @{message.from_user.username or message.from_user.first_name}",
                'tags': ['telegram', 'bot', 'upload', 'video'],
                'category_id': '22',
                'privacy_status': Config.YOUTUBE_PRIVACY_STATUS
            }
            
            await status_msg.edit_text("⏫ <strong>Uploading to YouTube...</strong>\n\n<em>This may take a while for large files...</em>")
            
            # Upload to YouTube
            youtube_url = await self.youtube_uploader.upload_video(str(file_path), video_info)
            
            if youtube_url:
                auth_method = await self.youtube_uploader.get_auth_method()
                await status_msg.edit_text(
                    f"✅ <strong>Upload Successful!</strong>\n\n"
                    f"🎥 <strong>YouTube URL:</strong> {youtube_url}\n"
                    f"📁 <strong>File:</strong> {file_name}\n"
                    f"💾 <strong>Size:</strong> {file_size / (1024*1024):.1f} MB\n"
                    f"🔐 <strong>Auth:</strong> {auth_method}\n"
                    f"🔒 <strong>Privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n"
                    f"📅 <strong>Uploaded:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "🎉 Your video is now live on YouTube!"
                )
            else:
                await status_msg.edit_text(
                    "❌ <strong>Upload Failed</strong>\n\n"
                    "The video could not be uploaded to YouTube.\n"
                    "Possible reasons:\n"
                    "• Authentication expired\n"
                    "• File format not supported by YouTube\n"
                    "• Network connectivity issues\n"
                    "• YouTube API quota exceeded\n\n"
                    "Please try again later."
                )
                
        except Exception as e:
            logger.error(f"Error processing video file: {e}")
            await message.reply_text(f"❌ <strong>Error:</strong> {str(e)}")
        finally:
            self.processing_users.discard(user_id)
            # Cleanup
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass

    async def process_video_url(self, message: Message, url: str):
        """Process video URL"""
        user_id = message.from_user.id
        
        if user_id in self.processing_users:
            await message.reply_text("⏳ <strong>Processing in progress</strong>\n\nPlease wait for the current operation to complete.")
            return
        
        try:
            self.processing_users.add(user_id)
            
            # Check authentication first
            auth_status = await self.youtube_uploader.check_authentication()
            if not auth_status:
                await message.reply_text(
                    "❌ <strong>Authentication Required</strong>\n\n"
                    "Please authenticate with YouTube first.\n\n"
                    "<strong>Options:</strong>\n"
                    "• Service Account (automatic if configured)\n"
                    "• OAuth 2.0: Use /start → Setup OAuth"
                )
                return

            status_msg = await message.reply_text("🔍 <strong>Analyzing URL...</strong>")
            
            # Get video info first
            info_result = await self.video_downloader.get_video_info(url)
            if not info_result['success']:
                await status_msg.edit_text(f"❌ <strong>URL Analysis Failed</strong>\n\n<strong>Error:</strong> {info_result['error']}")
                return
            
            video_info = info_result['info']
            
            # Check duration
            if video_info['duration'] > Config.MAX_VIDEO_DURATION:
                await status_msg.edit_text(
                    f"❌ <strong>Video Too Long</strong>\n\n"
                    f"⏱️ <strong>Duration:</strong> {video_info['duration'] // 60} minutes\n"
                    f"⏰ <strong>Limit:</strong> {Config.MAX_VIDEO_DURATION // 60} minutes\n\n"
                    f"<strong>Video:</strong> {video_info['title']}"
                )
                return
            
            await status_msg.edit_text(
                f"📹 <strong>Video Found</strong>\n\n"
                f"<strong>Title:</strong> {video_info['title'][:50]}...\n"
                f"<strong>Duration:</strong> {video_info['duration'] // 60}:{video_info['duration'] % 60:02d}\n"
                f"<strong>Uploader:</strong> {video_info['uploader']}\n"
                f"<strong>Views:</strong> {video_info['view_count']:,}\n\n"
                "⏬ <strong>Starting download...</strong>"
            )
            
            # Download video from URL
            download_result = await self.video_downloader.download_video(url, Config.TEMP_DIR)
            
            if not download_result['success']:
                await status_msg.edit_text(
                    f"❌ <strong>Download Failed</strong>\n\n"
                    f"<strong>Error:</strong> {download_result['error']}\n"
                    f"<strong>URL:</strong> {url}\n\n"
                    "<strong>Common causes:</strong>\n"
                    "• Video is private or removed\n"
                    "• Geographic restrictions\n"
                    "• Platform blocking downloads"
                )
                return
            
            file_path = download_result['file_path']
            video_info = download_result['info']
            
            await status_msg.edit_text("⏫ <strong>Uploading to YouTube...</strong>\n\n<em>This may take a while...</em>")
            
            # Prepare video metadata
            video_title = video_info.get('title', 'Downloaded Video')
            if len(video_title) > 100:
                video_title = video_title[:100]
            
            upload_info = {
                'title': video_title,
                'description': f"Downloaded from: {url}\n\nOriginal uploader: {video_info.get('uploader', 'Unknown')}\nOriginal views: {video_info.get('view_count', 0):,}\nUploaded via Telegram Bot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nBot user: @{message.from_user.username or message.from_user.first_name}\n\n{video_info.get('description', '')[:4000]}",
                'tags': (video_info.get('tags', []) + ['telegram', 'bot', 'download'])[:30],
                'category_id': '22',
                'privacy_status': Config.YOUTUBE_PRIVACY_STATUS
            }
            
            youtube_url = await self.youtube_uploader.upload_video(file_path, upload_info)
            
            if youtube_url:
                auth_method = await self.youtube_uploader.get_auth_method()
                await status_msg.edit_text(
                    f"✅ <strong>Upload Successful!</strong>\n\n"
                    f"🎥 <strong>YouTube URL:</strong> {youtube_url}\n"
                    f"🔗 <strong>Source:</strong> {url}\n"
                    f"📝 <strong>Title:</strong> {upload_info['title']}\n"
                    f"🔐 <strong>Auth:</strong> {auth_method}\n"
                    f"🔒 <strong>Privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n"
                    f"📅 <strong>Uploaded:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "🎉 Your video is now live on YouTube!"
                )
            else:
                await status_msg.edit_text(
                    "❌ <strong>Upload Failed</strong>\n\n"
                    "The video could not be uploaded to YouTube.\n"
                    "Please check your authentication and try again."
                )
                
        except Exception as e:
            logger.error(f"Error processing video URL: {e}")
            await message.reply_text(f"❌ <strong>Error:</strong> {str(e)}")
        finally:
            self.processing_users.discard(user_id)
            # Cleanup
            if 'file_path' in locals() and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                except:
                    pass

    async def handle_auth_command(self, message: Message):
        """Handle /auth command"""
        try:
            status = await self.youtube_uploader.check_authentication()
            auth_method = await self.youtube_uploader.get_auth_method()
            
            if status:
                channel_info = await self.youtube_uploader.get_channel_info()
                channel_name = "Unknown"
                if channel_info:
                    channel_name = channel_info.get("snippet", {}).get("title", "Unknown")
                
                await message.reply_text(
                    f"✅ <strong>Authentication Status: Active</strong>\n\n"
                    f"📺 <strong>Channel:</strong> {channel_name}\n"
                    f"🔐 <strong>Method:</strong> {auth_method}\n"
                    f"🔒 <strong>Privacy:</strong> {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
                    "You can upload videos now!"
                )
            else:
                await message.reply_text(
                    "❌ <strong>Authentication Status: Required</strong>\n\n"
                    "<strong>Available methods:</strong>\n"
                    "• Service Account (automatic if configured)\n"
                    "• OAuth 2.0: Use /start → Setup OAuth"
                )
        except Exception as e:
            logger.error(f"Auth command error: {e}")
            await message.reply_text(f"❌ <strong>Error:</strong> {str(e)}")

    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram YouTube Bot...")
        logger.info(f"Environment: {Config.ENVIRONMENT}")
        logger.info(f"Privacy Mode: {Config.YOUTUBE_PRIVACY_STATUS}")
        logger.info(f"Max File Size: {Config.MAX_FILE_SIZE / (1024*1024):.0f} MB")
        logger.info(f"Max Duration: {Config.MAX_VIDEO_DURATION / 60:.0f} minutes")
        
        # Create necessary directories
        Config.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        Config.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Start the bot
        self.app.run()


