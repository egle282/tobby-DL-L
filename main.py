import os
import telebot
import threading
import redis
import rq
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
import moviepy.editor as mpy
from instagrapi import Client
import logging

load_dotenv()

# === Конфиг ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# Redis + RQ
r = redis.from_url(REDIS_URL)
queue = rq.Queue(connection=r)

# === Основные функции ===
def download_video(url, chat_id):
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': f'{chat_id}_{url[-11:]}.mp4',
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
        bot.send_video(chat_id, open(filepath, 'rb'), timeout=60)
        os.remove(filepath)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")

# === Обработчики ===
@bot.message_handler(commands=['start'])
def start(message):
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    if ref_id and ref_id.isdigit():
        # Сохраняем рефералку в Redis
        r.hincrby("referrals", ref_id, 1)
    bot.reply_to(message, "Привет! Отправь ссылку на YouTube/TikTok/Instagram/X — скачаю видео.\nКоманды: /shorts, /reels, /ref")

@bot.message_handler(commands=['ref'])
def ref(message):
    bot.reply_to(message, f"Твоя реферальная ссылка:\nhttps://t.me/{bot.get_me().username}?start={message.from_user.id}\nТвоих рефералов: {r.hget('referrals', message.from_user.id) or 0}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    url = message.text.strip()
    if any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"]):
        bot.reply_to(message, "Скачиваю...")
        threading.Thread(target=download_video, args=(url, message.chat.id)).start()

# === Flask webhook для Render ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

# === Запуск ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен на Render!")
    
    # Запуск Flask на порту Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
