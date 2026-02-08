from telegram import Update
from telegram.ext import ContextTypes
from utils import restricted

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    welcome_message = """
🎵 *مرحباً بك في بوت الوسائط والملفات!*

*الخدمات المتاحة:*

📹 *تحويل يوتيوب لصوت:*
أرسل رابط يوتيوب وسأحوله لـ MP3

📚 *رفع الكتب للدرايف:*
أرسل ملف (PDF, EPUB, etc.) وسأرفعه للدرايف

*الروابط المدعومة:*
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/shorts/...

ابدأ الآن! 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = """
*كيفية الاستخدام:*

*🎵 تحويل يوتيوب:*
1. انسخ رابط الفيديو من يوتيوب
2. الصقه وأرسله إلي
3. استلم ملف الصوت!

*📚 رفع الكتب:*
1. أرسل ملف PDF أو EPUB أو أي كتاب
2. سيتم رفعه تلقائياً للدرايف

*الأوامر:*
/start - بدء البوت
/help - عرض المساعدة
/myid - معرفة الـ ID الخاص بك (للأدمن)
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the user their ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 الـ ID الخاص بك هو:\n`{user_id}`", parse_mode='Markdown')
