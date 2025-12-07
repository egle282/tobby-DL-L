import os
import yt_dlp
from config import Config
import telebot
from typing import Optional


def is_supported_url(url: str) -> bool:
    """Check if the URL is from a supported platform"""
    return any(platform in url for platform in Config.SUPPORTED_PLATFORMS)


def download_and_send(url: str, chat_id: int, message_id: int, bot: telebot.TeleBot) -> None:
    """
    Download video from URL and send it to the chat
    
    Args:
        url: Video URL to download
        chat_id: Telegram chat ID to send the video to
        message_id: Message ID to reply to
        bot: TeleBot instance
    """
    try:
        ydl_opts = {
            'format': Config.VIDEO_QUALITY,
            'outtmpl': f'/tmp/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Check file size
        if os.path.getsize(filename) > Config.MAX_FILE_SIZE:
            bot.send_message(chat_id, "Видео слишком большое (>49 МБ)")
            os.remove(filename)
            return

        # Send the video
        with open(filename, 'rb') as video:
            bot.send_video(
                chat_id, 
                video, 
                reply_to_message_id=message_id, 
                timeout=600
            )
        
        # Clean up
        os.remove(filename)
        print(f"Видео отправлено: {url}")
        
    except Exception as e:
        error_message = f"Ошибка при скачивании: {str(e)}"
        bot.send_message(chat_id, error_message)
        print(error_message)
        
        # Clean up in case of error
        try:
            # Find and remove any temp files that might have been created
            temp_files = [f for f in os.listdir('/tmp') if f.startswith(info.get('id', '')) if 'info' in locals()]
            for temp_file in temp_files:
                os.remove(os.path.join('/tmp', temp_file))
        except:
            pass  # Ignore cleanup errors


def validate_url(url: str) -> bool:
    """
    Validate if the URL is supported and accessible
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid and supported, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL format check
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    return is_supported_url(url)