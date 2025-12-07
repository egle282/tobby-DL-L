from flask import Flask, request
import telebot
from .config import Config


def create_web_app(bot: telebot.TeleBot):
    """Create Flask web application for webhooks"""
    app = Flask(__name__)
    
    @app.route('/webhook', methods=['GET', 'POST'])
    def webhook():
        """Handle incoming webhook requests from Telegram"""
        if request.method == 'GET':
            return "Бот живой!", 200
        
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            if json_string:
                try:
                    update = telebot.types.Message.de_json(json_string)
                    # Process the update - this is a simplified approach
                    # In practice, you'd want to handle the update properly
                    bot.process_new_updates([telebot.types.Update.de_json(json_string)])
                    return '', 200
                except Exception as e:
                    print(f"Error processing webhook: {e}")
                    return 'ok', 400
            return 'ok', 200
        return 'ok', 200

    @app.route('/')
    def index():
        """Main endpoint for health check"""
        return {
            "status": "ok",
            "service": "Tobby Downloader Bot",
            "version": "1.0.0"
        }

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {"status": "healthy"}, 200

    return app