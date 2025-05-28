"""
Motor de Automação Principal do BlogAuto AI
Sistema completo para geração e publicação automática de conteúdo
"""

import os
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import feedparser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config

logger = logging.getLogger(__name__)

class AutomationEngine:
    """Motor principal de automação para geração de conteúdo"""
    
    def __init__(self, database_url: str = None):
        """Inicializa o motor de automação"""
        self.database_url = database_url or Config.SQLALCHEMY_DATABASE_URI
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def run_automation_cycle(self):
        """Executa um ciclo completo de automação"""
        logger.info("🚀 Iniciando ciclo de automação")
        
        try:
            with self.SessionLocal() as session:
                # 1. Processar artigos agendados
                self._process_scheduled_articles(session)
                
                # 2. Buscar novos conteúdos de feeds RSS
                self._fetch_rss_feeds(session)
                
                # 3. Gerar novos artigos baseados em temas
                self._generate_theme_articles(session)
                
                # 4. Publicar artigos prontos
                self._publish_ready_articles(session)
                
                # 5. Limpeza de dados antigos
                self._cleanup_old_data(session)
                
                session.commit()
                logger.info("✅ Ciclo de automação concluído com sucesso")
                
        except Exception as e:
            logger.error(f"❌ Erro no ciclo de automação: {e}")
            
    def _process_scheduled_articles(self, session):
        """Processa artigos agendados para publicação"""
        try:
            current_time = datetime.utcnow()
            
            # Buscar artigos agendados
            result = session.execute(text("""
                SELECT id, title, scheduled_date, wordpress_config_id, user_id 
                FROM article 
                WHERE status = 'scheduled' 
                AND scheduled_date <= :current_time
                LIMIT 10
            """), {"current_time": current_time})
            
            scheduled_articles = result.fetchall()
            logger.info(f"📅 Encontrados {len(scheduled_articles)} artigos agendados")
            
            for article in scheduled_articles:
                try:
                    success = self._publish_article_to_wordpress(session, article.id)
                    if success:
                        # Atualizar status para publicado
                        session.execute(text("""
                            UPDATE article 
                            SET status = 'published', 
                                updated_at = :now 
                            WHERE id = :article_id
                        """), {"now": datetime.utcnow(), "article_id": article.id})
                        
                        logger.info(f"✅ Artigo {article.id} publicado com sucesso")
                    else:
                        # Marcar como falhado
                        session.execute(text("""
                            UPDATE article 
                            SET status = 'failed', 
                                publish_attempt_count = publish_attempt_count + 1,
                                last_attempt_date = :now 
                            WHERE id = :article_id
                        """), {"now": datetime.utcnow(), "article_id": article.id})
                        
                        logger.error(f"❌ Falha ao publicar artigo {article.id}")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar artigo agendado {article.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro no processamento de artigos agendados: {e}")
            
    def _fetch_rss_feeds(self, session):
        """Busca novos itens de feeds RSS"""
        try:
            # Buscar feeds RSS ativos
            result = session.execute(text("""
                SELECT rf.id, rf.url, rf.name, rf.user_id, rf.theme_id, rf.last_fetch
                FROM rss_feed rf
                JOIN automation_theme at ON rf.theme_id = at.id
                WHERE rf.is_active = 1 
                AND at.is_active = 1
                AND (rf.last_fetch IS NULL OR rf.last_fetch < :cutoff_time)
                LIMIT 20
            """), {"cutoff_time": datetime.utcnow() - timedelta(hours=2)})
            
            feeds = result.fetchall()
            logger.info(f"📡 Processando {len(feeds)} feeds RSS")
            
            for feed in feeds:
                try:
                    new_items = self._parse_rss_feed(feed.url, feed.last_fetch)
                    
                    for item in new_items:
                        # Verificar se já existe
                        existing = session.execute(text("""
                            SELECT id FROM news_item WHERE guid = :guid
                        """), {"guid": item['guid']}).fetchone()
                        
                        if not existing:
                            # Inserir nova notícia
                            session.execute(text("""
                                INSERT INTO news_item 
                                (title, description, content, link, guid, published_date, 
                                 rss_feed_id, user_id, created_at, is_processed)
                                VALUES (:title, :description, :content, :link, :guid, 
                                        :published_date, :rss_feed_id, :user_id, :created_at, 0)
                            """), {
                                "title": item['title'][:255],
                                "description": item['description'][:500] if item['description'] else None,
                                "content": item['content'],
                                "link": item['link'][:500],
                                "guid": item['guid'][:500],
                                "published_date": item['published_date'],
                                "rss_feed_id": feed.id,
                                "user_id": feed.user_id,
                                "created_at": datetime.utcnow()
                            })
                    
                    # Atualizar última busca
                    session.execute(text("""
                        UPDATE rss_feed 
                        SET last_fetch = :now 
                        WHERE id = :feed_id
                    """), {"now": datetime.utcnow(), "feed_id": feed.id})
                    
                    logger.info(f"📰 Feed '{feed.name}': {len(new_items)} novos itens")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar feed {feed.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro na busca de feeds RSS: {e}")
            
    def _parse_rss_feed(self, url: str, last_fetch: datetime = None) -> List[Dict]:
        """Faz parsing de um feed RSS e retorna novos itens"""
        try:
            feed = feedparser.parse(url)
            new_items = []
            
            for entry in feed.entries:
                # Processar data de publicação
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_date = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                # Verificar se é novo
                if not last_fetch or not published_date or published_date > last_fetch:
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value if entry.content else ""
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    
                    new_items.append({
                        'title': entry.get('title', 'Sem título'),
                        'description': entry.get('summary', ''),
                        'content': content,
                        'link': entry.get('link', ''),
                        'guid': entry.get('id', entry.get('link', '')),
                        'published_date': published_date
                    })
            
            return new_items
            
        except Exception as e:
            logger.error(f"Erro ao fazer parsing do feed {url}: {e}")
            return []
            
    def _generate_theme_articles(self, session):
        """Gera novos artigos baseados em temas"""
        try:
            # Buscar usuários com automação ativa
            result = session.execute(text("""
                SELECT DISTINCT u.id as user_id, 
                       ats.post_interval_hours,
                       ats.min_word_count,
                       ats.max_word_count,
                       ats.active_hours_start,
                       ats.active_hours_end,
                       ats.wordpress_config_id
                FROM user u
                JOIN automation_settings ats ON u.id = ats.user_id
                WHERE ats.is_active = 1
                AND (ats.next_scheduled_run IS NULL OR ats.next_scheduled_run <= :now)
            """), {"now": datetime.utcnow()})
            
            active_users = result.fetchall()
            
            for user in active_users:
                try:
                    # Verificar se está no horário ativo
                    current_hour = datetime.now().hour
                    if not (user.active_hours_start <= current_hour <= user.active_hours_end):
                        continue
                    
                    # Buscar notícias não processadas
                    unprocessed_news = session.execute(text("""
                        SELECT id, title, content, link
                        FROM news_item 
                        WHERE user_id = :user_id 
                        AND is_processed = 0
                        ORDER BY published_date DESC
                        LIMIT 3
                    """), {"user_id": user.user_id}).fetchall()
                    
                    # Gerar artigos a partir de notícias
                    for news in unprocessed_news:
                        try:
                            article_content = self._generate_article_from_news(
                                news, user.user_id, user.min_word_count, user.max_word_count
                            )
                            
                            if article_content:
                                # Inserir novo artigo
                                session.execute(text("""
                                    INSERT INTO article 
                                    (title, content, status, user_id, wordpress_config_id, 
                                     created_at, is_automated, news_item_id, ai_model)
                                    VALUES (:title, :content, 'draft', :user_id, :wp_config_id, 
                                            :created_at, 1, :news_id, 'gpt')
                                """), {
                                    "title": article_content['title'],
                                    "content": article_content['content'],
                                    "user_id": user.user_id,
                                    "wp_config_id": user.wordpress_config_id,
                                    "created_at": datetime.utcnow(),
                                    "news_id": news.id
                                })
                                
                                # Marcar notícia como processada
                                session.execute(text("""
                                    UPDATE news_item 
                                    SET is_processed = 1 
                                    WHERE id = :news_id
                                """), {"news_id": news.id})
                                
                                logger.info(f"📝 Artigo gerado para usuário {user.user_id}")
                                
                        except Exception as e:
                            logger.error(f"Erro ao gerar artigo da notícia {news.id}: {e}")
                    
                    # Atualizar próxima execução
                    next_run = datetime.utcnow() + timedelta(hours=user.post_interval_hours)
                    session.execute(text("""
                        UPDATE automation_settings 
                        SET next_scheduled_run = :next_run 
                        WHERE user_id = :user_id
                    """), {"next_run": next_run, "user_id": user.user_id})
                    
                except Exception as e:
                    logger.error(f"Erro ao processar usuário {user.user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro na geração de artigos temáticos: {e}")
            
    def _generate_article_from_news(self, news, user_id: int, min_words: int, max_words: int) -> Optional[Dict]:
        """Gera artigo usando IA a partir de uma notícia"""
        try:
            # Buscar chave de API do usuário
            from services.ai_service import generate_content_gpt, get_api_key
            from models import APIType
            
            api_key = get_api_key(user_id, APIType.GPT)
            if not api_key:
                return None
            
            # Criar prompt para geração
            prompt = f"""
            Baseado na seguinte notícia, crie um artigo original e informativo:
            
            Título: {news.title}
            Conteúdo: {news.content[:1000]}
            Link original: {news.link}
            
            Requisitos:
            - Criar um título atrativo e único
            - Escrever um artigo de {min_words} a {max_words} palavras
            - Incluir introdução, desenvolvimento e conclusão
            - Usar linguagem clara e profissional
            - Não copiar texto diretamente da fonte
            - Formato HTML simples (p, h2, h3, ul, li)
            
            Retorne apenas um JSON com:
            {{"title": "título do artigo", "content": "conteúdo completo em HTML"}}
            """
            
            response = generate_content_gpt(prompt, user_id, max_tokens=2000)
            
            # Tentar extrair JSON da resposta
            import json
            try:
                # Encontrar JSON na resposta
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    article_data = json.loads(json_str)
                    return article_data
            except:
                pass
            
            # Fallback: criar estrutura básica
            return {
                "title": f"Análise: {news.title}",
                "content": f"<p>{response}</p>"
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar artigo: {e}")
            return None
            
    def _publish_article_to_wordpress(self, session, article_id: int) -> bool:
        """Publica um artigo no WordPress"""
        try:
            # Buscar dados do artigo
            result = session.execute(text("""
                SELECT a.title, a.content, a.user_id, a.wordpress_config_id,
                       wc.site_url, wc.username, wc.app_password
                FROM article a
                JOIN word_press_config wc ON a.wordpress_config_id = wc.id
                WHERE a.id = :article_id
            """), {"article_id": article_id}).fetchone()
            
            if not result:
                return False
            
            # Simular publicação (implementar WordPress API real)
            import requests
            import base64
            
            # Preparar autenticação
            auth_string = f"{result.username}:{result.app_password}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            # Dados do post
            post_data = {
                "title": result.title,
                "content": result.content,
                "status": "publish"
            }
            
            headers = {
                "Authorization": f"Basic {auth_bytes}",
                "Content-Type": "application/json"
            }
            
            # Fazer requisição para WordPress API
            wp_url = f"{result.site_url.rstrip('/')}/wp-json/wp/v2/posts"
            response = requests.post(wp_url, json=post_data, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                # Salvar ID do post no WordPress
                wp_post_data = response.json()
                session.execute(text("""
                    UPDATE article 
                    SET wordpress_post_id = :wp_id 
                    WHERE id = :article_id
                """), {"wp_id": wp_post_data.get('id'), "article_id": article_id})
                
                return True
            else:
                logger.error(f"Erro na API WordPress: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao publicar no WordPress: {e}")
            return False
            
    def _publish_ready_articles(self, session):
        """Publica artigos que estão prontos para publicação"""
        try:
            # Buscar artigos em rascunho que podem ser agendados
            result = session.execute(text("""
                SELECT a.id, a.user_id, ats.active_hours_start, ats.active_hours_end
                FROM article a
                JOIN automation_settings ats ON a.user_id = ats.user_id
                WHERE a.status = 'draft' 
                AND a.is_automated = 1
                AND a.created_at < :cutoff_time
                LIMIT 5
            """), {"cutoff_time": datetime.utcnow() - timedelta(minutes=30)})
            
            ready_articles = result.fetchall()
            
            for article in ready_articles:
                current_hour = datetime.now().hour
                
                # Verificar se está no horário ativo
                if article.active_hours_start <= current_hour <= article.active_hours_end:
                    # Agendar para publicação em alguns minutos
                    scheduled_time = datetime.utcnow() + timedelta(minutes=random.randint(5, 15))
                    
                    session.execute(text("""
                        UPDATE article 
                        SET status = 'scheduled', 
                            scheduled_date = :scheduled_time 
                        WHERE id = :article_id
                    """), {"scheduled_time": scheduled_time, "article_id": article.id})
                    
                    logger.info(f"📅 Artigo {article.id} agendado para {scheduled_time}")
                    
        except Exception as e:
            logger.error(f"Erro ao agendar artigos: {e}")
            
    def _cleanup_old_data(self, session):
        """Remove dados antigos para manter performance"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Remover artigos falhados antigos
            result = session.execute(text("""
                DELETE FROM article 
                WHERE status = 'failed' 
                AND created_at < :cutoff_date
            """), {"cutoff_date": cutoff_date})
            
            if result.rowcount > 0:
                logger.info(f"🗑️ Removidos {result.rowcount} artigos falhados antigos")
            
            # Remover notícias processadas antigas
            old_cutoff = datetime.utcnow() - timedelta(days=60)
            result = session.execute(text("""
                DELETE FROM news_item 
                WHERE is_processed = 1 
                AND created_at < :old_cutoff
            """), {"old_cutoff": old_cutoff})
            
            if result.rowcount > 0:
                logger.info(f"🗑️ Removidas {result.rowcount} notícias antigas")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")


def main():
    """Função principal para execução standalone"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    engine = AutomationEngine()
    engine.run_automation_cycle()


if __name__ == "__main__":
    main()