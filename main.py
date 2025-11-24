import os
import telebot
import threading
import redis
import rq
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
import logging

# Загружаем переменные окружения (Render + Upstash)
load_dotenv()

# === Конфиг ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")          # Upstash
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# Инициализация
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# Redis + RQ (очередь для долгих задач)
r = redis.from_url(REDIS_URL)
queue = rq.Queue(connection=r)

# Логирование
logging.basicConfig(level=logging.INFO)

# === Основные функции скачивания ===
def download_and_send(url, chat_id, message_id=None):
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': f'/tmp/{chat_id}_{url.split("/")[-1]}.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.getsize(filename) > 50 * 1024 * 1024:  # > 50 МБ
            bot.send_message(chat_id, "Видео слишком большое для Telegram (>50 МБ)")
            os.remove(filename)
            return

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, timeout=300, reply_to_message_id=message_id)

        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка скачивания: {str(e)}")
        logging.error(f"Download error: {e}")

# === Обработчики ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Привет! Я скачиваю видео с:\n"
        "• YouTube / Shorts\n"
        "• TikTok\n"
        "• Instagram Reels\n"
        "• Twitter / X\n\n"
        "Просто кинь ссылку — я пришлю видео без водяных знаков!\n\n"
        "/ref — твоя реферальная ссылка"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['ref'])
def ref_link(message):
    refs = r.hget("referrals", message.from_user.id) or 0
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.reply_to(message, f"Твоя реферальная ссылка:\n{link}\n\nПриглашено: {refs} человек")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    platforms = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"]
    if any(p in url for p in platforms):
        bot.reply_to(message, "Скачиваю видео… (может занять 10–30 сек)")
        # Запускаем в фоне через RQ (чтобы не блокировать webhook)
        job = queue.enqueue(download_and_send, url, message.chat.id, message.message_id)
    else:
        bot.reply_to(message, "Отправь ссылку на видео с YouTube, TikTok, Instagram или X")

# === Flask webhook для Render ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('Content-Type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# === Запуск ===
if __name__ == "__main__":
    logging.info("Бот запущен на Render!")
    print("Бот запущен на Render!")
    
    # Render даёт переменную PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
