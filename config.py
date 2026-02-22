import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

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

# Dashboard settings
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'admin123')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))


def reload_config():
    """Reload all configuration from .env file without restarting."""
    global TELEGRAM_BOT_TOKEN, CREDENTIALS_PATH, FOLDERS, GOOGLE_DRIVE_FOLDER_ID
    global GOOGLE_DRIVE_PDF_FOLDER_ID, DEFAULT_FOLDER, ALLOWED_USERS_STR, ALLOWED_USERS
    global DASHBOARD_PASSWORD, DASHBOARD_PORT

    load_dotenv(override=True)

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

    FOLDERS['audio']['id'] = os.getenv('FOLDER_AUDIO', '')
    FOLDERS['video']['id'] = os.getenv('FOLDER_VIDEO', '')
    FOLDERS['books']['id'] = os.getenv('FOLDER_BOOKS', '')
    FOLDERS['other']['id'] = os.getenv('FOLDER_OTHER', '')

    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    GOOGLE_DRIVE_PDF_FOLDER_ID = os.getenv('GOOGLE_DRIVE_PDF_FOLDER_ID')
    DEFAULT_FOLDER = next((f['id'] for f in FOLDERS.values() if f['id']), GOOGLE_DRIVE_FOLDER_ID)

    ALLOWED_USERS_STR = os.getenv('ALLOWED_USERS', '')
    ALLOWED_USERS.clear()
    ALLOWED_USERS.update(int(uid.strip()) for uid in ALLOWED_USERS_STR.split(',') if uid.strip())

    DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'admin123')
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))

    logger.info("✅ Config reloaded from .env")
