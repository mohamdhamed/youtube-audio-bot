import os
import re
import asyncio
from functools import partial
from telegram import Update
from telegram.ext import ContextTypes
from utils import restricted
from config import CREDENTIALS_PATH, GOOGLE_DRIVE_FOLDER_ID
from services.youtube_service import download_audio, is_youtube_url
from services.drive_service import upload_to_drive
import logging

logger = logging.getLogger(__name__)

async def process_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    """Core logic to process a YouTube URL."""
    processing_msg = await update.message.reply_text(
        "⏳ جاري تحميل وتحويل الفيديو... انتظر قليلاً"
    )
    
    try:
        loop = asyncio.get_running_loop()
        file_path, result = await loop.run_in_executor(None, partial(download_audio, url, "downloads"))
        
        if file_path is None:
            await processing_msg.edit_text(f"❌ فشل التحميل: {result}")
            return
        
        await processing_msg.edit_text("📤 جاري إرسال الملف...")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        telegram_sent = False
        
        if file_size_mb <= 50:
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
        
        if GOOGLE_DRIVE_FOLDER_ID:
            await processing_msg.edit_text("☁️ جاري الرفع إلى Google Drive...")
            
            file_id = await loop.run_in_executor(
                None,
                partial(upload_to_drive, file_path, GOOGLE_DRIVE_FOLDER_ID, CREDENTIALS_PATH)
            )
            
            if file_id:
                drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                if telegram_sent:
                    await processing_msg.edit_text(
                        f"✅ تم بنجاح!\n• [رابط Drive]({drive_link})", 
                        parse_mode='Markdown'
                    )
                else:
                    await processing_msg.edit_text(
                        f"✅ تم الرفع للدرايف!\n🔗 [تحميل]({drive_link})", 
                        parse_mode='Markdown'
                    )
            else:
                await processing_msg.edit_text("⚠️ فشل الرفع لـ Drive")
        else:
             if not telegram_sent:
                await processing_msg.edit_text("❌ الملف كبير جداً ولا يوجد Drive.")
             else:
                await processing_msg.edit_text("✅ تم!")
        
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

@restricted
async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming YouTube links."""
    text = update.message.text.strip()
    url_match = re.search(r'((?:https?://|www\.)[^\s]+)', text)
    if not url_match:
        return
        
    url = url_match.group(1)
    if not is_youtube_url(url):
        return
    
    await process_youtube_url(update, context, url)
