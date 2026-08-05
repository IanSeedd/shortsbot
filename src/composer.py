import subprocess
import os
import config
import platform
# Prepara a legenda para ambos os modelos
def preparar_legenda(subtitle):
    abs_path = os.path.abspath(subtitle).replace("\\", "/")
    return abs_path.replace(":", "\\:")
def set_config(config): # Tenta pegar o thread do ffmpeg se não pegar usa 4 como padrão 
    global THREADS_FFMPEG
    THREADS_FFMPEG = config.get(
        'threads_ffmpeg',
        4
    )
def compor_blur(clip, watermark, subtitle, output):
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    subtitle_path = preparar_legenda(subtitle)
    nome_canal = config.NOME_CANAL.upper()

    # Pega uma fonte
    if platform.system() == "Windows":
        FONT = "C\\:/Windows/Fonts/arialbd.ttf"
    else:
        FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    filter_complex = (
    # 0. INVERTE APENAS O VIDEO DO ANIME (INPUT 1), separando em 3 labels para não ter erros no consumo.
    "[1:v]hflip,split=3[anime_bg][anime_glass][anime_fg];"

    # 1. FUNDO BORRADO (BASE) 
    "[anime_bg]scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,"
    "boxblur=25:10,"
    "eq=brightness=-0.3[bg];"

    # 2. LIQUID GLASS (ENTRE FUNDO E CONTEÚDO) 
    "[anime_glass]scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,"
    "crop=1500:1100:90:300," # alterei para 1000 e era 900 se algo ficar estranho corrige isso aqui
    "boxblur=30:10,"
    "eq=brightness=0.08:contrast=1.05,"
    "format=rgba,colorchannelmixer=aa=0.35[glass];"

    # 3. FUNDO + GLASS
    "[bg][glass]overlay=90:300:format=auto[bg_glass];"

    # 4. CONTEÚDO PRINCIPAL (CENTRO) 
    "[anime_fg]scale=1080:1200:force_original_aspect_ratio=increase,"
    "crop=1080:1200[fg_scaled];"

    # 5. JUNTA O CONTEÚDO PRINCIPAL COM O COMPLEXO DO FUNDO
    "[bg_glass][fg_scaled]overlay=(W-w)/2:(H-h)/2+100:format=auto[v_temp];"

    # 6. TRATA AS MARCAS D'ÁGUA (Consome a imagem do Input 2)
    "[2:v]scale=160:160,format=rgba,geq=lum='p(X,Y)':a='if(gt(hypot(X-80,Y-80),80),0,255)'[wm_circ];"
    "[2:v]scale=120:-1,format=rgba,colorchannelmixer=aa=0.3[wm_sutil];"

    # 7. APLICA MARCA D'ÁGUA E TEXTOS DA @GISELLECORTESBR DE FORMA ESTÁTICA PELA FONTE
    "[v_temp][wm_sutil]overlay=W-w-50:H/2+600-h-80[v_com_wm_sutil];"
    f"[v_com_wm_sutil]drawtext=text='{nome_canal}':fontcolor=white@0.3:fontsize=18:x=W-tw-50:y=H/2+530-40:borderw=2:bordercolor=black@0.3:fontfile='{FONT}'[v_com_nome_sutil];"
    "[v_com_nome_sutil][wm_circ]overlay=60:290[v_with_wm_top];"
    f"[v_with_wm_top]drawtext=text='{nome_canal}':fontcolor=white:fontsize=50:x=250:y=345:borderw=3:bordercolor=black:fontfile='{FONT}'[v_with_text];"
    
    # 8. RENDERIZA A LEGENDA POR CIMA DE TUDO NO FINAL, TOTALMENTE RETA E SÓLIDA
    f"[v_with_text]ass='{subtitle_path}'"
    )

    executar_ffmpeg(None, clip, watermark, filter_complex, output)

# Essa ta quebrada
def compor_gameplay(gameplay, clip, watermark, subtitle, output):
    # Modelo Split Screen (mantém estilo Center)
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    subtitle_path = preparar_legenda(subtitle)

    filter_complex = (
        "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vtop];"
        "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vbot];"
        "[vtop][vbot]vstack=inputs=2[vstacked];"
        "[2:v]scale=iw*0.8:ih*0.8,format=rgba,colorchannelmixer=aa=0.4[vwm];"
        "[vstacked][vwm]overlay=(W-w)/2:(H-h)/2[vwith_wm];"
        f"[vwith_wm]ass='{subtitle_path}'" 
    )

    executar_ffmpeg(gameplay, clip, watermark, filter_complex, output)

def executar_ffmpeg(gameplay, clip, watermark, filter_complex, output):
    cmd = ["ffmpeg", "-y"]
    
    # Input 0: Gameplay (se houver) ou cor preta
    if gameplay: 
        cmd.extend(["-i", gameplay])
    else: 
        cmd.extend(["-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1"])
    
    # Input 1: Clipe de Anime | Input 2: Marca d'agua
    cmd.extend(["-i", clip, "-i", watermark])
    
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "1:a", # Audio sempre do anime
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output
    ])
    
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )