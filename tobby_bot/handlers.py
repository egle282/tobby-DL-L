import telebot
from .services import validate_url, download_and_send
from .config import Config
from rq import Queue
from redis import Redis


def register_handlers(bot: telebot.TeleBot, queue: Queue):
    """Register all bot handlers"""
    
    @bot.message_handler(commands=['start'])
    def start(message: telebot.types.Message):
        """Handle /start command"""
        welcome_text = (
            "Привет! 🎬\n\n"
            "Кидай любую ссылку на видео — я пришлю его без водяков!\n\n"
            "Поддерживаемые платформы:\n"
            "• YouTube\n"
            "• TikTok\n"
            "• Instagram\n"
            "• Twitter/X"
        )
        bot.reply_to(message, welcome_text)

    @bot.message_handler(commands=['help'])
    def help_command(message: telebot.types.Message):
        """Handle /help command"""
        help_text = (
            "🤖 Как пользоваться ботом:\n\n"
            "1. Просто отправь мне ссылку на видео с одной из поддерживаемых платформ\n"
            "2. Я скачаю видео и отправлю его тебе обратно\n\n"
            "⚠️ Видео не должны превышать 49 МБ"
        )
        bot.reply_to(message, help_text)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message: telebot.types.Message):
        """Handle all other messages (assumed to be URLs)"""
        url = message.text.strip()
        
        # Validate the URL
        if not validate_url(url):
            bot.reply_to(message, "Не поддерживаемая ссылка. Отправь ссылку с YouTube, TikTok, Instagram или Twitter.")
            return
        
        # Check if it's a supported platform
        if not any(platform in url for platform in Config.SUPPORTED_PLATFORMS):
            bot.reply_to(message, "Не поддерживаемая платформа. Поддерживаются: YouTube, TikTok, Instagram, Twitter.")
            return
        
        # Send processing message
        processing_msg = bot.reply_to(message, "скачиваю… (ожидайте 10–60 сек)")
        
        # Add download task to queue
        try:
            queue.enqueue(
                download_and_send, 
                url, 
                message.chat.id, 
                message.message_id, 
                bot
            )
        except Exception as e:
            bot.reply_to(message, f"Ошибка при добавлении задачи: {str(e)}")
            print(f"Queue error: {e}")


def setup_admin_commands(bot: telebot.TeleBot):
    """Setup admin-only commands if needed"""
    
    @bot.message_handler(commands=['stats'], func=lambda m: str(m.from_user.id) in Config.ADMIN_IDS)
    def stats_command(message: telebot.types.Message):
        """Admin command to get bot statistics"""
        # TODO: Implement statistics gathering
        bot.reply_to(message, "Статистика временно недоступна")