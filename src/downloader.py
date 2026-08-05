import subprocess
import sys
import os
import json
import glob

# Função que retorna o index do MP4 na lista do glob
# Faça pastas para separar os videos do efeito ou o youtube por exemplo, não esquece de verificação de pastas
# Stremio parece ser a chave e não esquece de fazer o analisador de SEO
def escolher_mp4():
    mp4_dispo = glob.glob('input/*.mp4')
    if mp4_dispo:
        if len(mp4_dispo) > 1:
            for i in mp4_dispo:
                print(f'{mp4_dispo.index(i)+1} {i}')
            while True:
                try:
                    escolha = int(input("Qual MP4 deseja usar?: "))
                except ValueError:
                    print("Digite um número válido")
                    continue
                if 0 < escolha <= len(mp4_dispo):
                    return f'{mp4_dispo[escolha - 1]}'
                else:
                    print("Opção inválida")
        else:
            return f'{mp4_dispo[0]}'
    else:
        # Fallback caso seja o primeiro download e por algum motivo a logica do config não funcione
        return "input/video.mp4"

def atualizar_downloader():
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], 
                       capture_output=True)
    except: pass

def baixar_video_yt(url):
    atualizar_downloader()
    if not os.path.exists("input"): os.makedirs("input")
    
    for f in ["input/video.mp4", "input/legenda_nativa.txt", "input/metadata.json"]:
        if os.path.exists(f): os.remove(f)

    print(f"--- Baixando vídeo e metadados: {url} ---")
    
    comando = [
        "yt-dlp",
        "-f", "bv*[height<=720]+ba/best",
        "--merge-output-format", "mp4",
        "--write-info-json",       # EXTRAI TÍTULO E DESCRIÇÃO
        "--write-auto-subs",
        "--sub-langs", "pt.*",
        "--ignore-errors",
        "-o", "input/video.mp4",
        url
    ]
    
    try:
        subprocess.run(comando) 

        if os.path.exists("input/video.mp4"):
            print("Download concluído.")
            processar_legenda_nativa()
            
            # Extrai título e descrição do JSON gerado pelo yt-dlp
            info_file = "input/video.info.json"
            if os.path.exists(info_file):
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                return info.get('title', ''), info.get('description', '')
        return "", ""
    except Exception as e:
        print(f"Falha no download: {e}")
        return "", ""
    
def processar_legenda_nativa():
    # Procura o arquivo de legenda (pode vir como .vtt ou .srt)
    arquivos_legenda = [f for f in os.listdir("input") if f.endswith(('.vtt', '.srt'))]
    output_texto = "input/legenda_nativa.txt"

    if arquivos_legenda:
        caminho_origem = os.path.join("input", arquivos_legenda[0])
        print(f"Legenda encontrada: {caminho_origem}. Extraindo texto...")
        try:
            with open(caminho_origem, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            # Limpa metadados e timestamps para deixar apenas o texto puro para a IA
            texto_limpo = []
            for linha in linhas:
                if '-->' not in linha and 'WEBVTT' not in linha and linha.strip():
                    # Remove tags de estilo comuns em VTT
                    limpa = linha.replace('<c>', '').replace('</c>', '').strip()
                    if limpa: texto_limpo.append(limpa)

            with open(output_texto, 'w', encoding='utf-8') as f:
                f.write(" ".join(texto_limpo))
            print("Gabarito de legenda pronto para o transcritor.")
        except Exception as e:
            print(f"Erro ao limpar legenda: {e}")
    else:
        print("Aviso: Nenhuma legenda nativa extraída. O Whisper trabalhará sozinho.")
        with open(output_texto, 'w') as f: f.write("")