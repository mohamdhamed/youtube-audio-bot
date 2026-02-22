"""
YouTube Audio Download Service
Downloads YouTube videos and converts them to MP3 audio files.
"""

import os
import yt_dlp
from typing import Optional, Tuple


def get_ffmpeg_location() -> Optional[str]:
    """
    Detect FFmpeg location on the system.
    
    Returns:
        Path to FFmpeg directory, or None if in system PATH
    """
    import shutil
    
    # Check environment variable first
    ffmpeg_location = os.getenv('FFMPEG_PATH')
    if ffmpeg_location:
        return ffmpeg_location
    
    # If ffmpeg is in PATH, no need to specify location
    if shutil.which('ffmpeg'):
        return None
    
    # Only check common Windows paths if not found in PATH
    if os.name == 'nt':
        ffmpeg_paths = [
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin'),
            r'C:\ffmpeg\bin',
            r'C:\Program Files\ffmpeg\bin',
        ]
        for path in ffmpeg_paths:
            if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
                return path
    
    return None


def download_audio(youtube_url: str, output_dir: str = "downloads") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Download audio from a YouTube video and convert to MP3.
    
    Returns:
        Tuple of (file_path, title, thumbnail_path) if successful
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # FFmpeg detection
    ffmpeg_location = get_ffmpeg_location()

    # 1. Extract info first (without downloading) to get ID and Title
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            if not info:
                return None, "Failed to extract video info", None
            
            video_id = info.get('id')
            title = info.get('title', 'audio')
            
            # Use ID for filename to avoid special char issues
            filename = f"{video_id}.mp3"
            output_path = os.path.join(output_dir, filename)

    except Exception as e:
        return None, f"Extraction error: {str(e)}", None

    # 2. Download with deterministic filename
    ydl_opts = {
        'format': 'bestaudio/best',
        # Write thumbnail to disk so we can embed it
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            # Embed thumbnail in the audio file
            {'key': 'EmbedThumbnail'},
            # Add metadata (Title, Artist, etc.)
            {'key': 'FFmpegMetadata'},
        ],
        'outtmpl': os.path.join(output_dir, f'{video_id}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'overwrite': True,
    }
    
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            
            # Find thumbnail
            thumbnail_path = None
            for ext in ['jpg', 'jpeg', 'webp', 'png']:
                potential_thumb = os.path.join(output_dir, f"{video_id}.{ext}")
                if os.path.exists(potential_thumb):
                    thumbnail_path = potential_thumb
                    break
            
            if os.path.exists(output_path):
                return output_path, title, thumbnail_path
            
            return None, "Audio file not found after download (logic error)", None
            
    except yt_dlp.DownloadError as e:
        return None, f"Download error: {str(e)}", None
    except Exception as e:
        return None, f"Unexpected error: {str(e)}", None



def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a valid YouTube URL.
    
    Args:
        url: The URL to check
        
    Returns:
        True if it's a YouTube URL, False otherwise
    """
    youtube_patterns = [
        'youtube.com/watch',
        'youtu.be/',
        'youtube.com/shorts/',
        'youtube.com/v/',
        'youtube.com/embed/',
    ]
    return any(pattern in url.lower() for pattern in youtube_patterns)


if __name__ == "__main__":
    # Test the service
    test_url = input("Enter YouTube URL to test: ")
    if is_youtube_url(test_url):
        result, title, thumb = download_audio(test_url)
        if result:
            print(f"✅ Downloaded: {result}")
            print(f"   Title: {title}")
        else:
            print(f"❌ Error: {title}")
    else:
        print("❌ Not a valid YouTube URL")
