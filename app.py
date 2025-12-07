#!/usr/bin/env python3
"""
Tobby Downloader Bot - Main Application

A Telegram bot that downloads videos from various platforms and sends them back to users.
"""

import os
import telebot
from redis import Redis
from rq import Queue

from tobby_bot.config import Config
from tobby_bot.handlers import register_handlers, setup_admin_commands
from tobby_bot.web import create_web_app


def create_bot():
    """Create and configure the Telegram bot"""
    bot = telebot.TeleBot(Config.BOT_TOKEN)
    return bot


def create_queue():
    """Create Redis queue for background tasks"""
    redis_conn = Redis.from_url(Config.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    return queue


def main():
    """Main application entry point"""
    # Create bot instance
    bot = create_bot()
    
    # Create queue for background tasks
    queue = create_queue()
    
    # Register bot handlers
    register_handlers(bot, queue)
    setup_admin_commands(bot)
    
    # Create web application for webhooks
    app = create_web_app(bot)
    
    # Determine if we're running in webhook mode or polling mode
    if os.getenv("WEBHOOK_MODE", "False").lower() == "true":
        # Webhook mode - run Flask app
        port = int(os.environ.get("PORT", 10000))
        print(f"Starting webhook server on port {port}...")
        app.run(host="0.0.0.0", port=port)
    else:
        # Polling mode - good for local development
        print("Starting bot in polling mode...")
        bot.infinity_polling()


if __name__ == "__main__":
    main()