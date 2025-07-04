import asyncio
import logging
import yt_dlp
from pathlib import Path
import re

from .config import Config

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[height<=1080][filesize<2G]/best[filesize<2G]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'extractaudio': False,
            'embed_subs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'no_warnings': True,
            'quiet': True,
            'no_color': True,
            'extract_flat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'ignoreerrors': False,
            'no_check_certificate': True,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'merge_output_format': 'mp4',
        }

    async def download_video(self, url: str, output_dir: Path) -> dict:
        """Download video from URL"""
        try:
            # Clean and validate URL
            url = url.strip()
            if not self._is_valid_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            # Update output template with directory
            sanitized_template = str(output_dir / '%(title).100s.%(ext)s')
            self.ydl_opts['outtmpl'] = sanitized_template
            
            # Get video info first
            logger.info(f"Extracting info for: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                if not info:
                    return {
                        'success': False,
                        'error': 'Unable to extract video information'
                    }
                
                # Check if it's a live stream
                if info.get('is_live', False):
                    return {
                        'success': False,
                        'error': 'Live streams are not supported'
                    }
                
                # Check duration
                duration = info.get('duration', 0)
                if duration and duration > Config.MAX_VIDEO_DURATION:
                    return {
                        'success': False,
                        'error': f"Video too long: {duration//60} minutes (max: {Config.MAX_VIDEO_DURATION//60} minutes)"
                    }
                
                # Check file size estimate
                filesize = info.get('filesize') or info.get('filesize_approx', 0)
                if filesize and filesize > Config.MAX_FILE_SIZE:
                    return {
                        'success': False,
                        'error': f"File too large: {filesize/(1024*1024):.1f} MB (max: {Config.MAX_FILE_SIZE/(1024*1024):.1f} MB)"
                    }
                
                # Check if video is available
                availability = info.get('availability', 'public')
                if availability in ['private', 'subscriber_only', 'needs_auth']:
                    return {
                        'success': False,
                        'error': f'Video is {availability} and cannot be downloaded'
                    }
                
                logger.info(f"Starting download: {info.get('title', 'Unknown')}")
                
                # Download the video
                await asyncio.get_event_loop().run_in_executor(
                    None, ydl.download, [url]
                )
                
                # Find downloaded file
                title = self._sanitize_filename(info.get('title', 'video'))
                ext = info.get('ext', 'mp4')
                
                # Try multiple file naming patterns
                possible_files = [
                    output_dir / f"{title}.{ext}",
                    output_dir / f"{title[:50]}.{ext}",
                    output_dir / f"{title[:100]}.{ext}",
                    output_dir / f"{info.get('id', 'video')}.{ext}",
                ]
                
                file_path = None
                for pf in possible_files:
                    if pf.exists():
                        file_path = pf
                        break
                
                # If not found, search for any new file in the directory
                if not file_path:
                    import time
                    current_time = time.time()
                    
                    for file in output_dir.glob("*"):
                        if (file.is_file() and 
                            file.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'] and
                            (current_time - file.stat().st_mtime) < 300):  # 5 minutes ago
                            file_path = file
                            break
                
                if not file_path or not file_path.exists():
                    return {
                        'success': False,
                        'error': 'Downloaded file not found'
                    }
                
                # Check actual file size
                actual_size = file_path.stat().st_size
                if actual_size > Config.MAX_FILE_SIZE:
                    file_path.unlink()  # Delete oversized file
                    return {
                        'success': False,
                        'error': f"File too large: {actual_size/(1024*1024):.1f} MB (max: {Config.MAX_FILE_SIZE/(1024*1024):.1f} MB)"
                    }
                
                # Check if file is actually a video (minimum size check)
                if actual_size < 1024 * 10:  # Less than 10KB
                    file_path.unlink()
                    return {
                        'success': False,
                        'error': 'Downloaded file is too small or corrupted'
                    }
                
                logger.info(f"Successfully downloaded: {file_path.name} ({actual_size/(1024*1024):.1f} MB)")
                
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'info': {
                        'title': info.get('title', 'Downloaded Video'),
                        'description': info.get('description', ''),
                        'tags': self._extract_tags(info),
                        'duration': duration,
                        'uploader': info.get('uploader', ''),
                        'upload_date': info.get('upload_date', ''),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'webpage_url': info.get('webpage_url', url),
                        'thumbnail': info.get('thumbnail', ''),
                        'format': info.get('format', 'unknown'),
                        'filesize': actual_size
                    }
                }
                
        except yt_dlp.DownloadError as e:
            logger.error(f"Download error: {e}")
            error_msg = str(e)
            
            # Provide more user-friendly error messages
            if 'Video unavailable' in error_msg:
                error_msg = 'Video is unavailable or has been removed'
            elif 'Private video' in error_msg:
                error_msg = 'Video is private and cannot be downloaded'
            elif 'age-restricted' in error_msg.lower():
                error_msg = 'Video is age-restricted and cannot be downloaded'
            elif 'copyright' in error_msg.lower():
                error_msg = 'Video is blocked due to copyright restrictions'
            elif 'geoblocked' in error_msg.lower():
                error_msg = 'Video is blocked in your region'
            
            return {
                'success': False,
                'error': f"Download failed: {error_msg}"
            }
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[-\s]+', '-', filename)
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip('-_')

    def _extract_tags(self, info: dict) -> list:
        """Extract relevant tags from video info"""
        tags = []
        
        # Add uploader as tag
        if info.get('uploader'):
            tags.append(info['uploader'])
        
        # Add category if available
        if info.get('category'):
            tags.append(info['category'])
        
        # Add existing tags
        if info.get('tags'):
            tags.extend(info['tags'][:10])  # Limit to 10 tags
        
        # Add platform-specific tags
        url = info.get('webpage_url', '')
        if 'youtube.com' in url or 'youtu.be' in url:
            tags.append('YouTube')
        elif 'vimeo.com' in url:
            tags.append('Vimeo')
        elif 'tiktok.com' in url:
            tags.append('TikTok')
        elif 'instagram.com' in url:
            tags.append('Instagram')
        elif 'facebook.com' in url:
            tags.append('Facebook')
        elif 'twitter.com' in url:
            tags.append('Twitter')
        
        # Remove duplicates and empty tags
        tags = list(set([tag.strip() for tag in tags if tag and tag.strip()]))
        
        return tags[:20]  # YouTube allows max 500 characters total for tags

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))

    async def get_video_info(self, url: str) -> dict:
        """Get video information without downloading"""
        try:
            # Clean URL
            url = url.strip()
            if not self._is_valid_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            logger.info(f"Getting info for: {url}")
            
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                if info:
                    return {
                        'success': True,
                        'info': {
                            'title': info.get('title', 'Unknown'),
                            'duration': info.get('duration', 0),
                            'uploader': info.get('uploader', ''),
                            'view_count': info.get('view_count', 0),
                            'like_count': info.get('like_count', 0),
                            'description': (info.get('description', '')[:500] + '...') if info.get('description') else '',
                            'thumbnail': info.get('thumbnail', ''),
                            'webpage_url': info.get('webpage_url', url),
                            'upload_date': info.get('upload_date', ''),
                            'is_live': info.get('is_live', False),
                            'availability': info.get('availability', 'unknown'),
                            'filesize': info.get('filesize') or info.get('filesize_approx', 0)
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Unable to extract video information'
                    }
                    
        except Exception as e:
            logger.error(f"Info extraction failed: {e}")
            return {
                'success': False,
                'error': f"Failed to get video info: {str(e)}"
            }


