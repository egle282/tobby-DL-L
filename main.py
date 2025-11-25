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

# ← ЭТО ГЛАВНОЕ: очередь называется "default"
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

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, reply_to_message_id=message_id, timeout=600)
        os.remove(filename)
        print(f"УСПЕШНО отправлено: {url}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
        print(f"ОШИБКА: {e}")

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Кидай любую ссылку — пришлю видео без водяков!")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if any(x in url for x in ["youtube", "youtu.be", "tiktok", "instagram", "x.com", "twitter"]):
        bot.reply_to(m, "Скачиваю… (10–60 сек)")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)

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

# ← ЭТО РАБОЧИЙ keep-alive + постоянный worker
def forever_worker():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'tobby-dl-l.onrender.com')}"
    while True:
        try:
            requests.get(url, timeout=10)      # keep-alive
        except:
            pass
        
        # Постоянно обрабатываем очередь (без burst)
        try:
            from rq import Connection, SimpleWorker
            with Connection(redis_conn):
                worker = SimpleWorker([queue], connection=redis_conn)
                worker.work(burst=False, max_jobs=1)   # ← НЕ burst, работает вечно
        except:
            pass
        time.sleep(10)

if __name__ == "__main__":
    print("БОТ ЗАПУЩЕН — ВСЁ РАБОТАЕТ!")
    threading.Thread(target=forever_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
