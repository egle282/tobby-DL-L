import os
import logging
import telebot
import threading   # ← ЭТО БЫЛО ЗАБЫТО
import requests    # ← И ЭТО ТОЖЕ
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# === Redis + RQ (обязательно имя очереди "default") ===
if not REDIS_URL:
    print("ОШИБКА: REDIS_URL не найден!")
else:
    from redis import Redis
    from rq import Queue
    redis_conn = Redis.from_url(REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    print(f"Redis подключён: {REDIS_URL[:40]}...")

logging.basicConfig(level=logging.INFO)

# === Функция скачивания ===
def download_and_send(url, chat_id, message_id=None):
    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': f'/tmp/{chat_id}_{abs(hash(url))}.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.getsize(filename) > 50 * 1024 * 1024:
            bot.send_message(chat_id, "Видео >50 МБ, Telegram не примет")
            os.remove(filename)
            return

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, timeout=300, reply_to_message_id=message_id)
        os.remove(filename)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
        logging.error(f"Ошибка скачивания")

# === Обработчики ===
@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, "Привет! Кидай ссылку с YouTube / TikTok / Instagram Reels / X — пришлю видео без водяных знаков")

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    url = message.text.strip()
    if any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"]):
        bot.reply_to(message, "Скачиваю… (10–60 сек)")
        queue.enqueue(download_and_send, url, message.chat.id, message.message_id)
    else:
        bot.reply_to(message, "Пришли нормальную ссылку на видео")

# === Webhook ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('Content-Type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'ok', 200

@app.route('/')
def index():
    return "Бот живой!", 200

# === Keep-alive для бесплатного плана Render (чтобы не засыпал) ===
def keep_alive():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME') or 'tobby-dl-l.onrender.com'}"
    while True:
        try:
            requests.get(url, timeout=5)
        except:
            pass
        time.sleep(600)  # каждые 10 минут

# === Запуск ===
if __name__ == "__main__":
    print("Бот запущен на Render!")
    logging.info("Бот запущен на Render!")

    # Запускаем пинг в фоне
    threading.Thread(target=keep_alive, daemon=True).start()

    # Запускаем Flask (Render сам найдёт порт)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
