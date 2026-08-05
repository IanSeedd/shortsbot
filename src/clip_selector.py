import numpy as np
from scipy.io import wavfile
import os

AUDIO_PATH = "input/video.wav"

def analisar_energia_audio(clip_start, clip_end):
    try:
        sample_rate, audio_data = wavfile.read(AUDIO_PATH)
        if len(audio_data.shape) > 1: audio_data = audio_data.mean(axis=1)
        
        start_idx, end_idx = int(clip_start * sample_rate), int(clip_end * sample_rate)
        clip_audio = audio_data[max(0, start_idx):min(end_idx, len(audio_data))]
        
        if len(clip_audio) == 0: return 0
        
        segment_size = sample_rate
        rms = [np.sqrt(np.mean(clip_audio[i:i+segment_size]**2)) 
               for i in range(0, len(clip_audio), segment_size) if len(clip_audio[i:i+segment_size]) > 0]
        
        if not rms: return 0
        return np.std(rms) / (np.mean(rms) + 1e-10)
    except: return 0

def analisar_densidade_dialogo(segments, clip_start, clip_end):
    # AJUSTE: O modelo 'base' pode gerar muitos segmentos vazios ou com apenas espaços. 
    # Filtramos para contar apenas fala real.
    clip_segments = [s for s in segments if s["start"] >= clip_start and s["end"] <= clip_end and s["text"].strip()]
    
    if not clip_segments: return 0
    tempo_fala = sum(s["end"] - s["start"] for s in clip_segments)
    densidade = tempo_fala / (clip_end - clip_start)
    
    # Melhores clipes para Shorts têm boa densidade de fala
    return 1.0 if 0.4 <= densidade <= 0.8 else 0.6

def calcular_score_clip(segments, start, end, energia, dialogo):
    duracao = end - start
    # Score de duração ideal (40s é o alvo para Shorts)
    score_duracao = 1.0 - abs(40 - duracao) / 40
    return (score_duracao * 0.4) + (min(energia * 5, 1.0) * 0.3) + (dialogo * 0.3)

def selecionar_clipes(segments, min_dur=30, max_dur=55, num_clipes=3):
    # AJUSTE: Limpeza inicial dos segmentos do transcritor 'base'
    # Remove segmentos sem texto para não confundir o seletor de janelas
    segments = [s for s in segments if s["text"].strip()]
    
    if not segments: 
        print("Aviso: Nenhum segmento de fala útil encontrado no mapeamento.")
        return [(0, min(max_dur, 60))]

    video_duration = segments[-1]["end"]
    print(f"Analisando vídeo de {video_duration:.1f}s buscando {num_clipes} clipes distintos...")

    tamanho_janela = video_duration / num_clipes
    melhores_clipes = []

    for i in range(num_clipes):
        janela_inicio = i * tamanho_janela
        janela_fim = (i + 1) * tamanho_janela
        
        seg_janela = [s for s in segments if s["start"] >= janela_inicio and s["end"] <= janela_fim]
        
        if not seg_janela: continue

        candidatos_janela = []
        
        for idx in range(len(seg_janela)):
            clip_start = seg_janela[idx]["start"]
            
            for j in range(idx + 1, len(seg_janela)):
                clip_end = seg_janela[j]["end"]
                duracao = clip_end - clip_start
                
                if min_dur <= duracao <= max_dur:
                    energia = analisar_energia_audio(clip_start, clip_end)
                    dialogo = analisar_densidade_dialogo(segments, clip_start, clip_end)
                    score = calcular_score_clip(segments, clip_start, clip_end, energia, dialogo)
                    
                    candidatos_janela.append({
                        'start': clip_start, 
                        'end': clip_end, 
                        'score': score
                    })
                
                if duracao > max_dur: break

        if candidatos_janela:
            melhor_da_janela = max(candidatos_janela, key=lambda x: x['score'])
            melhores_clipes.append(melhor_da_janela)

    melhores_clipes.sort(key=lambda x: x['start'])
    
    print(f"Seleção finalizada: {len(melhores_clipes)} clipes encontrados.")
    return [(c['start'], c['end']) for c in melhores_clipes]