import telebot
from ..services import download_video

def register_handlers(bot, queue):
    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        bot.reply_to(message, "Привет! Отправь мне ссылку на видео для загрузки.")

    @bot.message_handler(commands=["help"])
    def send_help(message):
        bot.reply_to(message, "Отправь ссылку на видео, и я загружу его для тебя.")

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        url = message.text
        if url.startswith("http"):
            bot.reply_to(message, "Загрузка видео...")
            queue.enqueue(download_video, url, message.chat.id, bot)

def setup_admin_commands(bot):
    pass
