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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
                "🎥 **YouTube Uploader Bot**\n\n"
                "Welcome! I can help you upload videos to YouTube.\n\n"
                "**Features:**\n"
                "• Upload video files (up to 2GB)\n"
                "• Download and upload from video URLs\n"
                "• OAuth 2.0 + Service Account authentication\n"
                "• Multiple video formats support\n\n"
                "**Supported Platforms:**\n"
                "• YouTube, Vimeo, TikTok, Instagram\n"
                "• Facebook, Twitter, Dailymotion\n\n"
                "**Authentication Status:**\n"
                f"🔒 **Privacy Mode:** {Config.YOUTUBE_PRIVACY_STATUS}",
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
            if message.document and not (message.document.mime_type and message.document.mime_type.startswith('video/')):
                await message.reply_text("📎 **Document received**\n\nPlease send video files only.")
                return

            await self.process_video_file(message)

        @self.app.on_message(filters.text & ~filters.command(["start", "auth", "oauth"]))
        async def handle_text_message(client, message: Message):
            text = message.text.strip()
            user_id = message.from_user.id

            # Prevent multiple simultaneous processing
            if user_id in self.processing_users:
                await message.reply_text("⏳ **Processing in progress**\n\nPlease wait for the current operation to complete.")
                return

            # Check if it's an OAuth code (FIXED LOGIC)
            if self.is_oauth_code(text):
                await self.handle_oauth_code(message, text)
            elif self.is_video_url(text):
                await self.process_video_url(message, text)
            else:
                await message.reply_text(
                    "❓ **Unrecognized Input**\n\n"
                    "Please send:\n"
                    "• A video file (MP4, AVI, MOV, etc.)\n"
                    "• A video URL (YouTube, Vimeo, etc.)\n"
                    "• An OAuth authorization code\n\n"
                    "Use /start to see available options."
                )

        @self.app.on_message(filters.command("auth"))
        async def auth_command(client, message: Message):
            await self.handle_auth_command(message)

        @self.app.on_message(filters.command("oauth"))
        async def oauth_command(client, message: Message):
            """Handle OAuth code via command"""
            if len(message.command) > 1:
                code = ' '.join(message.command[1:])  # Join all parts after /oauth
                await self.handle_oauth_code(message, code)
            else:
                await message.reply_text(
                    "**OAuth Code Command**\n\n"
                    "Usage: `/oauth your_authorization_code`\n\n"
                    "Example: `/oauth 4/1AVMBsJjws3uaafmYm7iEBcni4Cmq2aBK81QQyOhW34CU_C5n7JqvUTIBhRM`"
                )

    def is_oauth_code(self, text: str) -> bool:
        """Check if the text is a Google OAuth authorization code"""
        text = text.strip()

        # Google OAuth authorization codes:
        # - Usually start with "4/" 
        # - Are typically 50-200 characters long
        # - Contain letters, numbers, underscores, hyphens, slashes

        # Primary check: Google OAuth codes start with "4/"
        if text.startswith('4/') and len(text) > 20:
            logger.info(f"Detected OAuth code starting with '4/': {text[:10]}...")
            return True

        # Secondary check: Long alphanumeric string that could be an OAuth code
        if (len(text) > 30 and len(text) < 300 and
            not text.startswith('http') and
            not text.startswith('www.') and
            not '\n' in text and
            not ' ' in text and
            any(c.isalnum() for c in text)):
            logger.info(f"Detected potential OAuth code: {text[:10]}...")
            return True

        return False

    async def handle_check_auth(self, callback_query: CallbackQuery):
        """Handle authentication check"""
        try:
            auth_status = await self.youtube_uploader.check_authentication()
            auth_method = await self.youtube_uploader.get_auth_method()

            if auth_status:
                channel_info = await self.youtube_uploader.get_channel_info()
                channel_name = "Unknown"
                if channel_info:
                    channel_name = channel_info.get('snippet', {}).get('title', 'Unknown')

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
                ])

                await callback_query.message.edit_text(
                    f"✅ **YouTube Authentication Active**\n\n"
                    f"📺 **Channel:** {channel_name}\n"
                    f"🔐 **Method:** {auth_method}\n"
                    f"🔒 **Privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
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
                    "❌ **YouTube Authentication Required**\n\n"
                    "Authentication methods available:\n"
                    "• **Service Account** (automatic if configured)\n"
                    "• **OAuth 2.0** (interactive setup)\n\n"
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
                    "🔐 **OAuth Setup Process**\n\n"
                    "**Steps:**\n"
                    "1. Click the link below to authorize\n"
                    "2. Grant permissions to your YouTube channel\n"
                    "3. Copy the authorization code\n"
                    "4. Send it back to me as a message\n\n"
                    f"**Authorization URL:**\n{auth_url}\n\n"
                    "⚠️ **Important:**\n"
                    "• This gives the bot access to your YouTube channel\n"
                    "• Only you can authorize your own channel\n"
                    "• The code expires in 10 minutes\n"
                    "• You can also use: `/oauth your_code`",
                    reply_markup=keyboard
                )
            else:
                await callback_query.message.edit_text(
                    "❌ **OAuth Setup Failed**\n\n"
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
            "📋 **How to Use YouTube Upload Bot**\n\n"
            "**1. Authentication:**\n"
            "• Service Account: Automatic (if configured)\n"
            "• OAuth 2.0: Manual setup via 'Setup OAuth'\n\n"
            "**2. Upload Videos:**\n"
            "• Send video files directly\n"
            "• Send video URLs from supported platforms\n\n"
            "**3. Supported Formats:**\n"
            "• **Files:** MP4, AVI, MOV, MKV, FLV, WebM\n"
            "• **URLs:** YouTube, Vimeo, TikTok, Instagram\n\n"
            "**4. Limits:**\n"
            f"• **File size:** {Config.MAX_FILE_SIZE // (1024*1024)} MB max\n"
            f"• **Duration:** {Config.MAX_VIDEO_DURATION // 60} minutes max\n\n"
            "**5. Privacy:**\n"
            f"• **Default privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n"
            "• Videos are uploaded to your authorized channel\n\n"
            "**6. Commands:**\n"
            "• `/start` - Show main menu\n"
            "• `/auth` - Quick authentication check\n"
            "• `/oauth code` - Submit OAuth code directly",
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
            "🎥 **YouTube Uploader Bot**\n\n"
            "Welcome! I can help you upload videos to YouTube.\n\n"
            "**Features:**\n"
            "• Upload video files (up to 2GB)\n"
            "• Download and upload from video URLs\n"
            "• OAuth 2.0 + Service Account authentication\n"
            "• Multiple video formats support\n\n"
            f"**Privacy Mode:** {Config.YOUTUBE_PRIVACY_STATUS}",
            reply_markup=keyboard
        )

    async def handle_oauth_code(self, message: Message, code: str):
        """Handle OAuth authorization code"""
        user_id = message.from_user.id

        try:
            self.processing_users.add(user_id)
            status_msg = await message.reply_text("🔐 **Processing authorization code...**")

            logger.info(f"Processing OAuth code: {code[:10]}...")

            success = await self.auth_handler.exchange_code_for_token(code)

            if success:
                await self.youtube_uploader.initialize()

                channel_info = await self.youtube_uploader.get_channel_info()
                channel_name = "Unknown"
                if channel_info:
                    channel_name = channel_info.get('snippet', {}).get('title', 'Unknown')

                await status_msg.edit_text(
                    f"✅ **Authentication Successful!**\n\n"
                    f"📺 **Channel:** {channel_name}\n"
                    f"🔐 **Method:** OAuth 2.0\n"
                    f"🔒 **Privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
                    "You can now upload videos to YouTube!\n"
                    "Send me a video file or URL to get started."
                )
            else:
                await status_msg.edit_text(
                    "❌ **Authentication Failed**\n\n"
                    "The authorization code may be:\n"
                    "• Invalid or expired\n"
                    "• Already used\n"
                    "• From wrong Google account\n\n"
                    "Please try the OAuth setup process again.\n"
                    "Use /start → Setup OAuth to get a new code."
                )

        except Exception as e:
            logger.error(f"OAuth code handling failed: {e}")
            await message.reply_text(f"❌ **Error:** {str(e)}")
        finally:
            self.processing_users.discard(user_id)

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
            await message.reply_text("⏳ **Processing in progress**\n\nPlease wait for the current operation to complete.")
            return

        try:
            self.processing_users.add(user_id)

            # Check authentication first
            auth_status = await self.youtube_uploader.check_authentication()
            if not auth_status:
                await message.reply_text(
                    "❌ **Authentication Required**\n\n"
                    "Please authenticate with YouTube first.\n\n"
                    "**Options:**\n"
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
                    f"❌ **File Too Large**\n\n"
                    f"📁 **Size:** {file_size / (1024*1024):.1f} MB\n"
                    f"📏 **Limit:** {Config.MAX_FILE_SIZE / (1024*1024):.1f} MB\n\n"
                    "Please send a smaller file."
                )
                return

            # Check duration for video files
            if hasattr(video, 'duration') and video.duration:
                if video.duration > Config.MAX_VIDEO_DURATION:
                    await message.reply_text(
                        f"❌ **Video Too Long**\n\n"
                        f"⏱️ **Duration:** {video.duration // 60} minutes\n"
                        f"⏰ **Limit:** {Config.MAX_VIDEO_DURATION // 60} minutes\n\n"
                        "Please send a shorter video."
                    )
                    return

            status_msg = await message.reply_text("⏬ **Downloading video...**")

            # Create unique file path
            file_extension = Path(file_name).suffix or '.mp4'
            file_path = Config.TEMP_DIR / f"{video.file_unique_id}{file_extension}"

            # Download video file
            await message.download(file_path)

            await status_msg.edit_text("🔍 **Preparing for upload...**")

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

            await status_msg.edit_text("⏫ **Uploading to YouTube...**\n\n*This may take a while for large files...*")

            # Upload to YouTube
            youtube_url = await self.youtube_uploader.upload_video(str(file_path), video_info)

            if youtube_url:
                auth_method = await self.youtube_uploader.get_auth_method()
                await status_msg.edit_text(
                    f"✅ **Upload Successful!**\n\n"
                    f"🎥 **YouTube URL:** {youtube_url}\n"
                    f"📁 **File:** {file_name}\n"
                    f"💾 **Size:** {file_size / (1024*1024):.1f} MB\n"
                    f"🔐 **Auth:** {auth_method}\n"
                    f"🔒 **Privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n"
                    f"📅 **Uploaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "🎉 Your video is now live on YouTube!"
                )
            else:
                await status_msg.edit_text(
                    "❌ **Upload Failed**\n\n"
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
            await message.reply_text(f"❌ **Error:** {str(e)}")
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
            await message.reply_text("⏳ **Processing in progress**\n\nPlease wait for the current operation to complete.")
            return

        try:
            self.processing_users.add(user_id)

            # Check authentication first
            auth_status = await self.youtube_uploader.check_authentication()
            if not auth_status:
                await message.reply_text(
                    "❌ **Authentication Required**\n\n"
                    "Please authenticate with YouTube first.\n\n"
                    "**Options:**\n"
                    "• Service Account (automatic if configured)\n"
                    "• OAuth 2.0: Use /start → Setup OAuth"
                )
                return

            status_msg = await message.reply_text("🔍 **Analyzing URL...**")

            # Get video info first
            info_result = await self.video_downloader.get_video_info(url)
            if not info_result['success']:
                await status_msg.edit_text(f"❌ **URL Analysis Failed**\n\n**Error:** {info_result['error']}")
                return

            video_info = info_result['info']

            # Check duration
            if video_info['duration'] > Config.MAX_VIDEO_DURATION:
                await status_msg.edit_text(
                    f"❌ **Video Too Long**\n\n"
                    f"⏱️ **Duration:** {video_info['duration'] // 60} minutes\n"
                    f"⏰ **Limit:** {Config.MAX_VIDEO_DURATION // 60} minutes\n\n"
                    f"**Video:** {video_info['title']}"
                )
                return

            await status_msg.edit_text(
                f"📹 **Video Found**\n\n"
                f"**Title:** {video_info['title'][:50]}...\n"
                f"**Duration:** {video_info['duration'] // 60}:{video_info['duration'] % 60:02d}\n"
                f"**Uploader:** {video_info['uploader']}\n"
                f"**Views:** {video_info['view_count']:,}\n\n"
                "⏬ **Starting download...**"
            )

            # Download video from URL
            download_result = await self.video_downloader.download_video(url, Config.TEMP_DIR)

            if not download_result['success']:
                await status_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"**Error:** {download_result['error']}\n"
                    f"**URL:** {url}\n\n"
                    "**Common causes:**\n"
                    "• Video is private or removed\n"
                    "• Geographic restrictions\n"
                    "• Platform blocking downloads"
                )
                return

            file_path = download_result['file_path']
            video_info = download_result['info']

            await status_msg.edit_text("⏫ **Uploading to YouTube...**\n\n*This may take a while...*")

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
                    f"✅ **Upload Successful!**\n\n"
                    f"🎥 **YouTube URL:** {youtube_url}\n"
                    f"🔗 **Source:** {url}\n"
                    f"📝 **Title:** {upload_info['title']}\n"
                    f"🔐 **Auth:** {auth_method}\n"
                    f"🔒 **Privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n"
                    f"📅 **Uploaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "🎉 Your video is now live on YouTube!"
                )
            else:
                await status_msg.edit_text(
                    "❌ **Upload Failed**\n\n"
                    "The video could not be uploaded to YouTube.\n"
                    "Please check your authentication and try again."
                )

        except Exception as e:
            logger.error(f"Error processing video URL: {e}")
            await message.reply_text(f"❌ **Error:** {str(e)}")
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
                    channel_name = channel_info.get('snippet', {}).get('title', 'Unknown')

                await message.reply_text(
                    f"✅ **Authentication Status: Active**\n\n"
                    f"📺 **Channel:** {channel_name}\n"
                    f"🔐 **Method:** {auth_method}\n"
                    f"🔒 **Privacy:** {Config.YOUTUBE_PRIVACY_STATUS}\n\n"
                    "You can upload videos now!"
                )
            else:
                await message.reply_text(
                    "❌ **Authentication Status: Required**\n\n"
                    "**Available methods:**\n"
                    "• Service Account (automatic if configured)\n"
                    "• OAuth 2.0: Use /start → Setup OAuth"
                )
        except Exception as e:
            logger.error(f"Auth command error: {e}")
            await message.reply_text(f"❌ **Error:** {str(e)}")

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
