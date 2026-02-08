from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import ALLOWED_USERS

def restricted(func):
    """Decorator to restrict access to allowed users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if ALLOWED_USERS and user_id not in ALLOWED_USERS:
            await update.message.reply_text(
                f"⛔ *غير مصرح لك باستخدام هذا البوت.*\n\n"
                f"🆔 المعرّف الخاص بك: `{user_id}`\n\n"
                "لطلب الصلاحية، انسخ المعرّف وأرسله للمطور:\n"
                "[تواصل معي](https://t.me/Mohamd_hamd)",
                parse_mode='Markdown'
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def get_filename_from_url(url: str, default="downloaded_file"):
    """Extract filename from URL."""
    from urllib.parse import urlparse, unquote
    import os
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    if not filename or '.' not in filename:
        filename = default
    return filename
