import os
import asyncio
from functools import partial
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import restricted
from config import CREDENTIALS_PATH, FOLDERS, DEFAULT_FOLDER
from services.drive_service import upload_to_drive
import logging

logger = logging.getLogger(__name__)

# Pending uploads state
pending_uploads = {}
pending_videos = {}

def get_folder_keyboard():
    """Create inline keyboard for folder selection."""
    buttons = []
    for key, folder in FOLDERS.items():
        if folder['id']:
            buttons.append(InlineKeyboardButton(folder['name'], callback_data=f"folder_{key}"))
    keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(keyboard)

def get_video_choice_keyboard():
    """Create inline keyboard for video upload choice."""
    keyboard = [
        [InlineKeyboardButton("🎵 استخراج الصوت", callback_data="video_audio")],
        [InlineKeyboardButton("🎬 رفع الفيديو", callback_data="video_keep")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_available_folders_count():
    return sum(1 for f in FOLDERS.values() if f['id'])

@restricted
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads."""
    document = update.message.document
    if not document:
        return
    
    file_name = document.file_name
    file_size_mb = document.file_size / (1024 * 1024)
    user_id = update.effective_user.id
    
    processing_msg = await update.message.reply_text(f"📥 جاري تحميل: {file_name}...")
    
    try:
        file = await context.bot.get_file(document.file_id)
        os.makedirs("downloads", exist_ok=True)
        local_path = os.path.join("downloads", file_name)
        await file.download_to_drive(local_path)
        
        available_folders = get_available_folders_count()
        
        if available_folders == 0:
            await processing_msg.edit_text("⚠️ لا توجد مجلدات مفعّلة في الإعدادات")
            os.remove(local_path)
            return
        elif available_folders == 1:
            folder_id = DEFAULT_FOLDER
            await processing_msg.edit_text("☁️ جاري الرفع إلى Drive...")
            loop = asyncio.get_running_loop()
            file_id, error = await loop.run_in_executor(None, partial(upload_to_drive, local_path, folder_id, CREDENTIALS_PATH))
            
            if file_id:
                drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                await processing_msg.edit_text(
                    f"✅ تم رفع الملف!\n📚 {file_name}\n🔗 [رابط Drive]({drive_link})",
                    parse_mode='Markdown'
                )
            else:
                await processing_msg.edit_text(f"❌ فشل الرفع: {error}")
            os.remove(local_path)
        else:
            pending_uploads[user_id] = {'file_path': local_path, 'file_name': file_name}
            await processing_msg.edit_text(
                f"📁 اختر مجلد الرفع:\n📄 {file_name}",
                reply_markup=get_folder_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

@restricted
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video uploads."""
    video = update.message.video
    if not video:
        return
    
    file_size_mb = video.file_size / (1024 * 1024)
    user_id = update.effective_user.id
    
    processing_msg = await update.message.reply_text(f"📥 جاري تحميل الفيديو ({file_size_mb:.1f}MB)...")
    
    try:
        file = await context.bot.get_file(video.file_id)
        os.makedirs("downloads", exist_ok=True)
        video_path = os.path.join("downloads", f"video_{video.file_unique_id}.mp4")
        await file.download_to_drive(video_path)
        
        pending_videos[user_id] = {'video_path': video_path}
        
        await processing_msg.edit_text(
            f"🎬 تم تحميل الفيديو ({file_size_mb:.1f}MB)\n\nاختر ماذا تريد:",
            reply_markup=get_video_choice_keyboard()
        )
            
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

async def handle_folder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle folder selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in pending_uploads:
        await query.edit_message_text("❌ لا يوجد ملف في الانتظار.")
        return
    
    folder_key = query.data.replace("folder_", "")
    folder_id = FOLDERS.get(folder_key, {}).get('id', '')
    folder_name = FOLDERS.get(folder_key, {}).get('name', '')
    
    if not folder_id:
        await query.edit_message_text("❌ المجلد غير متاح.")
        return
    
    upload_info = pending_uploads.pop(user_id)
    file_path = upload_info['file_path']
    file_name = upload_info['file_name']
    
    await query.edit_message_text(f"☁️ جاري الرفع إلى {folder_name}...")
    
    try:
        loop = asyncio.get_running_loop()
        file_id, error = await loop.run_in_executor(None, partial(upload_to_drive, file_path, folder_id, CREDENTIALS_PATH))
        
        if file_id:
            drive_link = f"https://drive.google.com/file/d/{file_id}/view"
            await query.edit_message_text(
                f"✅ تم الرفع!\n📄 {file_name}\n📁 {folder_name}\n🔗 [رابط Drive]({drive_link})",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"❌ فشل الرفع: {error}")
    except Exception as e:
        logger.error(f"Error uploading: {e}")
        await query.edit_message_text(f"❌ خطأ: {str(e)}")
    finally:
        try:
            os.remove(file_path)
        except:
            pass

async def handle_video_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video choice."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in pending_videos:
        await query.edit_message_text("❌ لا يوجد فيديو في الانتظار.")
        return
    
    video_info = pending_videos.pop(user_id)
    video_path = video_info['video_path']
    choice = query.data
    
    try:
        if choice == "video_audio":
            await query.edit_message_text("🎵 جاري استخراج الصوت...")
            audio_path = video_path.replace('.mp4', '.mp3')
            
            # Use current module check for FFmpeg or assume it's in path/service
            from services.youtube_service import get_ffmpeg_location
            ffmpeg_dir = get_ffmpeg_location()
            if ffmpeg_dir:
                ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
            else:
                ffmpeg_exe = 'ffmpeg'
            
            import subprocess
            subprocess.run([
                ffmpeg_exe, '-i', video_path, '-vn', '-acodec', 'libmp3lame', 
                '-ab', '192k', '-y', audio_path
            ], capture_output=True)
            
            os.remove(video_path)
            
            if not os.path.exists(audio_path):
                await query.edit_message_text("❌ فشل استخراج الصوت")
                return
            
            file_path = audio_path
            folder_id = FOLDERS['audio']['id']
            folder_name = FOLDERS['audio']['name']
            
        else:
            file_path = video_path
            folder_id = FOLDERS['video']['id']
            folder_name = FOLDERS['video']['name']
        
        if not folder_id:
            await query.edit_message_text(f"❌ مجلد {folder_name} غير مفعّل")
            os.remove(file_path)
            return
        
        await query.edit_message_text(f"☁️ جاري الرفع إلى {folder_name}...")
        loop = asyncio.get_running_loop()
        file_id, error = await loop.run_in_executor(None, partial(upload_to_drive, file_path, folder_id, CREDENTIALS_PATH))
        
        if file_id:
            drive_link = f"https://drive.google.com/file/d/{file_id}/view"
            emoji = "🎵" if choice == "video_audio" else "🎬"
            await query.edit_message_text(
                f"✅ تم الرفع!\n{emoji} تم!\n📁 {folder_name}\n🔗 [رابط Drive]({drive_link})",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"❌ فشل الرفع: {error}")
        
        try:
           if os.path.exists(file_path): os.remove(file_path)
        except: pass
        
    except Exception as e:
        logger.error(f"Error processing video choice: {e}")
        await query.edit_message_text(f"❌ خطأ: {str(e)}")
