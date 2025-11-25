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

# Redis + очередь
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("default", connection=redis_conn)

# Запускаем RQ worker в фоне (внутри одного процесса)
from rq.worker import SimpleWorker
worker = SimpleWorker([queue], connection=redis_conn)
threading.Thread(target=worker.work, daemon=True).start()

# Функция скачивания
def download_and_send(url, chat_id, message_id):
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video_file:
            bot.send_video(chat_id, video_file, reply_to_message_id=message_id, timeout=300)
        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")

# Обработчики бота
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Кидай ссылку с YouTube, TikTok, Instagram Reels или X — пришлю видео без водяных знаков!")

@bot.message_handler(func=lambda m: True)
def handle_url(m):
    url = m.text.strip()
    if any(site in url for site in ["youtube", "youtu.be", "tiktok", "instagram", "x.com", "twitter"]):
        bot.reply_to(m, "Скачиваю видео… (10–60 сек)")
        queue.enqueue(download_and_send, url, m.chat.id, m.message_id)

# Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'ok', 200

@app.route('/')
def index():
    return "Бот живой!", 200

# Keep-alive (чтобы не засыпал на бесплатном плане)
def keep_alive():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'tobby-dl-l.onrender.com')}"
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(600)  # каждые 10 минут

if __name__ == "__main__":
    print("Бот запущен!")
    threading.Thread(target=keep_alive, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
