"""
Google Drive Upload Service
Uploads files to Google Drive using OAuth 2.0 authentication.
"""

import os
import pickle
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# Scopes required for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_PATH = 'token.pickle'


def get_drive_service(credentials_path: str = "oauth_credentials.json"):
    """
    Create and return a Google Drive service object using OAuth 2.0.
    
    Args:
        credentials_path: Path to the OAuth credentials JSON file
        
    Returns:
        Google Drive service object
    """
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"❌ Credentials file not found: {credentials_path}")
                print("   Please download OAuth credentials from Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future runs
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(
    file_path: str,
    folder_id: str,
    credentials_path: str = "credentials.json"
) -> Optional[str]:
    """
    Upload a file to Google Drive.
    
    Args:
        file_path: Path to the local file to upload
        folder_id: Google Drive folder ID to upload to
        credentials_path: Path to OAuth credentials
        
    Returns:
        The file ID if successful, None if failed
    """
    try:
        service = get_drive_service(credentials_path)
        if service is None:
            return None
        
        # Get file name from path
        file_name = os.path.basename(file_path)
        
        # File metadata
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Determine MIME type based on file extension
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_name)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Create media upload object
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"✅ Uploaded: {file_name}")
        return file.get('id')
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        import traceback
        print(f"❌ Upload error: {str(e)}")
        traceback.print_exc()
        return None


def get_file_link(file_id: str, credentials_path: str = "credentials.json") -> Optional[str]:
    """
    Get the web view link for a file.
    
    Args:
        file_id: The Google Drive file ID
        credentials_path: Path to OAuth credentials
        
    Returns:
        The web view link if successful, None if failed
    """
    try:
        service = get_drive_service(credentials_path)
        if service is None:
            return None
        file = service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        return file.get('webViewLink')
    except Exception as e:
        print(f"❌ Error getting file link: {str(e)}")
        return None


def authenticate():
    """
    Run authentication flow manually.
    Call this once to set up OAuth token.
    """
    print("🔐 Starting OAuth authentication...")
    service = get_drive_service()
    if service:
        print("✅ Authentication successful! Token saved.")
        return True
    return False


if __name__ == "__main__":
    print("Google Drive OAuth Setup")
    print("-" * 40)
    authenticate()
