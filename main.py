import os
import logging
import telebot
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp

# --- Загрузка переменных окружения ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")      # Upstash или Render Key Value
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# --- Инициализация ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)  # пока не используем, но оставим

# --- Redis + RQ (ГЛАВНОЕ ИСПРАВЛЕНИЕ) ---
if not REDIS_URL:
    print("ОШИБКА: REDIS_URL не найден в переменных окружения!")
else:
    from redis import Redis
    from rq import Queue
    redis_conn = Redis.from_url(REDIS_URL)
    # Явно указываем имя очереди "default" — это критично для Render!
    queue = Queue("default", connection=redis_conn)
    print(f"Подключено к Redis: {REDIS_URL[:40]}...")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# === Функция скачивания (выполняется в фоне) ===
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

        # Проверка размера (Telegram лимит 50 МБ без премиума)
        if os.path.getsize(filename) > 50 * 1024 * 1024:
            bot.send_message(chat_id, "Видео слишком большое (>50 МБ). Попробуй шорт или 720p.")
            os.remove(filename)
            return

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, timeout=300, reply_to_message_id=message_id)

        os.remove(filename)
        logging.info(f"Видео успешно отправлено: {url}")

    except Exception as e:
        bot.send_message(chat_id, f"Не удалось скачать: {str(e)}")
        logging.error(f"Ошибка скачивания {url}: {e}")

# === Обработчики Telegram ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Привет! Я скачиваю видео с:\n\n"
        "• YouTube / Shorts\n"
        "• TikTok\n"
        "• Instagram Reels\n"
        "• Twitter / X\n\n"
        "Просто отправь ссылку — пришлю чистое видео без водяных знаков!\n\n"
        "/ref — твоя реферальная ссылка"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['ref'])
def ref_link(message):
    user_id = str(message.from_user.id)
    refs = redis_conn.hget("referrals", user_id) or 0
    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start={user_id}"
    bot.reply_to(message, f"Твоя реферальная ссылка:\n{link}\n\nПриглашено: {int(refs)} человек")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = message.text.strip()
    platforms = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "x.com", "twitter.com"]
    if any(p in url for p in platforms):
        bot.reply_to(message, "Скачиваю видео… (10–60 сек)")
        # Ставим задачу в очередь — теперь worker её точно увидит!
        queue.enqueue(download_and_send, url, message.chat.id, message.message_id)
    else:
        bot.reply_to(message, "Отправь ссылку на видео с YouTube, TikTok, Instagram или X")

# === Flask webhook для Render ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('Content-Type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def index():
    return "Бот живой!", 200

# === Запуск ===
if __name__ == "__main__":
    logging.info("Бот запущен на Render!")
    print("Бот запущен на Render!")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
