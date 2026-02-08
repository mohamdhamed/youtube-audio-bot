import re
from telegram import Update
from telegram.ext import ContextTypes
from utils import restricted
from services.youtube_service import is_youtube_url
from handlers.youtube import process_youtube_url

@restricted
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages."""
    text = update.message.text.strip()
    
    # 1. Try to find a URL
    url_match = re.search(r'((?:https?://|www\.)[^\s]+)', text)
    
    if url_match:
        url = url_match.group(1)
        # 2. Check if it is a YouTube URL
        if is_youtube_url(url):
             await process_youtube_url(update, context, url)
             return
        else:
            await update.message.reply_text("❌ هذا الرابط ليس رابط يوتيوب مدعوم.")
            return

    # 3. No link found -> Unknown message
    await update.message.reply_text(
        "🤔 لم أجد رابطاً في رسالتك!\n"
        "أرسل رابط يوتيوب أو ملف لرفعه.\n"
        "استخدم /help للمساعدة."
    )
