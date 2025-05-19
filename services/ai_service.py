import os
import logging
import json
import anthropic
import openai
from datetime import datetime
from app import db
from models import Article, ArticleStatus, AIModel, APIKey, APIType, ArticleLog, LogType

logger = logging.getLogger(__name__)

def get_api_key(user_id, model_type):
    """
    Obtém a chave de API para o modelo especificado
    
    Args:
        user_id: ID do usuário
        model_type: Tipo de API (APIType.CLAUDE ou APIType.GPT)
        
    Returns:
        str: Chave de API ou None se não encontrada
    """
    api_key = APIKey.query.filter_by(user_id=user_id, type=model_type).first()
    return api_key.key if api_key else None

def generate_content_claude(prompt, user_id, max_tokens=4000):
    """
    Gera conteúdo usando o modelo Claude da Anthropic
    
    Args:
        prompt: Prompt para o modelo
        user_id: ID do usuário (para buscar a chave de API)
        max_tokens: Número máximo de tokens na resposta
        
    Returns:
        str: Texto gerado pelo modelo
    """
    api_key = get_api_key(user_id, APIType.CLAUDE)
    
    if not api_key:
        raise Exception("Chave de API Claude não encontrada")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    except Exception as e:
        logger.error(f"Erro ao gerar conteúdo com Claude: {str(e)}")
        raise Exception(f"Erro ao gerar conteúdo com Claude: {str(e)}")

def generate_content_gpt(prompt, user_id, max_tokens=2000):
    """
    Gera conteúdo usando o modelo GPT da OpenAI
    
    Args:
        prompt: Prompt para o modelo
        user_id: ID do usuário (para buscar a chave de API)
        max_tokens: Número máximo de tokens na resposta
        
    Returns:
        str: Texto gerado pelo modelo
    """
    api_key = get_api_key(user_id, APIType.GPT)
    
    if not api_key:
        raise Exception("Chave de API OpenAI não encontrada")
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em criação de conteúdo para blogs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erro ao gerar conteúdo com GPT: {str(e)}")
        raise Exception(f"Erro ao gerar conteúdo com GPT: {str(e)}")

def generate_article_from_theme(theme, ai_model, user_id, wp_config_id):
    """
    Gera um artigo completo baseado em um tema
    
    Args:
        theme: Objeto AutomationTheme
        ai_model: Modelo de IA a ser usado (AIModel)
        user_id: ID do usuário
        wp_config_id: ID da configuração WordPress
        
    Returns:
        Article: Objeto do artigo gerado
    """
    keywords = theme.keywords.split(',')
    main_keyword = keywords[0].strip()
    
    # Construir prompt para o modelo de IA
    prompt = f"""Gere um artigo de blog completo sobre o tema "{theme.name}" focando na palavra-chave principal "{main_keyword}".
    
Outras palavras-chave relacionadas: {', '.join(keywords[1:5] if len(keywords) > 1 else [])}

O artigo deve ter:
1. Um título atraente e otimizado para SEO
2. Uma introdução envolvente
3. 4-5 seções com subtítulos relevantes
4. Uma conclusão
5. Meta descrição para SEO (limite de 155 caracteres)
6. 5 tags sugeridas

Formate o conteúdo em markdown e separe cada elemento com marcadores específicos:

TITULO: [Título do artigo]

META: [Meta descrição]

TAGS: [tag1, tag2, tag3, tag4, tag5]

CONTEUDO:
[Conteúdo completo do artigo em markdown]
"""
    
    # Gerar conteúdo com o modelo adequado
    try:
        if ai_model == AIModel.CLAUDE:
            response = generate_content_claude(prompt, user_id)
        else:
            response = generate_content_gpt(prompt, user_id)
        
        # Extrair partes do artigo
        titulo = ""
        meta = ""
        tags = ""
        conteudo = ""
        
        # Parsear resposta
        sections = response.split("\n\n")
        for section in sections:
            if section.startswith("TITULO:"):
                titulo = section.replace("TITULO:", "").strip()
            elif section.startswith("META:"):
                meta = section.replace("META:", "").strip()
            elif section.startswith("TAGS:"):
                tags = section.replace("TAGS:", "").strip()
            elif section.startswith("CONTEUDO:"):
                conteudo = section.replace("CONTEUDO:", "").strip()
        
        # Se não conseguiu extrair corretamente, tentar outro método
        if not titulo or not conteudo:
            lines = response.split("\n")
            for i, line in enumerate(lines):
                if "TITULO:" in line:
                    titulo = line.replace("TITULO:", "").strip()
                elif "META:" in line:
                    meta = line.replace("META:", "").strip()
                elif "TAGS:" in line:
                    tags = line.replace("TAGS:", "").strip()
                elif "CONTEUDO:" in line:
                    conteudo = "\n".join(lines[i+1:]).strip()
        
        # Se ainda não conseguiu extrair título, usar o tema como título
        if not titulo:
            titulo = f"Artigo sobre {theme.name}"
        
        # Contar palavras
        word_count = len(conteudo.split())
        
        # Criar artigo
        article = Article(
            title=titulo,
            content=conteudo,
            meta_description=meta[:320] if meta else None,
            tags=tags[:256] if tags else None,
            status=ArticleStatus.DRAFT,
            ai_model=ai_model,
            is_automated=True,
            source_type="keyword",
            keyword=main_keyword,
            word_count=word_count,
            user_id=user_id,
            wordpress_config_id=wp_config_id,
            theme_id=theme.id
        )
        
        db.session.add(article)
        
        # Adicionar log
        log = ArticleLog(
            message=f"Artigo gerado automaticamente a partir do tema '{theme.name}'",
            log_type=LogType.INFO,
            article_id=article.id
        )
        
        db.session.add(log)
        db.session.commit()
        
        return article
    
    except Exception as e:
        logger.error(f"Erro ao gerar artigo a partir do tema: {str(e)}")
        raise e

def generate_article_from_news(news_item, ai_model, user_id, wp_config_id):
    """
    Gera um artigo reescrito a partir de um item de notícia
    
    Args:
        news_item: Objeto NewsItem
        ai_model: Modelo de IA a ser usado (AIModel)
        user_id: ID do usuário
        wp_config_id: ID da configuração WordPress
        
    Returns:
        Article: Objeto do artigo gerado
    """
    # Construir prompt para o modelo de IA
    prompt = f"""Reescreva completamente a notícia abaixo para criar um artigo original para blog.
    
TÍTULO ORIGINAL: {news_item.title}

CONTEÚDO ORIGINAL:
{news_item.content[:5000] if news_item.content else news_item.description[:1000]}

FONTE: {news_item.link}

Reescreva completamente, mudando a estrutura, parágrafo e escolhas de palavras para criar um artigo 100% original, melhorado e informativo.

O artigo deve ter:
1. Um título original (diferente do original)
2. Uma introdução envolvente
3. Conteúdo reescrito e expandido
4. Uma conclusão
5. Meta descrição para SEO (limite de 155 caracteres)
6. 5 tags sugeridas

IMPORTANTE: Não copie frases ou parágrafos do original. Reescreva completamente com suas próprias palavras.

Formate o conteúdo em markdown e separe cada elemento com marcadores específicos:

TITULO: [Título do artigo]

META: [Meta descrição]

TAGS: [tag1, tag2, tag3, tag4, tag5]

CONTEUDO:
[Conteúdo completo do artigo em markdown]
"""
    
    # Gerar conteúdo com o modelo adequado
    try:
        if ai_model == AIModel.CLAUDE:
            response = generate_content_claude(prompt, user_id)
        else:
            response = generate_content_gpt(prompt, user_id)
        
        # Extrair partes do artigo
        titulo = ""
        meta = ""
        tags = ""
        conteudo = ""
        
        # Parsear resposta
        sections = response.split("\n\n")
        for section in sections:
            if section.startswith("TITULO:"):
                titulo = section.replace("TITULO:", "").strip()
            elif section.startswith("META:"):
                meta = section.replace("META:", "").strip()
            elif section.startswith("TAGS:"):
                tags = section.replace("TAGS:", "").strip()
            elif section.startswith("CONTEUDO:"):
                conteudo = section.replace("CONTEUDO:", "").strip()
        
        # Se não conseguiu extrair corretamente, tentar outro método
        if not titulo or not conteudo:
            lines = response.split("\n")
            for i, line in enumerate(lines):
                if "TITULO:" in line:
                    titulo = line.replace("TITULO:", "").strip()
                elif "META:" in line:
                    meta = line.replace("META:", "").strip()
                elif "TAGS:" in line:
                    tags = line.replace("TAGS:", "").strip()
                elif "CONTEUDO:" in line:
                    conteudo = "\n".join(lines[i+1:]).strip()
        
        # Se ainda não conseguiu extrair título, usar o título original
        if not titulo:
            titulo = f"Reescrita: {news_item.title}"
        
        # Contar palavras
        word_count = len(conteudo.split())
        
        # Criar artigo
        article = Article(
            title=titulo,
            content=conteudo,
            meta_description=meta[:320] if meta else None,
            tags=tags[:256] if tags else None,
            status=ArticleStatus.DRAFT,
            ai_model=ai_model,
            is_automated=True,
            source_type="rss",
            source_url=news_item.link,
            word_count=word_count,
            user_id=user_id,
            wordpress_config_id=wp_config_id,
            news_item_id=news_item.id
        )
        
        db.session.add(article)
        
        # Adicionar log
        log = ArticleLog(
            message=f"Artigo gerado automaticamente a partir da notícia '{news_item.title}'",
            log_type=LogType.INFO,
            article_id=article.id
        )
        
        db.session.add(log)
        db.session.commit()
        
        return article
    
    except Exception as e:
        logger.error(f"Erro ao gerar artigo a partir da notícia: {str(e)}")
        raise e