import os
import time
import threading
import requests
import telebot
from flask import Flask, request
from dotenv import load_dotenv
import yt_dlp
from redis import Redis
from rq import Queue, Connection
from rq.worker import SimpleWorker

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ← САМОЕ ГЛАВНОЕ — очередь "default"
queue = Queue("default", connection=Redis.from_url(REDIS_URL))

def download_and_send(url, chat_id, message_id):
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, reply_to_message_id=message_id, timeout=600)
        os.remove(filename)
        print("ВИДЕО УСПЕШНО ОТПРАВЛЕНО")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")
        print("ОШИБКА:", e)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Кидай любую ссылку — пришлю видео без водяных знаков!")

@bot.message_handler(func=lambda m: True)
def echo_all(m):
    url = m.text.strip()
    if any(x in url for x in ["youtube", "youtu.be", "tiktok", "instagram", "x.com", "twitter"]):
        bot.reply_to(m, "Скачиваю… (10–60 сек)")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Бот живой!", 200

# ← ЭТО САМЫЙ НАДЁЖНЫЙ СПОСОБ ДЛЯ БЕСПЛАТНОГО RENDER
def run_worker():
    while True:
        try:
            with Connection():
                w = SimpleWorker([queue], connection=queue.connection)
                w.work(burst=False)          # ← работает вечно, НЕ burst
        except:
            time.sleep(5)

threading.Thread(target=run_worker, daemon=True).start()

# keep-alive
def ping():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'tobby-dl-l.onrender.com')}"
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(600)

threading.Thread(target=ping, daemon=True).start()

if __name__ == "__main__":
    print("БОТ ЗАПУЩЕН — ГОТОВ К РАБОТЕ")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
