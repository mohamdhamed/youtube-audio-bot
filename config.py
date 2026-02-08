import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Credentials
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

# Drive Folders
FOLDERS = {
    'audio': {'id': os.getenv('FOLDER_AUDIO', ''), 'name': '🎵 صوت', 'emoji': '🎵'},
    'video': {'id': os.getenv('FOLDER_VIDEO', ''), 'name': '🎬 فيديو', 'emoji': '🎬'},
    'books': {'id': os.getenv('FOLDER_BOOKS', ''), 'name': '📚 كتب', 'emoji': '📚'},
    'other': {'id': os.getenv('FOLDER_OTHER', ''), 'name': '📁 أخرى', 'emoji': '📁'},
}

# Backwards compatibility
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
GOOGLE_DRIVE_PDF_FOLDER_ID = os.getenv('GOOGLE_DRIVE_PDF_FOLDER_ID')
DEFAULT_FOLDER = next((f['id'] for f in FOLDERS.values() if f['id']), GOOGLE_DRIVE_FOLDER_ID)

# User permissions
ALLOWED_USERS_STR = os.getenv('ALLOWED_USERS', '')
ALLOWED_USERS = set(int(uid.strip()) for uid in ALLOWED_USERS_STR.split(',') if uid.strip())
