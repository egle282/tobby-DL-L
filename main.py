import os
import time
import threading
import requests
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
queue = Queue(connection=redis_conn)          # ← без имени — это важно!

# Скачивание
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
            bot.send_video(chat_id, video, reply_to_message_id=message_id, timeout=300)
        os.remove(filename)
        print(f"Видео отправлено: {url}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
        print(f"Ошибка скачивания: {e}")

# Обработчики
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Кидай любую ссылку — пришлю видео без водяков!")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if any(s in url for s in ["youtube", "youtu.be", "tiktok", "instagram", "x.com", "twitter"]):
        bot.reply_to(m, "Скачиваю… (10–60 сек)")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)   # ← задача в очередь

# Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'ok', 200

@app.route('/')
def home():
    return "Бот живой!", 200

# Keep-alive + RQ worker в ОДНОМ потоке (самый надёжный способ на бесплатном плане)
def worker_and_ping():
    # Keep-alive пинг каждые 10 минут
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'tobby-dl-l.onrender.com')}"
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        
        # Каждые 30 секунд пытаемся обработать задачи из очереди
        try:
            from rq import Connection
            with Connection(redis_conn):
                from rq.worker import SimpleWorker
                w = SimpleWorker([queue], connection=redis_conn)
                w.work(burst=True, max_jobs=5)   # обрабатываем до 5 задач и возвращаемся
        except:
            pass
        time.sleep(30)

if __name__ == "__main__":
    print("Бот запущен! Worker и keep-alive работают в фоне")
    threading.Thread(target=worker_and_ping, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
