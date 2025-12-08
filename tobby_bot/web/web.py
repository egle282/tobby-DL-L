from flask import Flask, request
import telebot

def create_web_app(bot):
    app = Flask(__name__)

    @app.route(f"/{bot.token}", methods=["POST"])
    def webhook():
        update = telebot.types.Message.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([telebot.types.Message.de_json(update["message"])])
        return "", 200

    return app
