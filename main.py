import os
import telebot
import yt_dlp
from flask import Flask, request
from dotenv import load_dotenv
from redis import Redis
from rq import Queue

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ОЧЕРЕДЬ "default" — именно её слушает rq worker из команды запуска
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

        if os.path.getsize(filename) > 49_000_000:
            bot.send_message(chat_id, "Видео >49 МБ — Telegram не примет")
            os.remove(filename)
            return

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, reply_to_message_id=message_id, timeout=600)
        os.remove(filename)
        print(f"Видео отправлено: {url}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
        print(f"Ошибка: {e}")

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Кидай ссылку — пришлю видео без водяков!")

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

@app.route('/')
def index():
    return "Бот живой!"

# НИКАКИХ multiprocessing, threading, keep-alive — всё запускается через Start Command
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
