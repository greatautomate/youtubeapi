#!/usr/bin/env python3
"""
Telegram YouTube Bot - Main Entry Point
"""
import sys
import logging
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.bot import TelegramYouTubeBot

def main():
    """Main application entry point"""
    try:
        bot = TelegramYouTubeBot()
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


