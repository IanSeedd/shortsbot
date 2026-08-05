from src import (
    baixar_video_yt, extrair_audio, transcrever_mapeamento, 
    transcrever_clipe_final, set_config_transcriber, selecionar_clipes, 
    cortar, gerar_legenda, compor_gameplay, compor_blur, 
    gerar_metadata, identificar_cena, detectar_config_otimizada, upload_video, set_config,
)
import config
import os
# Imports do get anime
import glob
import cv2
from groq import Groq

# Variaveis vindas do config.py
VIDEO_PATH = config.PATHS["video_input"]
AUDIO_PATH = config.PATHS["audio_original"]
PRE_DOWNLOAD = config.PRE_DOWNLOAD
URL = config.YOUTUBE_URL
MAX_SHORTS = config.MAX_SHORTS

if not PRE_DOWNLOAD:
    titulo_yt, desc_yt = baixar_video_yt(URL)
else:
    titulo_yt = ''
    desc_yt = ''
# 1.5 Identificação
def hist_calc(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # Transforma em HSV pra fazer o calculo
    # Como essa função é complexa aqui está a cola: 
    # frame, canais(no caso hue e saturation), mask(none porque quero analisar tudo), quant de bins(vai de 0 a 255 mas assim fica melhor), range(limite de valores em cada canal)
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256]) 
    # Transforma a contagem bruta em porcentagem facilitando o calculo final
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return hist
def duplicado(hist_atual, hist_anterior, limiar):
    if hist_anterior is None:
        return False
    calculo = cv2.compareHist(hist_atual, hist_anterior, cv2.HISTCMP_CORREL)
    if calculo >= limiar:
        return True
    return False 
def tirar_print(video_path):
    cap = cv2.VideoCapture(video_path)
    # Cria a pasta
    os.makedirs("input/context_files", exist_ok=True)
    frame_count = 4316 # Começa depois da abertura (teoricamente)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count) 
    sucessos = 0
    if cap.isOpened():
        while True:
            # Skippa o ending:
            if frame_count >= 30920:
                break
            success, frame = cap.read() # Se a variável sucesso for true o frame é lido pelo cap
            if not success: # Caso de errado quebra o loop por segurança
                break 
            
            temp_path = f"input/context_files/context_frame{sucessos}.jpg"
            frame_count += 2 # Antes dos filtros assim eu não preciso ficar reescrevendo isso toda hora
            # Filtros:
            if frame.mean() < 15 or frame.mean() > 240:
                continue
            variance = cv2.Laplacian(frame, cv2.CV_64F).var()
            if variance < 100: # Tira os frames que são borrados 
                continue
            if sucessos < 1:
                hist_anterior = None
            hist_atual = hist_calc(frame)
            if duplicado(hist_atual, hist_anterior, 0.7):
                continue
            cv2.imwrite(temp_path, frame) # Salva o frame com o nome do arquivo(temp_path) 
            hist_anterior = hist_atual
            if sucessos >= 20:
                break
            sucessos += 1 # Assim fica mais facil trabalhar, já que não precisamos de tantas imagens assim
    cap.release()


tirar_print(VIDEO_PATH)
# cenas = glob.glob('input/context_files/*.txt')
# identificar(cenas)
# client = Groq(api_key=config.GROQ_API_KEY)
# def identificar(cenas):
#     # Aqui ele prepara o conteudo da mensagem já mandando as imagens de uma vez só 
#     conteudo = [
#         {
#             "type": "text",
#             "text": "Identify the anime characters in this frame as well as the anime they are from and the season/episode. Please be short and dont detail the process of thinking, give me only what I said.",
#         }
#     ]
#     for caminho in cenas:
#         with open(caminho, "r", encoding="utf-8") as f:
#             b64_string = f.read().strip()
#         conteudo.append(
#             {
#                 "type": "image_url",
#                 "image_url": {"url": f"data:image/jpeg;base64,{b64_string}"},
#             }
#         )
#     response = client.chat.completions.create(
#         model="qwen/qwen3.6-27b",
#         messages=[
#             {
#                 "role": "user",
#                 "content": conteudo
#             }
#         ],
#         temperature=0.1,
#     )
#     print(response.choices[0].message.content)