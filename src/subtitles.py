import os

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def gerar_legenda(segments, output_path, modelo="blur"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080", "PlayResY: 1920",
        "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Estilo para modelo blur (posicionado mais para baixo - y=350)
        "Style: Top,Arial Black,85,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,8,30,30,1500,1",  # 350 em cima
        # Estilo para modelo split (centro)
        "Style: Center,Arial Black,105,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,10,0,5,30,30,960,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    lines = header.copy()
    MAX_WORD_DURATION = 1.5
    
    for seg in segments:
        if 'words' in seg:
            words = seg['words']
            chunk_size = 6 
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                if not chunk: continue

                for j, target_word in enumerate(chunk):
                    start_w = target_word['start']
                    
                    if j < len(chunk) - 1:
                        end_w = chunk[j+1]['start']
                    else:
                        real_end = target_word['end']
                        if (real_end - start_w) > MAX_WORD_DURATION:
                            end_w = start_w + MAX_WORD_DURATION
                        else:
                            end_w = real_end
                    
                    ts_start = format_timestamp(start_w)
                    ts_end = format_timestamp(end_w)
                    
                    text_parts = []
                    for k, w in enumerate(chunk):
                        word_text = w['word'].strip().upper()
                        if k == j:
                            text_parts.append(f"{{\\1c&H00FFFF&}}{word_text}{{\\1c&HFFFFFF&}}")
                        else:
                            text_parts.append(word_text)
                    
                    meio = len(text_parts) // 2
                    if len(text_parts) > 3:
                        texto_final = " ".join(text_parts[:meio+1]) + "\\N" + " ".join(text_parts[meio+1:])
                    else:
                        texto_final = " ".join(text_parts)

                    # Usa estilo diferente baseado no modelo
                    estilo = "Top" if modelo == "blur" else "Center"
                    lines.append(f"Dialogue: 0,{ts_start},{ts_end},{estilo},,0,0,0,,{texto_final}")
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))