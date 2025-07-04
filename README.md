&lt;h1&gt;Telegram YouTube Bot&lt;/h1&gt;

&lt;p&gt;A comprehensive Telegram bot that uploads videos to YouTube with multiple authentication methods and platform support.&lt;/p&gt;

&lt;h2&gt;🚀 Features&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;✅ &lt;strong&gt;Multiple Authentication Methods&lt;/strong&gt;
  &lt;ul&gt;
  &lt;li&gt;Service Account (automated)&lt;/li&gt;
  &lt;li&gt;OAuth 2.0 (interactive)&lt;/li&gt;
  &lt;/ul&gt;
&lt;/li&gt;
&lt;li&gt;✅ &lt;strong&gt;Video Upload Support&lt;/strong&gt;
  &lt;ul&gt;
  &lt;li&gt;Direct file uploads (up to 2GB)&lt;/li&gt;
  &lt;li&gt;URL downloads from 50+ platforms&lt;/li&gt;
  &lt;/ul&gt;
&lt;/li&gt;
&lt;li&gt;✅ &lt;strong&gt;Platform Support&lt;/strong&gt;
  &lt;ul&gt;
  &lt;li&gt;YouTube, Vimeo, TikTok, Instagram&lt;/li&gt;
  &lt;li&gt;Facebook, Twitter, Dailymotion, and more&lt;/li&gt;
  &lt;/ul&gt;
&lt;/li&gt;
&lt;li&gt;✅ &lt;strong&gt;Docker Containerization&lt;/strong&gt;&lt;/li&gt;
&lt;li&gt;✅ &lt;strong&gt;Render.com Deployment Ready&lt;/strong&gt;&lt;/li&gt;
&lt;li&gt;✅ &lt;strong&gt;Comprehensive Error Handling&lt;/strong&gt;&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;📋 Prerequisites&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;Python 3.11+&lt;/li&gt;
&lt;li&gt;Telegram Bot Token&lt;/li&gt;
&lt;li&gt;Google Cloud Console project&lt;/li&gt;
&lt;li&gt;YouTube Data API v3 enabled&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;⚡ Quick Start&lt;/h2&gt;

&lt;h3&gt;1. Clone Repository&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;git clone https://github.com/yourusername/telegram-youtube-bot.git
cd telegram-youtube-bot
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;2. Install Dependencies&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;pip install -r requirements.txt
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;3. Setup Environment&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;cp .env.example .env
# Edit .env with your credentials
&lt;/code&gt;&lt;/pre&n
&lt;h3&gt;4. Run Setup&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;python setup.py
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;5. Start Bot&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;python run.py
&lt;/code&gt;&lt;/pre&gt;

&lt;h2&gt;🔐 Authentication Methods&lt;/h2&gt;

&lt;p&gt;Choose &lt;strong&gt;ONE&lt;/strong&gt; of the following methods:&lt;/p&gt;

&lt;h3&gt;Method 1: Service Account (Recommended for Production)&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;Method 2: OAuth Client Secret JSON&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;GOOGLE_CLIENT_SECRET_JSON={"installed":{"client_id":"...",...}}
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;Method 3: OAuth Components&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
&lt;/code&gt;&lt;/pre&gt;

&lt;h2&gt;🌐 Environment Variables&lt;/h2&gt;

&lt;h3&gt;Required Variables&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;# Telegram (REQUIRED)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# Google Authentication (CHOOSE ONE METHOD)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
# OR
GOOGLE_CLIENT_SECRET_JSON={"installed":{"client_id":"...",...}}
# OR
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;Optional Variables&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;YOUTUBE_API_KEY=your_api_key
YOUTUBE_PRIVACY_STATUS=unlisted
MAX_FILE_SIZE=2147483648
MAX_VIDEO_DURATION=7200
ENVIRONMENT=production
LOG_LEVEL=INFO
&lt;/code&gt;&lt;/pre&gt;

&lt;h2&gt;🐳 Docker Deployment&lt;/h2&gt;

&lt;h3&gt;Local Docker&lt;/h3&gt;
&lt;pre&gt;&lt;code&gt;docker-compose up -d
&lt;/code&gt;&lt;/pre&gt;

&lt;h3&gt;Render.com Deployment&lt;/h3&gt;
&lt;ol&gt;
&lt;li&gt;&lt;strong&gt;Push to GitHub&lt;/strong&gt;&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Create Background Worker&lt;/strong&gt; on Render.com&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Use Blueprint&lt;/strong&gt; with &lt;code&gt;render.yaml&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Set Environment Variables&lt;/strong&gt; in dashboard&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Deploy&lt;/strong&gt; with Docker&lt;/li&gt;
&lt;/ol&gt;

&lt;h2&gt;📖 Usage&lt;/h2&gt;

&lt;ol&gt;
&lt;li&gt;&lt;strong&gt;Start the bot&lt;/strong&gt;: Send &lt;code&gt;/start&lt;/code&gt; to your bot&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Authenticate&lt;/strong&gt;: 
   &lt;ul&gt;
   &lt;li&gt;Service Account: Automatic&lt;/li&gt;
   &lt;li&gt;OAuth: Follow setup process&lt;/li&gt;
   &lt;/ul&gt;
&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Upload videos&lt;/strong&gt;:
   &lt;ul&gt;
   &lt;li&gt;Send video files directly&lt;/li&gt;
   &lt;li&gt;Send video URLs from supported platforms&lt;/li&gt;
   &lt;/ul&gt;
&lt;/li&gt;
&lt;/ol&gt;

&lt;h2&gt;🎯 Supported Platforms&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;Video Platforms&lt;/strong&gt;: YouTube, Vimeo, Dailymotion&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Social Media&lt;/strong&gt;: TikTok, Instagram, Facebook, Twitter&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Other&lt;/strong&gt;: Reddit, Streamable, Twitch&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;📝 Commands&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;&lt;code&gt;/start&lt;/code&gt; - Show main menu and authentication status&lt;/li&gt;
&lt;li&gt;&lt;code&gt;/auth&lt;/code&gt; - Quick authentication check&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;🔧 Configuration&lt;/h2&gt;

&lt;h3&gt;File Size Limits&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;Default&lt;/strong&gt;: 2GB&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Configurable&lt;/strong&gt;: Set &lt;code&gt;MAX_FILE_SIZE&lt;/code&gt; in bytes&lt;/li&gt;
&lt;/ul&gt;

&lt;h3&gt;Video Duration Limits&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;Default&lt;/strong&gt;: 2 hours (7200 seconds)&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Configurable&lt;/strong&gt;: Set &lt;code&gt;MAX_VIDEO_DURATION&lt;/code&gt; in seconds&lt;/li&gt;
&lt;/ul&gt;

&lt;h3&gt;Privacy Settings&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;Default&lt;/strong&gt;: &lt;code&gt;unlisted&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Options&lt;/strong&gt;: &lt;code&gt;public&lt;/code&gt;, &lt;code&gt;unlisted&lt;/code&gt;, &lt;code&gt;private&lt;/code&gt;&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;🚨 Troubleshooting&lt;/h2&gt;

&lt;h3&gt;Authentication Issues&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Verify Google credentials are correct&lt;/li&gt;
&lt;li&gt;Check YouTube API is enabled&lt;/li&gt;
&lt;li&gt;Ensure proper scopes are set&lt;/li&gt;
&lt;/ul&gt;

&lt;h3&gt;Upload Failures&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Check file size and duration limits&lt;/li&gt;
&lt;li&gt;Verify authentication status&lt;/li&gt;
&lt;li&gt;Check YouTube API quotas&lt;/li&gt;
&lt;/ul&gt;

&lt;h3&gt;Download Failures&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Verify URL is accessible&lt;/li&gt;
&lt;li&gt;Check platform restrictions&lt;/li&gt;
&lt;li&gt;Ensure video is not private&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;📊 Features Overview&lt;/h2&gt;

&lt;table&gt;
&lt;thead&gt;
&lt;tr&gt;
&lt;th&gt;Feature&lt;/th&gt;
&lt;th&gt;Status&lt;/th&gt;
&lt;th&gt;Description&lt;/th&gt;
&lt;/tr&gt;
&lt;/thead&gt;
&lt;tbody&gt;
&lt;tr&gt;
&lt;td&gt;File Upload&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Direct video file uploads&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;URL Download&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Download from 50+ platforms&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Service Account&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Automated authentication&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;OAuth 2.0&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Interactive authentication&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Docker Support&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Containerized deployment&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Error Handling&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Comprehensive error messages&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
&lt;td&gt;Progress Updates&lt;/td&gt;
&lt;td&gt;✅&lt;/td&gt;
&lt;td&gt;Real-time status updates&lt;/td&gt;
&lt;/tr&gt;
&lt;/tbody&gt;
&lt;/table&gt;

&lt;h2&gt;🔄 API Quotas&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;YouTube API&lt;/strong&gt;: 10,000 units/day (default)&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Upload Cost&lt;/strong&gt;: ~1600 units per video&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Daily Uploads&lt;/strong&gt;: ~6 videos with default quota&lt;/li&gt;
&lt;/ul&gt;

&lt;h2&gt;📄 License&lt;/h2&gt;

&lt;p&gt;MIT License - see LICENSE file for details.&lt;/p&gt;

&lt;h2&gt;🤝 Contributing&lt;/h2&gt;

&lt;ol&gt;
&lt;li&gt;Fork the repository&lt;/li&gt;
&lt;li&gt;Create feature branch&lt;/li&gt;
&lt;li&gt;Make changes&lt;/li&gt;
&lt;li&gt;Submit pull request&lt;/li&gt;
&lt;/ol&gt;

&lt;h2&gt;📞 Support&lt;/h2&gt;

&lt;ul&gt;
&lt;li&gt;&lt;strong&gt;Issues&lt;/strong&gt;: GitHub Issues&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Documentation&lt;/strong&gt;: See README.md&lt;/li&gt;
&lt;li&gt;&lt;strong&gt;Updates&lt;/strong&gt;: Check releases page&lt;/li&gt;
&lt;/ul&gt;

&lt;hr&gt;

&lt;p&gt;&lt;strong&gt;Made with ❤️ for the YouTube creator community&lt;/strong&gt;&lt;/p&gt;


