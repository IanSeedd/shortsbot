import gc
import torch
import whisper
import os
from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu" # Decide entre CPU ou GPU (
MODEL_BASE = None 
MODEL_PREMIUM = None
CONFIG = {'usar_fp16': False, 'limitar_memoria': True}

def set_config_transcriber(config):
    global CONFIG
    CONFIG.update(config)
# Carrega os modelos evita repetição no carregamento
def get_model(type):
    global MODEL_BASE
    if type=='base':
        if MODEL_BASE is None:
            print("Carregando Whisper Base...")
            MODEL_BASE = whisper.load_model(
                "base",
                device=DEVICE
            )
        return MODEL_BASE
    global MODEL_PREMIUM
    if type=='premium':
        if MODEL_PREMIUM is None:
            print("Carregando Whisper Large-v3...")
            MODEL_PREMIUM = whisper.load_model(
                "large-v3",
                device=DEVICE
            )
        return MODEL_PREMIUM

def transcrever_rapido_local(audio_path):
    try:
        model = get_model('base')
        result = model.transcribe(
            audio_path,
            language="pt",
            verbose=False,
            fp16=False,
            temperature=0,
            condition_on_previous_text=False
        )

        return result["segments"]
    except: return []

def transcrever_clipe_premium(clipe_audio_path, dados_contexto, legenda_yt=""):
    if not os.path.exists(clipe_audio_path): return []
    
    # Trava de segurança para garantir que temos um dicionário
    if isinstance(dados_contexto, str):
        dados_contexto = {"anime": dados_contexto, "contexto": ""}

    nome_anime = dados_contexto.get("anime", "Anime")
    termos = dados_contexto.get("contexto", "")

    try:
        model = get_model('premium')
        
        whisper_args = {
            'language': 'pt',
            'fp16': CONFIG.get('usar_fp16', False),
            'temperature': 0,
            'word_timestamps': True,
            'no_speech_threshold': 0.3, # Mais sensível para não ignorar o 2º vídeo
            'condition_on_previous_text': False,
            'initial_prompt': f"Vocabulario de {nome_anime}: {termos}."
        }

        with torch.inference_mode():
            result = model.transcribe(
                clipe_audio_path,
                **whisper_args
            )
        
        if not result["segments"]:
            return []
        
        if CONFIG.get("limitar_memoria", False):
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        return corrigir_com_ia_suave(result["segments"], nome_anime, termos)
        
    except Exception as e:
        print(f"Erro na transcrição rápida: {e}")
        return []

def corrigir_com_ia_suave(segmentos, nome_anime, termos):
    textos_originais = [seg['text'].strip() for seg in segmentos if len(seg['text'].strip()) > 1]
    if not textos_originais: return segmentos

    try:
        textos_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(textos_originais)])
        prompt = f"""
        CORRIJA NOMES E GOLPES: {nome_anime}
        CONTEXTO: {termos}
        TEXTOS:
        {textos_str}
        REGRAS CRITICAS:
        1. NAO mude a estrutura da frase.
        2. NAO tente adivinhar o que foi dito se estiver confuso.
        3. Se nao houver erro de nome proprio, retorne a frase EXATAMENTE como recebeu.
        4. Retorne apenas as frases corrigidas, uma por linha.
        5. Tente corrigir nomes de personagens e golpes, lembre-se de se basear no nome do anime e no contexto.
        6. Além disso, corrija erros de concordancia palavras fora do contexto, porém não altere o contexto de forma brusca!
        7. NÃO seja agressivo na correção, não elimine os palavrões.
        8. TENTE entender a cena para corrigi-la de forma mais precisa.

        Exemplo de correção:
        "Katsuki Makumo" para "Katsuki Bakugo"
        "Lady Naga" para "Lady Nagant"
        """
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0
        )
        corrigidos = [l.strip() for l in response.choices[0].message.content.strip().split('\n') if l.strip()]
        
        for i, seg in enumerate(segmentos):
            if i < len(corrigidos):
                seg['text'] = corrigidos[i].upper()
        return segmentos
    except: return segmentos

# FUNCOES DE PONTE PARA O MAIN
def transcrever_mapeamento(audio_path, nome_anime):
    # Tenta usar o áudio limpo pelo Demucs se existir
    target = "input/video_vocals.wav" if os.path.exists("input/video_vocals.wav") else audio_path
    return transcrever_rapido_local(target)

def transcrever_clipe_final(clipe_audio_path, dados_contexto):
    # Esta função agora aceita o dicionário completo 'dados_contexto'
    return transcrever_clipe_premium(clipe_audio_path, dados_contexto)