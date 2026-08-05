#facilitar as importações do main
# Conteúdo obrigatório dentro de src/__init__.py
from .downloader import baixar_video_yt, escolher_mp4
from .audio_extractor import extrair_audio
from .transcriber import transcrever_mapeamento, transcrever_clipe_final, set_config_transcriber
from .clip_selector import selecionar_clipes
from .cutter import cortar
from .subtitles import gerar_legenda
from .composer import compor_gameplay, compor_blur, set_config
from .metadata import gerar_metadata
from .get_anime import identificar_cena
from .hardware_detector import detectar_config_otimizada
from .uploader import upload_video