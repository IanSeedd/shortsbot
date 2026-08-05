import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import config 

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]
TOKEN_FILE = "token.json"
CLIENT_SECRET = "client_secret.json"

def get_youtube():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove(TOKEN_FILE)
                return get_youtube()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
            
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def verificar_canal(youtube):
    canal = youtube.channels().list(part="id", mine=True).execute()
    # Usa o ID do config.py
    if canal["items"][0]["id"] != config.YOUTUBE_CHANNEL_ID:
        raise Exception(f"UPLOAD BLOQUEADO! Canal conectado ({canal['items'][0]['id']}) não é o permitido.")

def upload_video(video_path, meta_pronta):
    """
    Realiza o upload se a flag ENABLE_UPLOAD estiver ativa.
    """
    if not config.ENABLE_UPLOAD:
        print(">>> Upload desativado no config.py. Pulando etapa.")
        return

    if not os.path.exists(video_path):
        print(f"Vídeo não encontrado: {video_path}")
        return

    # Força o status de privacidade definido no config
    meta_pronta['status'] = {
        "privacyStatus": config.VIDEO_PRIVACY_STATUS,
        "selfDeclaredMadeForKids": False
    }

    try:
        youtube = get_youtube()
        verificar_canal(youtube)

        print(f"Enviando para o YouTube: {meta_pronta['snippet']['title']}")

        request = youtube.videos().insert(
            part="snippet,status",
            body=meta_pronta,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )
        response = request.execute()
        print(f"Sucesso! Vídeo ID: {response['id']}")
        return response['id']
    except Exception as e:
        print(f"Erro no upload: {e}")
        return None