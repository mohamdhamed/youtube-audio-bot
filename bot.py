from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_BOT_TOKEN, ALLOWED_USERS
from handlers import commands, media, youtube, messages
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def start_health_server():
    """Start HTTP server for cloud health checks."""
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        
        def log_message(self, format, *args):
            pass
    
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 Health server running on port {port}")

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        print("   Create a .env file with: TELEGRAM_BOT_TOKEN=your_token")
        return
    
    print("🚀 Starting YouTube Audio Drive Bot...")
    if ALLOWED_USERS:
        print(f"🔐 Allowed users: {ALLOWED_USERS}")
    else:
        print("⚠️ No user restrictions (ALLOWED_USERS is empty)")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("myid", commands.myid_command))
    
    # Media Handlers
    application.add_handler(MessageHandler(filters.VIDEO, media.handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, media.handle_document))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(media.handle_folder_callback, pattern=r'^folder_'))
    application.add_handler(CallbackQueryHandler(media.handle_video_choice_callback, pattern=r'^video_'))
    
    # Text Messages (YouTube links & Unknown)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_text_message))
    
    # Start
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    start_health_server()
    main()
