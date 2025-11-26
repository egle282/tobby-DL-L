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

if not BOT_TOKEN or not REDIS_URL:
    print("ОШИБКА: нет BOT_TOKEN или REDIS_URL")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ← ОЧЕРЕДЬ ОБЯЗАТЕЛЬНО "default"
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("default", connection=redis_conn)

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

        # Telegram лимит 50 МБ
        if os.path.getsize(filename) > 49_000_000:
            bot.send_message(chat_id, "Видео слишком большое (>49 МБ)")
            os.remove(filename)
            return

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, reply_to_message_id=message_id, timeout=600)

        os.remove(filename)
        print(f"Видео успешно отправлено: {url}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка скачивания: {str(e)}")
        print(f"ОШИБКА: {e}")

@bot.message_handler(commands=['start', 'help'])
def start(m):
    bot.reply_to(m, "Кидай любую ссылку с YouTube, TikTok, Instagram Reels, Twitter/X — пришлю чистое видео без водяных знаков!")

@bot.message_handler(func=lambda m: True)
def handle_message(m):
    url = m.text.strip()
    if any(site in url for site in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"]):
        bot.reply_to(m, "Скачиваю видео… жди 10–60 сек")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)
    else:
        bot.reply_to(m, "Пришли нормальную ссылку на видео")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'ok', 200

@app.route('/')
def index():
    return "Бот живой и готов качать видео!", 200

# ← РАБОЧИЙ WORKER ДЛЯ БЕСПЛАТНЫХ ПЛАНОВ (Railway / Render)
def run_worker():
    print("Запускаю RQ worker навсегда...")
    while True:
        try:
            with Connection(redis_conn):
                worker = SimpleWorker([queue], connection=redis_conn)
                worker.work(burst=False)          # ← вечно живой
        except Exception as e:
            print("Worker упал, перезапускаю через 5 сек:", e)
            time.sleep(5)

# keep-alive (для Render, на Railway не обязателен, но не мешает)
def keep_alive():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'your-project.onrender.com')}"
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(600)

if __name__ == "__main__":
    print("БОТ ЗАПУЩЕН — ГОТОВ К РАБОТЕ 24/7")
    threading.Thread(target=run_worker, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
