mport yt_dlp
import os
from ..config import Config

def download_video(url, chat_id, bot):
    ydl_opts = {
        "outtmpl": os.path.join(Config.DOWNLOAD_PATH, "%(title)s.%(ext)s"),
        "max_filesize": Config.MAX_FILE_SIZE,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            bot.send_video(chat_id, open(filename, "rb"))
            os.remove(filename)
    except Exception as e:
        bot.reply_to(chat_id, f"Ошибка загрузки: {e}")
