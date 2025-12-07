# Tobby Downloader Bot

A Telegram bot that downloads videos from various platforms (YouTube, TikTok, Instagram, Twitter, etc.) and sends them back to users without watermarks.

## 🚀 Features

- Download videos from YouTube, TikTok, Instagram, Twitter, Facebook, and more
- Removes watermarks from downloaded videos
- Supports video formats up to 49MB (Telegram's limit)
- Webhook support for production deployment
- Redis-based job queue for processing downloads in the background
- Admin commands for bot management
- Error handling and size checking
- Modular code architecture for maintainability

## 📋 Prerequisites

- Python 3.8+
- Redis server (for job queues)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## 🛠️ Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your configuration:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   REDIS_URL=redis://localhost:6379  # or your Redis URL
   ADMIN_IDS=123456789,987654321    # comma-separated admin user IDs
   WEBHOOK_URL=your_webhook_url      # optional, for webhook mode
   ```

6. Run the application:
   ```bash
   python app.py
   ```

### Docker Deployment

Build and run with Docker:
```bash
docker build -t tobby-downloader-bot .
docker run -d --env-file .env tobby-downloader-bot
```

## ⚙️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Your Telegram bot token from [@BotFather](https://t.me/BotFather) | Yes |
| `REDIS_URL` | Redis connection URL (for job queues) | Yes |
| `ADMIN_IDS` | Comma-separated list of admin user IDs | Yes |
| `WEBHOOK_URL` | Webhook URL for production (optional if using polling) | No |
| `PORT` | Port number for webhook (default: 8000) | No |
| `MAX_FILE_SIZE` | Maximum file size in MB (default: 49) | No |

## 🏗️ Project Structure

```
tobby_downloader_bot/
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── run.sh                   # Startup script
├── render.yaml              # Render deployment configuration
├── .env.example             # Environment variables template
├── README.md                # This file
└── tobby_bot/              # Main package
    ├── __init__.py
    ├── config/              # Configuration management
    │   └── __init__.py
    ├── services/            # Video download and processing logic
    │   └── __init__.py
    ├── handlers/            # Telegram bot command handlers
    │   └── __init__.py
    └── web/                 # Flask webhook endpoints
        └── __init__.py
```

## 🤖 Bot Commands

- `/start` - Start the bot and get welcome message
- `/help` - Show help information
- `/stats` - Get bot statistics (admin only)
- `/broadcast <message>` - Send message to all users (admin only)
- Send any video URL - Download and send back the video

## 🌐 Supported Platforms

The bot supports downloading from:
- YouTube
- TikTok
- Instagram
- Twitter/X
- Facebook
- Reddit
- And many other platforms supported by yt-dlp

## 🚀 Deployment

### Render.com

The bot is configured for easy deployment on Render using the `render.yaml` file:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following build command: `pip install -r requirements.txt`
4. Use the following start command: `bash run.sh`
5. Add your environment variables in the Render dashboard

### Heroku (Alternative)

1. Create a new app on Heroku
2. Add your environment variables in Settings > Config Vars
3. Deploy using Git or connect your GitHub repository

### Self-Hosting

For self-hosting, ensure you have Redis running and accessible, then run:
```bash
python app.py
```

## 🔧 Troubleshooting

- **Bot not responding**: Check if your webhook is properly configured or if polling is working
- **Download fails**: Ensure your server has enough storage space and yt-dlp is properly installed
- **Redis connection issues**: Verify your Redis URL and connection settings
- **Large files**: Files over 49MB will not be sent due to Telegram limitations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions, please open an issue in the repository.