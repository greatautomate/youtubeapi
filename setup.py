
#!/usr/bin/env python3
"""
Setup script for Telegram YouTube Bot
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    # Required Telegram variables
    required_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH', 
        'TELEGRAM_BOT_TOKEN'
    ]
    
    # Check Google authentication methods
    google_auth_methods = [
        'GOOGLE_CLIENT_SECRET_JSON',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        ('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET')
    ]
    
    missing_telegram = []
    for var in required_vars:
        if not os.getenv(var):
            missing_telegram.append(var)
    
    # Check if at least one Google auth method is available
    has_auth = False
    auth_method = "None"
    
    if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
        has_auth = True
        auth_method = "Service Account"
    elif os.getenv('GOOGLE_CLIENT_SECRET_JSON'):
        has_auth = True
        auth_method = "OAuth Client Secret JSON"
    elif os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
        has_auth = True
        auth_method = "OAuth Client Components"
    
    if missing_telegram:
        print(f"❌ Missing Telegram variables: {', '.join(missing_telegram)}")
        return False
    
    if not has_auth:
        print("❌ Missing Google authentication method")
        print("\nChoose ONE of the following:")
        print("• GOOGLE_SERVICE_ACCOUNT_JSON (service account)")
        print("• GOOGLE_CLIENT_SECRET_JSON (OAuth full JSON)")
        print("• GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET (OAuth components)")
        return False
    
    print("✅ All required environment variables are set!")
    print(f"🔐 Authentication method: {auth_method}")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        Path("./session"),
        Path("./credentials"),
        Path("./temp")
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import pyrogram
        import yt_dlp
        import googleapiclient
        import google.auth
        print("✅ All dependencies are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Telegram YouTube Bot...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment variables
    if not check_environment():
        print("\n📋 Setup your .env file with required variables")
        print("See .env.example for reference")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n✅ Setup completed successfully!")
    print("\n🎯 Next steps:")
    print("1. Run the bot: python run.py")
    print("2. Use /start command in Telegram")
    print("3. Upload videos or URLs")
    print("\n🐳 Docker deployment:")
    print("• docker-compose up -d")
    print("\n☁️ Render.com deployment:")
    print("• Push to GitHub")
    print("• Create Background Worker on Render.com")
    print("• Use Blueprint with render.yaml")
    print("• Set environment variables")
    print("• Deploy with Docker")

if __name__ == "__main__":
    main()


