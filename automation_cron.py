#!/usr/bin/env python3
"""
Sistema de automação com CRON para BlogAuto AI
Este script executa tarefas automatizadas de geração e publicação de conteúdo
Pode ser executado via crontab para funcionar sem intervenção manual
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Configurar logging
log_dir = project_dir / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Configura o ambiente para execução standalone"""
    try:
        # Importar configurações Flask
        from app import app, db
        from models import (User, AutomationSettings, AutomationTheme, 
                           RSSFeed, NewsItem, Article, ArticleStatus)
        from services.ai_service import generate_article_from_theme, generate_article_from_news
        from services.wordpress_service import WordPressService
        from services.rss_service import fetch_website_content
        
        return {
            'app': app,
            'db': db,
            'models': {
                'User': User,
                'AutomationSettings': AutomationSettings,
                'AutomationTheme': AutomationTheme,
                'RSSFeed': RSSFeed,
                'NewsItem': NewsItem,
                'Article': Article,
                'ArticleStatus': ArticleStatus
            },
            'services': {
                'ai_service': {
                    'generate_article_from_theme': generate_article_from_theme,
                    'generate_article_from_news': generate_article_from_news
                },
                'WordPressService': WordPressService,
                'fetch_website_content': fetch_website_content
            }
        }
    except ImportError as e:
        logger.error(f"Erro ao importar dependências: {e}")
        return None

def process_scheduled_articles(env):
    """Processa artigos agendados para publicação"""
    logger.info("Iniciando processamento de artigos agendados...")
    
    with env['app'].app_context():
        try:
            # Buscar artigos agendados que devem ser publicados
            current_time = datetime.utcnow()
            scheduled_articles = env['db'].session.query(env['models']['Article']).filter(
                env['models']['Article'].status == env['models']['ArticleStatus'].SCHEDULED,
                env['models']['Article'].scheduled_date <= current_time
            ).all()
            
            logger.info(f"Encontrados {len(scheduled_articles)} artigos para publicação")
            
            for article in scheduled_articles:
                try:
                    # Obter configuração do WordPress
                    if not article.wordpress_config:
                        logger.warning(f"Artigo {article.id} sem configuração WordPress")
                        continue
                    
                    # Publicar no WordPress
                    wp_service = env['services']['WordPressService'](article.wordpress_config)
                    success = wp_service.publish_article(article.id)
                    
                    if success:
                        logger.info(f"Artigo {article.id} publicado com sucesso")
                    else:
                        logger.error(f"Falha ao publicar artigo {article.id}")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar artigo {article.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro no processamento de artigos agendados: {e}")

def process_automation_tasks(env):
    """Processa tarefas de automação baseadas em configurações dos usuários"""
    logger.info("Iniciando processamento de tarefas de automação...")
    
    with env['app'].app_context():
        try:
            # Buscar usuários com automação ativa
            active_settings = env['db'].session.query(env['models']['AutomationSettings']).filter(
                env['models']['AutomationSettings'].is_active == True
            ).all()
            
            logger.info(f"Encontradas {len(active_settings)} configurações de automação ativas")
            
            for settings in active_settings:
                try:
                    # Verificar se é hora de executar
                    if settings.next_scheduled_run and settings.next_scheduled_run <= datetime.utcnow():
                        logger.info(f"Executando automação para usuário {settings.user_id}")
                        
                        # Processar feeds RSS
                        process_rss_feeds(env, settings.user_id)
                        
                        # Gerar artigos baseados em temas
                        generate_theme_articles(env, settings.user_id, settings)
                        
                        # Atualizar próxima execução
                        settings.next_scheduled_run = datetime.utcnow() + timedelta(hours=settings.post_interval_hours)
                        env['db'].session.commit()
                        
                except Exception as e:
                    logger.error(f"Erro ao processar automação do usuário {settings.user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro no processamento de automação: {e}")

def process_rss_feeds(env, user_id):
    """Processa feeds RSS para um usuário específico"""
    try:
        # Buscar feeds RSS ativos do usuário
        rss_feeds = env['db'].session.query(env['models']['RSSFeed']).filter(
            env['models']['RSSFeed'].user_id == user_id,
            env['models']['RSSFeed'].is_active == True
        ).all()
        
        import feedparser
        
        for feed in rss_feeds:
            try:
                # Buscar novas notícias usando feedparser
                parsed_feed = feedparser.parse(feed.url)
                new_items = []
                
                for entry in parsed_feed.entries:
                    # Verificar se é um item novo (após last_fetch)
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = datetime(*entry.published_parsed[:6])
                    
                    if not feed.last_fetch or not published_date or published_date > feed.last_fetch:
                        new_items.append({
                            'title': entry.get('title', ''),
                            'description': entry.get('description', ''),
                            'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                            'link': entry.get('link', ''),
                            'guid': entry.get('id', entry.get('link', '')),
                            'published_date': published_date
                        })
                
                for item in new_items:
                    # Criar item de notícia no banco
                    news_item = env['models']['NewsItem'](
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        content=item.get('content', ''),
                        link=item.get('link', ''),
                        guid=item.get('guid', item.get('link', '')),
                        published_date=item.get('published_date'),
                        rss_feed_id=feed.id,
                        user_id=user_id
                    )
                    env['db'].session.add(news_item)
                    
                # Atualizar última busca
                feed.last_fetch = datetime.utcnow()
                env['db'].session.commit()
                
                logger.info(f"Feed {feed.name} processado: {len(new_items)} novos itens")
                
            except Exception as e:
                logger.error(f"Erro ao processar feed {feed.name}: {e}")
                
    except Exception as e:
        logger.error(f"Erro no processamento de feeds RSS: {e}")

def generate_theme_articles(env, user_id, settings):
    """Gera artigos baseados em temas configurados"""
    try:
        # Buscar temas ativos do usuário
        themes = env['db'].session.query(env['models']['AutomationTheme']).filter(
            env['models']['AutomationTheme'].user_id == user_id,
            env['models']['AutomationTheme'].is_active == True
        ).order_by(env['models']['AutomationTheme'].priority.desc()).all()
        
        if not themes:
            logger.info(f"Nenhum tema ativo encontrado para usuário {user_id}")
            return
            
        # Verificar se há artigos não processados para gerar
        unprocessed_news = env['db'].session.query(env['models']['NewsItem']).filter(
            env['models']['NewsItem'].user_id == user_id,
            env['models']['NewsItem'].is_processed == False
        ).limit(5).all()  # Processar até 5 notícias por execução
        
        ai_model = settings.user.api_keys.filter_by(type='claude').first() or settings.user.api_keys.filter_by(type='gpt').first()
        if not ai_model:
            logger.warning(f"Usuário {user_id} não tem chaves de API configuradas")
            return
            
        # Gerar artigos a partir de notícias
        for news_item in unprocessed_news:
            try:
                article = env['services']['ai_service']['generate_article_from_news'](
                    news_item, 
                    'claude' if ai_model.type == 'claude' else 'gpt',
                    user_id,
                    settings.wordpress_config_id
                )
                
                if article:
                    # Marcar como agendado se dentro do horário ativo
                    current_hour = datetime.now().hour
                    if settings.active_hours_start <= current_hour <= settings.active_hours_end:
                        # Agendar para publicação imediata
                        article.scheduled_date = datetime.utcnow() + timedelta(minutes=5)
                        article.status = env['models']['ArticleStatus'].SCHEDULED
                    
                    news_item.is_processed = True
                    env['db'].session.commit()
                    
                    logger.info(f"Artigo gerado a partir da notícia: {news_item.title}")
                    
            except Exception as e:
                logger.error(f"Erro ao gerar artigo da notícia {news_item.id}: {e}")
        
        # Gerar artigos baseados em temas (se não há notícias suficientes)
        if len(unprocessed_news) < 2:
            for theme in themes[:2]:  # Máximo 2 temas por execução
                try:
                    article = env['services']['ai_service']['generate_article_from_theme'](
                        theme,
                        'claude' if ai_model.type == 'claude' else 'gpt',
                        user_id,
                        settings.wordpress_config_id
                    )
                    
                    if article:
                        # Agendar para publicação
                        current_hour = datetime.now().hour
                        if settings.active_hours_start <= current_hour <= settings.active_hours_end:
                            article.scheduled_date = datetime.utcnow() + timedelta(minutes=10)
                            article.status = env['models']['ArticleStatus'].SCHEDULED
                        
                        env['db'].session.commit()
                        logger.info(f"Artigo gerado para tema: {theme.name}")
                        
                except Exception as e:
                    logger.error(f"Erro ao gerar artigo para tema {theme.name}: {e}")
                    
    except Exception as e:
        logger.error(f"Erro na geração de artigos temáticos: {e}")

def cleanup_old_data(env):
    """Limpa dados antigos para manter performance"""
    logger.info("Iniciando limpeza de dados antigos...")
    
    with env['app'].app_context():
        try:
            # Limpar logs antigos (mais de 30 dias)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Limpar artigos falhados antigos (mais de 7 dias)
            old_failed_articles = env['db'].session.query(env['models']['Article']).filter(
                env['models']['Article'].status == env['models']['ArticleStatus'].FAILED,
                env['models']['Article'].created_at < datetime.utcnow() - timedelta(days=7)
            ).count()
            
            if old_failed_articles > 0:
                env['db'].session.query(env['models']['Article']).filter(
                    env['models']['Article'].status == env['models']['ArticleStatus'].FAILED,
                    env['models']['Article'].created_at < datetime.utcnow() - timedelta(days=7)
                ).delete()
                env['db'].session.commit()
                logger.info(f"Removidos {old_failed_articles} artigos falhados antigos")
                
            # Limpar notícias processadas antigas (mais de 60 dias)
            old_cutoff = datetime.utcnow() - timedelta(days=60)
            old_news = env['db'].session.query(env['models']['NewsItem']).filter(
                env['models']['NewsItem'].is_processed == True,
                env['models']['NewsItem'].created_at < old_cutoff
            ).count()
            
            if old_news > 0:
                env['db'].session.query(env['models']['NewsItem']).filter(
                    env['models']['NewsItem'].is_processed == True,
                    env['models']['NewsItem'].created_at < old_cutoff
                ).delete()
                env['db'].session.commit()
                logger.info(f"Removidas {old_news} notícias antigas processadas")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")

def main():
    """Função principal do sistema de automação"""
    logger.info("=== Iniciando BlogAuto AI Automation System ===")
    
    # Configurar ambiente
    env = setup_environment()
    if not env:
        logger.error("Falha ao configurar ambiente. Encerrando.")
        sys.exit(1)
    
    try:
        # Executar tarefas de automação
        process_scheduled_articles(env)
        process_automation_tasks(env)
        
        # Limpeza de dados (executar apenas uma vez por dia)
        current_hour = datetime.now().hour
        if current_hour == 2:  # 2h da madrugada
            cleanup_old_data(env)
            
        logger.info("=== Automação concluída com sucesso ===")
        
    except Exception as e:
        logger.error(f"Erro crítico na automação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()