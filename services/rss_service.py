import logging
import feedparser
import trafilatura
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RSSService:
    """Serviço para capturar e processar feeds RSS"""
    
    @staticmethod
    def fetch_feed_items(feed_url: str) -> List[Dict[str, Any]]:
        """
        Busca e processa um feed RSS a partir de uma URL
        
        Args:
            feed_url: URL do feed RSS
            
        Returns:
            Lista de itens do feed como dicionários
        """
        try:
            # Parse do feed RSS
            parsed_feed = feedparser.parse(feed_url)
            
            if hasattr(parsed_feed, 'bozo_exception'):
                logger.error(f"Erro ao analisar feed: {parsed_feed.bozo_exception}")
                return []
            
            items = []
            
            for entry in parsed_feed.entries:
                # Extrair data de publicação
                published_date = None
                if hasattr(entry, 'published_parsed'):
                    # Converter struct_time para datetime
                    published_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    published_date = datetime(*entry.updated_parsed[:6])
                
                # Extrair conteúdo
                content = ""
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                else:
                    # Tentar extrair conteúdo da página
                    try:
                        content = RSSService._extract_content_from_url(entry.link)
                    except Exception as e:
                        logger.warning(f"Não foi possível extrair conteúdo da URL {entry.link}: {str(e)}")
                
                # Criar representação do item
                item = {
                    'title': entry.title,
                    'link': entry.link,
                    'guid': entry.id if hasattr(entry, 'id') else entry.link,
                    'published_date': published_date,
                    'content': content
                }
                
                items.append(item)
            
            return items
        except Exception as e:
            logger.error(f"Erro ao processar feed RSS: {str(e)}")
            return []
    
    @staticmethod
    def _extract_content_from_url(url: str) -> Optional[str]:
        """
        Extrai o conteúdo principal de uma URL
        
        Args:
            url: URL da página
            
        Returns:
            Conteúdo extraído ou None se falhar
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded)
                return content
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair conteúdo de {url}: {str(e)}")
            return None