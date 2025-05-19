"""
Serviço para processamento aprimorado de notícias RSS
Este módulo contém funções mais robustas para lidar com a geração de artigos a partir de feeds
"""

import logging
from datetime import datetime
from app import db
from models import NewsItem, Article, ArticleStatus, ArticleLog, LogType, AIModel
from services.ai_service import generate_article_from_news
from services.rss_service import fetch_and_process_feed

logger = logging.getLogger(__name__)

def process_news_item(news_item, ai_model, user_id, wp_config_id=None):
    """
    Processa uma notícia RSS e gera um artigo a partir dela com tratamento de erros aprimorado
    
    Args:
        news_item: Objeto NewsItem para processar
        ai_model: Enum AIModel (CLAUDE ou GPT)
        user_id: ID do usuário dono da notícia
        wp_config_id: ID opcional da configuração WordPress
        
    Returns:
        tuple: (artigo criado, status de sucesso, mensagem)
    """
    if news_item.is_processed:
        return None, False, "Esta notícia já foi processada anteriormente"
    
    try:
        # Gerar o artigo
        article = Article(
            title=f"Reescrita (em andamento): {news_item.title[:100]}",
            content="Este conteúdo está sendo gerado...",
            status=ArticleStatus.DRAFT,
            ai_model=ai_model,
            is_automated=True,
            source_type="rss",
            source_url=news_item.link,
            user_id=user_id,
            wordpress_config_id=wp_config_id,
            news_item_id=news_item.id
        )
        
        # Salvar o artigo primeiro para obter um ID
        db.session.add(article)
        db.session.flush()
        
        # Criar log inicial
        log = ArticleLog(
            message=f"Iniciando geração de artigo a partir da notícia '{news_item.title}'",
            log_type=LogType.INFO,
            article_id=article.id
        )
        db.session.add(log)
        db.session.commit()
        
        # Agora gerar o conteúdo usando IA
        try:
            # Chamar o serviço de IA para realmente gerar o conteúdo
            final_article = generate_article_from_news(
                news_item=news_item,
                ai_model=ai_model,
                user_id=user_id,
                wp_config_id=wp_config_id,
                existing_article_id=article.id  # Passar o ID do artigo já criado
            )
            
            # Marcar a notícia como processada
            news_item.is_processed = True
            db.session.commit()
            
            return final_article, True, f"Artigo gerado com sucesso: {final_article.title}"
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo do artigo: {str(e)}")
            
            # Ainda assim, manter o artigo rascunho para edição manual
            error_log = ArticleLog(
                message=f"Erro ao gerar conteúdo completo: {str(e)}",
                log_type=LogType.ERROR,
                article_id=article.id
            )
            db.session.add(error_log)
            db.session.commit()
            
            return article, False, f"Erro na geração do conteúdo, mas artigo rascunho foi criado: {str(e)}"
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar artigo a partir da notícia: {str(e)}")
        return None, False, f"Erro ao processar notícia: {str(e)}"

def fetch_process_all_feeds(user_id):
    """
    Busca todos os feeds ativos de um usuário e processa as notícias novas
    
    Args:
        user_id: ID do usuário proprietário dos feeds
        
    Returns:
        dict: Estatísticas de processamento
    """
    from models import RSSFeed
    
    stats = {
        'feeds_processed': 0,
        'feeds_with_errors': 0,
        'new_items': 0
    }
    
    # Buscar todos os feeds ativos do usuário
    feeds = RSSFeed.query.filter_by(user_id=user_id, is_active=True).all()
    
    if not feeds:
        logger.info(f"Nenhum feed ativo encontrado para o usuário {user_id}")
        return stats
    
    # Processar cada feed
    for feed in feeds:
        try:
            new_items, total_items = fetch_and_process_feed(feed)
            stats['new_items'] += new_items
            stats['feeds_processed'] += 1
            
            # Atualizar data de última busca
            feed.last_fetch = datetime.utcnow()
            db.session.commit()
        
        except Exception as e:
            stats['feeds_with_errors'] += 1
            logger.error(f"Erro ao processar feed {feed.name}: {str(e)}")
    
    return stats

def update_ai_service_to_use_existing_article(generate_article_from_news_function):
    """
    Wrapper para estender a função generate_article_from_news para suportar artigos existentes
    
    Args:
        generate_article_from_news_function: Função original
        
    Returns:
        function: Nova função com suporte a artigos existentes
    """
    def wrapper(news_item, ai_model, user_id, wp_config_id=None, existing_article_id=None):
        # A função AI já foi atualizada para suportar existing_article_id
        return generate_article_from_news_function(news_item, ai_model, user_id, wp_config_id, existing_article_id)
    
    return wrapper