# YouTube Audio Drive Bot

This Telegram bot accepts YouTube video URLs, converts them to MP3 audio, sends the audio back to you, and uploads it to Google Drive.

## Prerequisites

1. **Python 3.9+**
2. **FFmpeg** - Install from https://ffmpeg.org/download.html
3. **Telegram Bot Token** - Get from @BotFather
4. **Google Cloud Service Account** - JSON file with Drive API enabled

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id_here
   ```

3. Place your `credentials.json` (Google Service Account) in this directory.

4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

1. Send a YouTube link to the bot
2. Wait for processing
3. Receive the audio file in chat
4. Audio is also uploaded to your Google Drive folder
