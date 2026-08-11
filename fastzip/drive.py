import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service(credentials_path: Path, token_path: Path):
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.яrun_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def upload_to_drive(service, file_path: Path):
    file_metadata = {'name': file_path.name}
    media = MediaFileUpload(str(file_path), mimetype='application/zip', resumable=True)

    print("Начинаю загрузку в Google Drive...")
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return file.get('id')