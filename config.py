# config.py
from src import escolher_mp4
import os
from dotenv import load_dotenv
load_dotenv()

# --- API KEYS ---
GROQ_API_KEY = os.getenv('GROQ_KEY')

# --- CONFIGURAÇÕES DE DOWNLOAD E PRODUÇÃO ---
YOUTUBE_URL = "https://www.youtube.com/watch?v=4Jj4seBjntg"
MAX_SHORTS = 1
PRE_DOWNLOAD = True
VIDEO_LANGUAGE = "pt"
MODELO_VISUAL = "blur" # Opcoes: "gameplay" ou "blur"
NOME_CANAL = "@GISELLECORTESBR"

# --- CONFIGURAÇÕES DE UPLOAD ---
ENABLE_UPLOAD = False  # Mude para False se quiser apenas testar a edição
VIDEO_PRIVACY_STATUS = "unlisted" # "private", "public" ou "unlisted"

if PRE_DOWNLOAD == True:
    video_input = escolher_mp4()
else:
    video_input = "input/video.mp4"
print(video_input) # Apenas para debugar

# --- CAMINHOS DE ARQUIVOS (PATHS) ---
PATHS = {
    "video_input": video_input,
    "audio_original": "input/video.wav",
    "audio_vocals": "input/video_vocals.wav",
    "output_folder": "output/final",
    "metadata_json": "output/relatorio_producao.json"
}