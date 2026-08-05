from groq import Groq
import json
import config

client = Groq(api_key=config.GROQ_API_KEY)

def gerar_metadata(texto_transcricao, dados_contexto):
    """
    Usa o dicionário completo do get_anime para gerar SEO agressivo.
    """
    # Extração segura de dados
    if isinstance(dados_contexto, str):
        nome_anime = dados_contexto
        termos_chave = ""
    else:
        nome_anime = dados_contexto.get("anime", "Anime")
        termos_chave = dados_contexto.get("contexto", "")

    # Tags dinâmicas baseadas no anime
    tag_anime = f"#{nome_anime.lower().replace(' ', '')}"
    # Tags fixas
    TAGS_FIXAS = ["#anime", "#animeshorts", "#otaku", tag_anime] 

    try:
        prompt_agressivo = f"""
        VOCÊ É UM EXPERT EM YOUTUBE SHORTS VIRAL (ESTILO RETENÇÃO 100%).
        
        DADOS DA CENA:
        - ANIME: {nome_anime}
        - PERSONAGENS/GOLPES: {termos_chave}
        - O QUE É DITO: "{texto_transcricao}"
        
        TAREFA:
        1. Crie um TÍTULO (máx 100 chars): Use gatilhos de curiosidade, choque ou "clickbait do bem". 
           Se a cena permitir, use um duplo sentido sutil ou humor ácido. 
           OBRIGATÓRIO: Use emojis e termine com #shorts.
        
        2. Crie uma DESCRIÇÃO (2 linhas): Primeira linha deve ser um CTA (Call to Action) chamativo. 
           Segunda linha deve deve ser um chamado para inscrição e like.

        EXEMPLOS DE ESTILO:
        - "Ele realmente usou ISSO!? 😱 #shorts"
        - "O jeito que ele olhou pra ela... 😏 #shorts"
        - "Ninguém esperava por esse final! 🔥 #shorts"

        RESPONDA APENAS JSON:
        {{
            "titulo": "...",
            "descricao": "..."
        }}
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Expert em retenção e algoritmos de vídeo curto. Resposta apenas JSON."},
                {"role": "user", "content": prompt_agressivo}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.8 # Um pouco de criatividade para os títulos
        )

        dados = json.loads(chat_completion.choices[0].message.content)
        
        # Limpeza e Formatação
        titulo = dados.get("titulo", f"Momento Épico em {nome_anime}").strip()
        # Garante que o título não tenha aspas duplas internas que quebram o sistema
        titulo = titulo.replace('"', '')
        
        descricao = dados.get("descricao", "Assista até o fim para entender! #anime").strip()

        return {
            "snippet": {
                "title": titulo,
                "description": f"{descricao}\n\n{ ' '.join(TAGS_FIXAS) }",
                "tags": TAGS_FIXAS, 
                "categoryId": "1"
            },
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
        }
        
    except Exception as e:
        print(f"Erro no Metadata: {e}")
        return {
            "snippet": {
                "title": f"O final vai te surpreender! 😱 #{nome_anime} #shorts",
                "description": "Momentos épicos de anime todos os dias!",
                "tags": TAGS_FIXAS,
                "categoryId": "1"
            },
            "status": {"privacyStatus": "private"}
        }