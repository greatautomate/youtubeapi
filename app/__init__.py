
"""
Telegram YouTube Bot Package
"""
from .config import Config

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your environment variables")
    raise

__version__ = "1.0.0"
__author__ = "Telegram YouTube Bot"
__description__ = "A Telegram bot that uploads videos to YouTube"


