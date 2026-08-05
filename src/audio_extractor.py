import subprocess
import os
import shutil
import sys
import config
# Caminhos 
VIDEO_INPUT = config.PATHS["video_input"]
AUDIO_ORIGINAL = config.PATHS["audio_original"]
AUDIO_VOCALS = config.PATHS["audio_vocals"]
def extrair_audio():
    # 1. Extrai o áudio original
    subprocess.run([
        "ffmpeg", "-y", "-i", VIDEO_INPUT,
        "-vn", "-ac", "1", "-ar", "16000",
        AUDIO_ORIGINAL
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Separando voz com Demucs...")
    try:
        # 2. SEPARAÇÃO DE VOZ (Demucs)
        # Ele vai criar uma pasta 'separated/htdemucs/video/vocals.wav'
        subprocess.run([
            sys.executable, "-m", "demucs.separate",
            "-n", "htdemucs",
            "--two-stems", "vocals",
            "-o", "input/separado",
            AUDIO_ORIGINAL
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # O Demucs organiza as pastas por modelo, entao o caminho eh um pouco longo
        voz_gerada = "input/separado/htdemucs/video/vocals.wav"
        
        if os.path.exists(voz_gerada):
            shutil.move(voz_gerada, AUDIO_VOCALS)
            print("Voz isolada com sucesso!")
        
    except Exception as e:
        print(f"Aviso: Falha na separacao. Erro: {e}")
        if not os.path.exists(AUDIO_VOCALS):
            shutil.copy(AUDIO_ORIGINAL, AUDIO_VOCALS)
    # Limpeza dos temporarios
    finally:
        if os.path.exists("input/separado"):
            shutil.rmtree("input/separado")