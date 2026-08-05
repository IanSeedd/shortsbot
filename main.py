from src import (
    baixar_video_yt, extrair_audio, transcrever_mapeamento, 
    transcrever_clipe_final, set_config_transcriber, selecionar_clipes, 
    cortar, gerar_legenda, compor_gameplay, compor_blur, 
    gerar_metadata, identificar_cena, detectar_config_otimizada, upload_video, set_config,
)
import os
import subprocess
import time
import config

# Variaveis vindas do config.py
VIDEO_PATH = config.PATHS["video_input"]
AUDIO_PATH = config.PATHS["audio_original"]
PRE_DOWNLOAD = config.PRE_DOWNLOAD
URL = config.YOUTUBE_URL
MAX_SHORTS = config.MAX_SHORTS
print("-" * 70)
print("                SHORTS BOT - INICIANDO PROCESSO                ")
print("-" * 70)

# 0. CONFIGURACOES E HARDWARE, ainda não FAZEM ABSOLUTAMENTE NADAAAAAAAAAAAAA
config_hardware = detectar_config_otimizada()
set_config_transcriber({
    'usar_fp16': config_hardware['usar_fp16'],
    'limitar_memoria': config_hardware['limitar_memoria']
})
set_config(config_hardware)

# 1. DOWNLOAD
print(f"\n[1/5] Obtendo conteudo e identificando contexto...")
start_total = time.perf_counter()
if not PRE_DOWNLOAD:
    titulo_yt, desc_yt = baixar_video_yt(URL)
else:
    titulo_yt = None
    desc_yt = None
# 1.5 Identificação
dados_contexto = identificar_cena(titulo_yt, desc_yt, VIDEO_PATH)
nome_do_anime = dados_contexto["anime"]
print(f"Anime Identificado: {nome_do_anime}")
print(f"Dicionario de Golpes: {dados_contexto['contexto'][:100]}...")

# 2. AUDIO E MAPEAMENTO
print("[2/5] Extraindo audio e mapeando falas...")
extrair_audio()
segments_mapeamento = transcrever_mapeamento(AUDIO_PATH, nome_do_anime)

if not segments_mapeamento:
    print("ERRO: Falha ao mapear audio.")
    exit(1)

clips = selecionar_clipes(segments_mapeamento)
clips = clips[:MAX_SHORTS] if len(clips) > MAX_SHORTS else clips
print(f"Clipes selecionados: {len(clips)}")

# 3. PROCESSAMENTO DE CLIPES
print(f"\n[3/5] Iniciando producao de {len(clips)} shorts...")
relatorio_final = []
estatisticas = {'transcricao': 0, 'composicao': 0, 'produzidos': 0, 'uploads': 0}
# Criação dos caminhos, se não existirem
os.makedirs("output/clips", exist_ok=True)
os.makedirs("output/subtitles", exist_ok=True)
os.makedirs("output/final", exist_ok=True)

for i, (start, end) in enumerate(clips, 1):
    print(f"\n>>> Processando Short {i}/{len(clips)} ({start:.1f}s - {end:.1f}s)")
    clip_path = cortar(start, end, i)
    clip_audio_path = f"output/clips/audio_clip_{i:02}.wav"
    
    # Config FFmpeg
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", "input/video.mp4",
        "-t", str(end - start), "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", clip_audio_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Transcricao Premium com dicionario de contexto
    t_trans = time.time()
    segments_premium = transcrever_clipe_final(clip_audio_path, dados_contexto)
    estatisticas['transcricao'] += time.time() - t_trans

    subtitle_path = f"output/subtitles/clip_{i:02}.ass"
    if config.MODELO_VISUAL == "blur":
        # Modelo estilo YouTube Shorts Cinematico
        gerar_legenda(segments_premium, subtitle_path, modelo="blur")
    else:
        # Modelo Split Screen com Gameplay
        gerar_legenda(segments_premium, subtitle_path, modelo="split")
    
    final_video = f"output/final/short_{i:02}.mp4"
    t_comp = time.time()

    if config.MODELO_VISUAL == "blur":
        # Modelo estilo YouTube Shorts Cinematico
        compor_blur(clip_path, "input/watermark.png", subtitle_path, final_video)
    else:
        # Modelo Split Screen com Gameplay
        compor_gameplay("input/gameplay.mp4", clip_path, "input/watermark.png", subtitle_path, final_video)
        
    estatisticas['composicao'] += time.time() - t_comp

    # Geracao de metadados inteligente
    texto_completo = " ".join([s["text"].strip() for s in segments_premium])
    meta = gerar_metadata(texto_completo, dados_contexto)

    # LOGICA DE UPLOAD CENTRALIZADA
    video_id = None
    if config.ENABLE_UPLOAD:
        print(f"Iniciando upload do short {i}...")
        video_id = upload_video(final_video, meta)
        if video_id:
            estatisticas['uploads'] += 1
    else:
        print("Upload desabilitado em config.py - Pulando etapa de envio.")

    relatorio_final.append({
        "id": i,
        "video": final_video,
        "video_id": video_id,
        "titulo": meta['snippet']['title'],
        "descricao": meta['snippet']['description'],
        "trecho": f"{start:.1f}s - {end:.1f}s",
        "contexto_ia": dados_contexto.get("contexto", "Nao identificado") # Puxando do get_anime
    })
    estatisticas['produzidos'] += 1
    print(f"Concluido: {os.path.basename(final_video)}")
    from src.hardware_detector import monitorar_recursos
    if monitorar_recursos():
        print(
            f"Pausando "
            f"{config_hardware['pausa_entre_clipes']} segundos..."
        )

        time.sleep(
            config_hardware['pausa_entre_clipes']
        )

# 5. RESUMO 
tempo_total = time.perf_counter() - start_total
print("\n" + "=" * 70)
print("                    RESUMO DE PRODUCAO FINAL                    ")
print("=" * 70)
print(f"ANIME IDENTIFICADO: {nome_do_anime}")
print(f"DADOS DO CLIPE (get_anime): {dados_contexto.get('contexto', 'Nao identificado')}")
print(f"SHORTS GERADOS: {estatisticas['produzidos']}")
print(f"TEMPO TOTAL: {tempo_total/60:.1f} minutos")
print("-" * 70)
print(
    f"Tempo em transcrições: "
    f"{estatisticas['transcricao']:.1f}s"
)
print(
    f"Tempo em composição: "
    f"{estatisticas['composicao']:.1f}s"
)

for item in relatorio_final:
    print(f"\n[SHORT {item['id']:02}] -> {os.path.basename(item['video'])}")
    print(f"TRECHO: {item['trecho']}")
    print(f"TITULO VIRAL: {item['titulo']}")
    print(f"DESCRICAO: {item['descricao']}")
    print(f"CONTEXTO IA: {item['contexto_ia'][:100]}...") # Mostra o que a IA entendeu da cena
    print("-" * 40)
# Abre a pasta se tiver relatório final, significa que não tiveram erros no processo
if relatorio_final:
    print(f"\nProcesso finalizado com sucesso.")
    if input("Abrir pasta de resultados? (s/n): ").lower() == 's':
        pasta = os.path.abspath("output/final")
        if os.path.exists(pasta):
            import platform
            if platform.system() == "Windows": os.startfile(pasta)
            else: subprocess.run(["open" if platform.system() == "Darwin" else "xdg-open", pasta])