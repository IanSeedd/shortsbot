import cv2
import base64
import os
from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY)

def identificar_cena(titulo="", descricao="", video_path="input/video.mp4"):
    print("Iniciando Identificacao de Contexto com Auto-Update...")
    
    # 1. Captura de Frame
    b64_image = ""
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.5))
        success, frame = cap.read()
        if success:
            temp_path = "input/context_frame.jpg"
            cv2.imwrite(temp_path, frame)
            with open(temp_path, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode('utf-8')
            if os.path.exists(temp_path): os.remove(temp_path)
    cap.release()

    # --- LOGICA DE ATUALIZACAO AUTOMATICA DOS MODELOS ---
    # Lista de modelos por ordem de prioridade (do mais novo para o mais estável)
    modelos_vision = ["llama3.2-vision"]
    modelos_texto = ["llama-3.3-70b-versatile", "llama3-70b-8192"]
    
    contexto_visual = "Nenhum dado visual obtido"
    
    # Tentativa Dinâmica para Visão
    if b64_image:
        for model in modelos_vision:
            try:
                response_vision = client.chat.completions.create(
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "Identify the characters and anime in this frame."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]}],
                    model=model,
                )
                contexto_visual = response_vision.choices[0].message.content.strip()
                break # Se funcionou, sai do loop
            except Exception as e:
                print(f"Aviso: Modelo {model} falhou ou descontinuado. Tentando proximo...")
                continue

    # Tentativa Dinâmica para Veredito Final
    prompt_final = f"""
    Identify Official Anime Name and 15 technical terms (moves/characters).
    Evidence: {titulo} | {descricao[:200]} | Visual: {contexto_visual}
    Format:
    Anime: [Name]
    Terms: [Term1, Term2...]
    """

    for model_text in modelos_texto:
        try:
            final_res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_final}],
                model=model_text,
                temperature=0
            )
            resposta = final_res.choices[0].message.content.strip()
            
            # Parsing
            nome_anime = "Anime"
            termos_contexto = "golpes, ataques"
            for linha in resposta.split('\n'):
                if "Anime:" in linha: nome_anime = linha.split("Anime:")[1].strip()
                if "Terms:" in linha: termos_contexto = linha.split("Terms:")[1].strip()
            
            print(f"Resultado final obtido com: {model_text}")
            return {"anime": nome_anime, "contexto": termos_contexto}
            
        except Exception as e:
            print(f"Erro no modelo {model_text}. Tentando fallback...")
            continue

    # Fallback Crítico (Se tudo der errado)
    return {"anime": titulo.split()[0] if titulo else "Anime", "contexto": "luta, acao"}