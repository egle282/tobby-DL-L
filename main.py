import os
import time
import threading
import requests
import logging
import telebot
from flask import Flask, request
from dotenv import load_dotenv
import yt_dlp
from redis import Redis
from rq import Queue

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Redis
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("default", connection=redis_conn)

# Скачивание
def download_and_send(url, chat_id, message_id):
    try:
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': '/tmp/%(id)s.%(ext)s', 'merge_output_format': 'mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        with open(filename, 'rb') as f:
            bot.send_video(chat_id, f, reply_to_message_id=message_id, timeout=300)
        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")

# Сообщения
@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "Кидай любую ссылку с YouTube, TikTok, Instagram, X")

@bot.message_handler(func=lambda m: True)
def all(m):
    url = m.text
    if any(x in url for x in ["youtube", "tiktok", "instagram", "x.com", "twitter"]):
        bot.reply_to(m, "Скачиваю… жди 15–40 сек")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)

# Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode())
    bot.process_new_updates([update])
    return '', 200

@app.route('/'): return "живой"

# Keep-alive (чтобы не засыпал)
def keep_alive():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'tobby-dl-l.onrender.com')}"
    while True:
        try: requests.get(url)
        except: pass
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
