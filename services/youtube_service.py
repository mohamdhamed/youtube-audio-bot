"""
YouTube Audio Download Service
Downloads YouTube videos and converts them to MP3 audio files.
"""

import os
import yt_dlp
from typing import Optional, Tuple


def download_audio(youtube_url: str, output_dir: str = "downloads") -> Tuple[Optional[str], Optional[str]]:
    """
    Download audio from a YouTube video and convert to MP3.
    
    Args:
        youtube_url: The YouTube video URL
        output_dir: Directory to save the audio file
        
    Returns:
        Tuple of (file_path, title) if successful, (None, error_message) if failed
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure yt-dlp options
    # FFmpeg path - try common locations
    import os as _os
    ffmpeg_paths = [
        _os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin'),
        _os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links'),
        r'C:\ffmpeg\bin',
        r'C:\Program Files\ffmpeg\bin',
    ]
    ffmpeg_location = None
    for path in ffmpeg_paths:
        if _os.path.exists(_os.path.join(path, 'ffmpeg.exe')):
            ffmpeg_location = path
            break
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info = ydl.extract_info(youtube_url, download=True)
            
            if info is None:
                return None, "Failed to extract video information"
            
            # Get the title and construct the output filename
            title = info.get('title', 'audio')
            # Clean the title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            output_path = os.path.join(output_dir, f"{safe_title}.mp3")
            
            # yt-dlp may create file with original title, find it
            for file in os.listdir(output_dir):
                if file.endswith('.mp3') and title[:20] in file:
                    output_path = os.path.join(output_dir, file)
                    break
            
            if os.path.exists(output_path):
                return output_path, title
            
            # Try to find any newly created mp3 file
            for file in os.listdir(output_dir):
                if file.endswith('.mp3'):
                    full_path = os.path.join(output_dir, file)
                    # Check if this is a recently created file
                    if os.path.getctime(full_path) > os.path.getctime(output_dir):
                        return full_path, title
            
            return None, "Audio file not found after download"
            
    except yt_dlp.DownloadError as e:
        return None, f"Download error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


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
        result, title = download_audio(test_url)
        if result:
            print(f"✅ Downloaded: {result}")
            print(f"   Title: {title}")
        else:
            print(f"❌ Error: {title}")
    else:
        print("❌ Not a valid YouTube URL")
