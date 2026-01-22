"""
YouTube Audio Drive Bot
A Telegram bot that converts YouTube videos to audio and uploads to Google Drive.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from services.youtube_service import download_audio, is_youtube_url
from services.drive_service import upload_to_drive

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get credentials from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')


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
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming YouTube links."""
    url = update.message.text.strip()
    
    # Check if it's a YouTube URL - silently ignore non-YouTube links
    if not is_youtube_url(url):
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ جاري تحميل وتحويل الفيديو... انتظر قليلاً"
    )
    
    try:
        # Download and convert audio
        file_path, result = download_audio(url, "downloads")
        
        if file_path is None:
            await processing_msg.edit_text(f"❌ فشل التحميل: {result}")
            return
        
        # Update status
        await processing_msg.edit_text("📤 جاري إرسال الملف...")
        
        # Check file size (Telegram limit is 50MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        telegram_sent = False
        
        if file_size_mb <= 50:
            # Send audio file to user
            try:
                with open(file_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=result,
                        caption=f"🎵 {result}"
                    )
                telegram_sent = True
            except Exception as send_error:
                logger.warning(f"Failed to send via Telegram: {send_error}")
        else:
            await processing_msg.edit_text(
                f"⚠️ الملف كبير ({file_size_mb:.1f}MB)، سيتم رفعه للدرايف فقط..."
            )
        
        # Upload to Google Drive if configured
        if GOOGLE_DRIVE_FOLDER_ID:
            await processing_msg.edit_text("☁️ جاري الرفع إلى Google Drive...")
            
            file_id = upload_to_drive(
                file_path,
                GOOGLE_DRIVE_FOLDER_ID,
                CREDENTIALS_PATH
            )
            
            if file_id:
                drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                if telegram_sent:
                    await processing_msg.edit_text(
                        "✅ تم بنجاح!\n"
                        "• الملف مرسل إليك\n"
                        f"• [رابط Drive]({drive_link})"
                    , parse_mode='Markdown')
                else:
                    await processing_msg.edit_text(
                        f"✅ تم الرفع للدرايف!\n"
                        f"📁 الملف كبير ({file_size_mb:.1f}MB)\n"
                        f"🔗 [اضغط هنا للتحميل]({drive_link})"
                    , parse_mode='Markdown')
            else:
                await processing_msg.edit_text(
                    "✅ تم إرسال الملف!\n" if telegram_sent else "❌ فشل الرفع!\n"
                    "⚠️ فشل الرفع إلى Drive (تحقق من الإعدادات)"
                )
        else:
            if telegram_sent:
                await processing_msg.edit_text("✅ تم إرسال الملف بنجاح!")
            else:
                await processing_msg.edit_text(
                    f"❌ الملف كبير جداً ({file_size_mb:.1f}MB)\n"
                    "أضف إعدادات Drive لرفع الملفات الكبيرة."
                )
        
        # Cleanup: remove local file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove temp file: {e}")
            
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads (books, PDFs, etc.)."""
    document = update.message.document
    
    if not document:
        return
    
    file_name = document.file_name
    file_size_mb = document.file_size / (1024 * 1024)
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"📥 جاري تحميل: {file_name}...\n"
        f"📦 الحجم: {file_size_mb:.1f}MB"
    )
    
    try:
        # Download file from Telegram
        file = await context.bot.get_file(document.file_id)
        
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        local_path = os.path.join("downloads", file_name)
        
        await file.download_to_drive(local_path)
        
        await processing_msg.edit_text("☁️ جاري الرفع إلى Google Drive...")
        
        # Upload to Drive
        if GOOGLE_DRIVE_FOLDER_ID:
            file_id = upload_to_drive(
                local_path,
                GOOGLE_DRIVE_FOLDER_ID,
                CREDENTIALS_PATH
            )
            
            if file_id:
                drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                await processing_msg.edit_text(
                    f"✅ تم رفع الملف بنجاح!\n"
                    f"📚 {file_name}\n"
                    f"🔗 [رابط Drive]({drive_link})"
                , parse_mode='Markdown')
            else:
                await processing_msg.edit_text(
                    "❌ فشل الرفع إلى Drive\n"
                    "تحقق من إعدادات الاتصال."
                )
        else:
            await processing_msg.edit_text(
                "⚠️ Drive غير مفعّل. أضف GOOGLE_DRIVE_FOLDER_ID"
            )
        
        # Cleanup
        try:
            os.remove(local_path)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown messages."""
    await update.message.reply_text(
        "🤔 أرسل لي رابط يوتيوب أو ملف لرفعه!\n"
        "استخدم /help للمساعدة."
    )


def main() -> None:
    """Run the bot."""
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        print("   Create a .env file with: TELEGRAM_BOT_TOKEN=your_token")
        return
    
    print("🚀 Starting YouTube Audio Drive Bot...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handle URLs (messages containing http)
    url_filter = filters.TEXT & filters.Regex(r'https?://')
    application.add_handler(MessageHandler(url_filter, handle_youtube_link))
    
    # Handle document uploads (books, PDFs, etc.)
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Handle other text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
    
    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def start_health_server():
    """Start a simple HTTP server for Koyeb health checks."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        
        def log_message(self, format, *args):
            pass  # Suppress logging
    
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 Health server running on port {port}")


if __name__ == '__main__':
    start_health_server()
    main()
