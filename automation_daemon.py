#!/usr/bin/env python3
"""
BlogAuto AI - Sistema de Automação Completo
Sistema daemon que executa automação contínua sem necessidade de interface web
"""

import os
import sys
import time
import logging
import signal
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading
import schedule

# Configurar ambiente
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Configurar logging avançado
log_dir = project_dir / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'automation_daemon.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BlogAutoAIDaemon:
    """Daemon principal para automação completa do BlogAuto AI"""
    
    def __init__(self):
        self.running = False
        self.threads = []
        
    def start(self):
        """Inicia o daemon de automação"""
        logger.info("🚀 Iniciando BlogAuto AI Automation Daemon")
        self.running = True
        
        # Configurar handlers para parada graceful
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            # Configurar tarefas agendadas
            self._setup_scheduled_tasks()
            
            # Iniciar thread principal de monitoramento
            main_thread = threading.Thread(target=self._main_loop, daemon=True)
            main_thread.start()
            self.threads.append(main_thread)
            
            # Aguardar execução
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interrupção manual detectada")
        finally:
            self.stop()
            
    def stop(self):
        """Para o daemon gracefully"""
        logger.info("🛑 Parando BlogAuto AI Automation Daemon")
        self.running = False
        
        # Aguardar threads terminarem
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
                
    def _signal_handler(self, signum, frame):
        """Handler para sinais do sistema"""
        logger.info(f"Sinal {signum} recebido, parando daemon...")
        self.running = False
        
    def _setup_scheduled_tasks(self):
        """Configura tarefas agendadas"""
        # Processar artigos agendados - a cada 5 minutos
        schedule.every(5).minutes.do(self._process_scheduled_articles)
        
        # Buscar feeds RSS - a cada 30 minutos
        schedule.every(30).minutes.do(self._fetch_rss_feeds)
        
        # Gerar novos artigos - a cada 2 horas
        schedule.every(2).hours.do(self._generate_new_articles)
        
        # Limpeza de dados - diariamente às 2h
        schedule.every().day.at("02:00").do(self._cleanup_data)
        
        logger.info("📋 Tarefas agendadas configuradas")
        
    def _main_loop(self):
        """Loop principal do daemon"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                time.sleep(60)
                
    def _process_scheduled_articles(self):
        """Processa artigos agendados para publicação"""
        try:
            logger.info("📅 Processando artigos agendados...")
            
            from app import app, db
            from models import Article, ArticleStatus
            
            with app.app_context():
                current_time = datetime.utcnow()
                
                # Buscar artigos agendados
                articles = Article.query.filter(
                    Article.status == ArticleStatus.SCHEDULED,
                    Article.scheduled_date <= current_time
                ).limit(10).all()
                
                logger.info(f"Encontrados {len(articles)} artigos para publicação")
                
                for article in articles:
                    try:
                        success = self._publish_to_wordpress(article)
                        
                        if success:
                            article.status = ArticleStatus.PUBLISHED
                            logger.info(f"✅ Artigo '{article.title}' publicado")
                        else:
                            article.status = ArticleStatus.FAILED
                            article.publish_attempt_count += 1
                            logger.error(f"❌ Falha ao publicar '{article.title}'")
                            
                        article.last_attempt_date = datetime.utcnow()
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar artigo {article.id}: {e}")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Erro no processamento de artigos agendados: {e}")
            
    def _fetch_rss_feeds(self):
        """Busca novos itens de feeds RSS"""
        try:
            logger.info("📡 Buscando feeds RSS...")
            
            from app import app, db
            from models import RSSFeed, NewsItem, AutomationTheme
            import feedparser
            
            with app.app_context():
                # Buscar feeds ativos
                feeds = db.session.query(RSSFeed).join(AutomationTheme).filter(
                    RSSFeed.is_active == True,
                    AutomationTheme.is_active == True
                ).all()
                
                logger.info(f"Processando {len(feeds)} feeds RSS")
                
                for feed in feeds:
                    try:
                        # Parse do feed
                        parsed_feed = feedparser.parse(feed.url)
                        new_items_count = 0
                        
                        for entry in parsed_feed.entries:
                            try:
                                # Verificar se já existe
                                guid = entry.get('id', entry.get('link', ''))
                                existing = NewsItem.query.filter_by(guid=guid).first()
                                
                                if not existing:
                                    # Processar data
                                    published_date = None
                                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                        try:
                                            published_date = datetime(*entry.published_parsed[:6])
                                        except:
                                            pass
                                    
                                    # Verificar se é recente
                                    if not feed.last_fetch or not published_date or published_date > feed.last_fetch:
                                        # Extrair conteúdo
                                        content = ""
                                        if hasattr(entry, 'content') and entry.content:
                                            content = entry.content[0].value
                                        elif hasattr(entry, 'summary'):
                                            content = entry.summary
                                        
                                        # Criar item de notícia
                                        news_item = NewsItem(
                                            title=entry.get('title', 'Sem título')[:255],
                                            description=entry.get('summary', '')[:500],
                                            content=content,
                                            link=entry.get('link', '')[:500],
                                            guid=guid[:500],
                                            published_date=published_date,
                                            rss_feed_id=feed.id,
                                            user_id=feed.user_id,
                                            is_processed=False
                                        )
                                        
                                        db.session.add(news_item)
                                        new_items_count += 1
                                        
                            except Exception as e:
                                logger.error(f"Erro ao processar entrada do feed: {e}")
                                continue
                        
                        # Atualizar última busca
                        feed.last_fetch = datetime.utcnow()
                        
                        if new_items_count > 0:
                            logger.info(f"📰 Feed '{feed.name}': {new_items_count} novos itens")
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar feed '{feed.name}': {e}")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Erro na busca de feeds RSS: {e}")
            
    def _generate_new_articles(self):
        """Gera novos artigos automaticamente"""
        try:
            logger.info("📝 Gerando novos artigos...")
            
            from app import app, db
            from models import (AutomationSettings, NewsItem, AutomationTheme, 
                              Article, ArticleStatus, AIModel, APIKey, APIType)
            from services.ai_service import generate_article_from_news, generate_article_from_theme
            
            with app.app_context():
                # Buscar usuários com automação ativa
                active_settings = AutomationSettings.query.filter_by(is_active=True).all()
                
                for settings in active_settings:
                    try:
                        # Verificar horário ativo
                        current_hour = datetime.now().hour
                        if not (settings.active_hours_start <= current_hour <= settings.active_hours_end):
                            continue
                            
                        # Verificar se deve executar
                        if settings.next_scheduled_run and settings.next_scheduled_run > datetime.utcnow():
                            continue
                        
                        # Buscar notícias não processadas
                        unprocessed_news = NewsItem.query.filter_by(
                            user_id=settings.user_id,
                            is_processed=False
                        ).limit(3).all()
                        
                        # Determinar modelo de IA
                        api_key = APIKey.query.filter_by(
                            user_id=settings.user_id,
                            type=APIType.CLAUDE
                        ).first()
                        
                        if not api_key:
                            api_key = APIKey.query.filter_by(
                                user_id=settings.user_id,
                                type=APIType.GPT
                            ).first()
                            
                        if not api_key:
                            logger.warning(f"Usuário {settings.user_id} sem chaves de API")
                            continue
                            
                        ai_model = AIModel.CLAUDE if api_key.type == APIType.CLAUDE else AIModel.GPT
                        
                        # Gerar artigos a partir de notícias
                        for news_item in unprocessed_news:
                            try:
                                article = generate_article_from_news(
                                    news_item,
                                    ai_model,
                                    settings.user_id,
                                    settings.wordpress_config_id
                                )
                                
                                if article:
                                    # Agendar para publicação
                                    article.scheduled_date = datetime.utcnow() + timedelta(
                                        minutes=self._random_delay()
                                    )
                                    article.status = ArticleStatus.SCHEDULED
                                    
                                    news_item.is_processed = True
                                    
                                    logger.info(f"📰 Artigo gerado a partir de: {news_item.title[:50]}...")
                                    
                            except Exception as e:
                                logger.error(f"Erro ao gerar artigo da notícia {news_item.id}: {e}")
                        
                        # Se poucas notícias, gerar por temas
                        if len(unprocessed_news) < 2:
                            themes = AutomationTheme.query.filter_by(
                                user_id=settings.user_id,
                                is_active=True
                            ).order_by(AutomationTheme.priority.desc()).limit(2).all()
                            
                            for theme in themes:
                                try:
                                    article = generate_article_from_theme(
                                        theme,
                                        ai_model,
                                        settings.user_id,
                                        settings.wordpress_config_id
                                    )
                                    
                                    if article:
                                        article.scheduled_date = datetime.utcnow() + timedelta(
                                            minutes=self._random_delay()
                                        )
                                        article.status = ArticleStatus.SCHEDULED
                                        
                                        logger.info(f"🎯 Artigo gerado para tema: {theme.name}")
                                        
                                except Exception as e:
                                    logger.error(f"Erro ao gerar artigo do tema {theme.name}: {e}")
                        
                        # Atualizar próxima execução
                        settings.next_scheduled_run = datetime.utcnow() + timedelta(
                            hours=settings.post_interval_hours
                        )
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar automação do usuário {settings.user_id}: {e}")
                        
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Erro na geração de artigos: {e}")
            
    def _publish_to_wordpress(self, article) -> bool:
        """Publica artigo no WordPress"""
        try:
            from services.wordpress_service import WordPressService
            
            if not article.wordpress_config:
                logger.error(f"Artigo {article.id} sem configuração WordPress")
                return False
                
            wp_service = WordPressService(article.wordpress_config)
            return wp_service.publish_article(article.id)
            
        except Exception as e:
            logger.error(f"Erro ao publicar no WordPress: {e}")
            return False
            
    def _cleanup_data(self):
        """Limpa dados antigos"""
        try:
            logger.info("🗑️ Executando limpeza de dados...")
            
            from app import app, db
            from models import Article, ArticleStatus, NewsItem
            
            with app.app_context():
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                # Remover artigos falhados antigos
                failed_count = Article.query.filter(
                    Article.status == ArticleStatus.FAILED,
                    Article.created_at < cutoff_date
                ).count()
                
                if failed_count > 0:
                    Article.query.filter(
                        Article.status == ArticleStatus.FAILED,
                        Article.created_at < cutoff_date
                    ).delete()
                    logger.info(f"Removidos {failed_count} artigos falhados")
                
                # Remover notícias processadas antigas
                old_cutoff = datetime.utcnow() - timedelta(days=60)
                news_count = NewsItem.query.filter(
                    NewsItem.is_processed == True,
                    NewsItem.created_at < old_cutoff
                ).count()
                
                if news_count > 0:
                    NewsItem.query.filter(
                        NewsItem.is_processed == True,
                        NewsItem.created_at < old_cutoff
                    ).delete()
                    logger.info(f"Removidas {news_count} notícias antigas")
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")
            
    def _random_delay(self) -> int:
        """Retorna um delay aleatório para evitar spam"""
        import random
        return random.randint(10, 60)  # 10 a 60 minutos


def main():
    """Função principal"""
    try:
        daemon = BlogAutoAIDaemon()
        daemon.start()
    except Exception as e:
        logger.error(f"Erro crítico no daemon: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()