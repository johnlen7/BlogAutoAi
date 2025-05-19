import os
import logging
import feedparser
import trafilatura
import html2text
from datetime import datetime, timezone
from urllib.parse import urlparse
from app import db
from models import RSSFeed, NewsItem, Article, ArticleStatus, AIModel

logger = logging.getLogger(__name__)
h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = False
h2t.ignore_tables = False

def fetch_and_process_feed(feed):
    """
    Busca e processa um feed RSS, salvando novos itens no banco de dados
    
    Args:
        feed: Objeto RSSFeed do banco de dados
        
    Returns:
        tuple: (quantidade de novos itens, total de itens no feed)
    """
    logger.info(f"Buscando feed: {feed.name} ({feed.url})")
    
    try:
        # Fazer o parse do feed
        parsed = feedparser.parse(feed.url)
        
        if parsed.bozo == 1:
            # Feed inválido
            logger.error(f"Erro ao processar feed {feed.name}: {parsed.bozo_exception}")
            return 0, 0
        
        # Processar entradas
        new_items_count = 0
        total_items = len(parsed.entries)
        
        for entry in parsed.entries:
            # Obter GUID ou link como identificador único
            guid = getattr(entry, 'id', entry.link)
            
            # Verificar se o item já existe
            existing_item = NewsItem.query.filter_by(guid=guid).first()
            if existing_item:
                continue
            
            # Obter data de publicação (se disponível)
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    pass
            
            # Obtendo o conteúdo
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'description') and entry.description:
                content = entry.description
            
            # Extrair o texto completo do link
            full_content = ""
            try:
                downloaded = trafilatura.fetch_url(entry.link)
                full_content = trafilatura.extract(downloaded) or ""
            except Exception as e:
                logger.warning(f"Erro ao extrair conteúdo de {entry.link}: {str(e)}")
            
            # Se não conseguiu extrair conteúdo pelo trafilatura, usar o que já temos
            if not full_content and content:
                full_content = h2t.handle(content)
            
            # Criar novo item de notícia
            news_item = NewsItem(
                title=entry.title,
                description=content[:2000] if content else "",  # Limitar tamanho da descrição
                content=full_content[:10000] if full_content else "",  # Limitar tamanho do conteúdo
                link=entry.link,
                guid=guid,
                published_date=published_date,
                is_processed=False,
                rss_feed_id=feed.id,
                user_id=feed.user_id
            )
            
            db.session.add(news_item)
            new_items_count += 1
        
        # Salvar no banco de dados
        db.session.commit()
        
        logger.info(f"Feed {feed.name} processado. {new_items_count} novos itens de {total_items} total.")
        return new_items_count, total_items
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar feed {feed.name}: {str(e)}")
        raise e

def fetch_all_feeds():
    """
    Busca e processa todos os feeds RSS ativos
    
    Returns:
        dict: Estatísticas de processamento
    """
    stats = {
        'total_feeds': 0,
        'processed_feeds': 0,
        'feeds_with_errors': 0,
        'new_items': 0,
        'total_items': 0
    }
    
    # Buscar todos os feeds ativos
    feeds = RSSFeed.query.filter_by(is_active=True).all()
    stats['total_feeds'] = len(feeds)
    
    if not feeds:
        logger.info("Nenhum feed ativo encontrado.")
        return stats
    
    # Processar cada feed
    for feed in feeds:
        try:
            new_items, total_items = fetch_and_process_feed(feed)
            stats['new_items'] += new_items
            stats['total_items'] += total_items
            stats['processed_feeds'] += 1
            
            # Atualizar a data da última busca
            feed.last_fetch = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            stats['feeds_with_errors'] += 1
            logger.error(f"Erro ao processar feed {feed.name}: {str(e)}")
    
    logger.info(f"Processamento de feeds concluído. Estatísticas: {stats}")
    return stats