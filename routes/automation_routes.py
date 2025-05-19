import csv
import io
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import (
    AutomationTheme, RSSFeed, NewsItem, AutomationSettings,
    Article, ArticleStatus, AIModel, RepeatSchedule, LogType, 
    ArticleLog, WordPressConfig, APIKey, APIType
)

logger = logging.getLogger(__name__)

automation_bp = Blueprint('automation', __name__, url_prefix='/automation')

@automation_bp.route('/', methods=['GET'])
@login_required
def index():
    """Página inicial de automação"""
    # Verificar se o usuário tem configurações de automação
    automation_settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
    theme_count = AutomationTheme.query.filter_by(user_id=current_user.id).count()
    feed_count = RSSFeed.query.filter_by(user_id=current_user.id).count()
    
    # Se o usuário já tem temas ou feeds, mostrar a página principal de automação
    if theme_count > 0 or feed_count > 0:
        return render_template('automation/index.html', 
                              automation_settings=automation_settings,
                              theme_count=theme_count,
                              feed_count=feed_count)
    
    # Caso contrário, mostrar a página de placeholder com instruções
    return render_template('automation/placeholder.html')

@automation_bp.route('/themes', methods=['GET'])
@login_required
def themes_list():
    """Lista de temas para automação"""
    themes = AutomationTheme.query.filter_by(user_id=current_user.id).order_by(AutomationTheme.priority.desc()).all()
    return render_template('automation/themes.html', themes=themes)

@automation_bp.route('/themes', methods=['POST'])
@login_required
def create_theme():
    """Criar novo tema de automação"""
    data = request.json
    
    if not data or not data.get('name') or not data.get('keywords'):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    try:
        theme = AutomationTheme(
            name=data['name'],
            keywords=data['keywords'],
            priority=int(data.get('priority', 0)),
            is_active=data.get('is_active', True),
            user_id=current_user.id
        )
        
        db.session.add(theme)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tema criado com sucesso', 'theme_id': theme.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar tema: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao criar tema: {str(e)}'}), 500

@automation_bp.route('/themes/<int:theme_id>', methods=['GET'])
@login_required
def get_theme(theme_id):
    """Obter detalhes de um tema específico"""
    theme = AutomationTheme.query.filter_by(id=theme_id, user_id=current_user.id).first()
    
    if not theme:
        return jsonify({'success': False, 'message': 'Tema não encontrado'}), 404
    
    return jsonify({
        'success': True,
        'theme': {
            'id': theme.id,
            'name': theme.name,
            'keywords': theme.keywords,
            'priority': theme.priority,
            'is_active': theme.is_active
        }
    })

@automation_bp.route('/themes/<int:theme_id>', methods=['PUT'])
@login_required
def update_theme(theme_id):
    """Atualizar um tema existente"""
    theme = AutomationTheme.query.filter_by(id=theme_id, user_id=current_user.id).first()
    
    if not theme:
        return jsonify({'success': False, 'message': 'Tema não encontrado'}), 404
    
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    try:
        theme.name = data.get('name', theme.name)
        theme.keywords = data.get('keywords', theme.keywords)
        theme.priority = int(data.get('priority', theme.priority))
        theme.is_active = data.get('is_active', theme.is_active)
        theme.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tema atualizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar tema: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao atualizar tema: {str(e)}'}), 500

@automation_bp.route('/themes/<int:theme_id>', methods=['DELETE'])
@login_required
def delete_theme(theme_id):
    """Excluir um tema"""
    theme = AutomationTheme.query.filter_by(id=theme_id, user_id=current_user.id).first()
    
    if not theme:
        return jsonify({'success': False, 'message': 'Tema não encontrado'}), 404
    
    try:
        db.session.delete(theme)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tema excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir tema: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao excluir tema: {str(e)}'}), 500

@automation_bp.route('/themes/import', methods=['POST'])
@login_required
def import_themes():
    """Importar temas de um arquivo CSV"""
    if 'csvFile' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['csvFile']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'O arquivo deve ser um CSV'}), 400
    
    try:
        # Ler o arquivo CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        
        # Pular o cabeçalho
        next(csv_reader, None)
        
        themes_added = 0
        errors = []
        
        for row in csv_reader:
            if len(row) < 2:
                errors.append(f"Linha ignorada: {','.join(row)} - Formato inválido")
                continue
            
            name = row[0].strip()
            keywords = row[1].strip()
            priority = 0
            
            if len(row) >= 3 and row[2].strip():
                try:
                    priority = int(row[2].strip())
                except ValueError:
                    priority = 0
            
            if not name or not keywords:
                errors.append(f"Linha ignorada: {','.join(row)} - Nome ou palavras-chave vazios")
                continue
            
            # Verificar se o tema já existe
            existing_theme = AutomationTheme.query.filter_by(name=name, user_id=current_user.id).first()
            
            if existing_theme:
                # Atualizar tema existente
                existing_theme.keywords = keywords
                existing_theme.priority = priority
                existing_theme.updated_at = datetime.utcnow()
                themes_added += 1
            else:
                # Criar novo tema
                theme = AutomationTheme(
                    name=name,
                    keywords=keywords,
                    priority=priority,
                    is_active=True,
                    user_id=current_user.id
                )
                db.session.add(theme)
                themes_added += 1
        
        db.session.commit()
        
        message = f"{themes_added} temas importados com sucesso."
        if errors:
            message += f" {len(errors)} linhas com erros."
        
        return jsonify({'success': True, 'message': message, 'errors': errors})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao importar temas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao importar temas: {str(e)}'}), 500

@automation_bp.route('/feeds', methods=['GET'])
@login_required
def feeds_list():
    """Lista de feeds RSS"""
    feeds = RSSFeed.query.filter_by(user_id=current_user.id).all()
    themes = AutomationTheme.query.filter_by(user_id=current_user.id).all()
    news_items = NewsItem.query.join(RSSFeed).filter(RSSFeed.user_id == current_user.id).order_by(NewsItem.published_date.desc()).limit(20).all()
    return render_template('automation/feeds.html', feeds=feeds, themes=themes, news_items=news_items)

@automation_bp.route('/feeds', methods=['POST'])
@login_required
def create_feed():
    """Criar novo feed RSS"""
    data = request.json
    
    if not data or not data.get('name') or not data.get('url') or not data.get('theme_id'):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se o tema existe e pertence ao usuário
    theme = AutomationTheme.query.filter_by(id=data['theme_id'], user_id=current_user.id).first()
    if not theme:
        return jsonify({'success': False, 'message': 'Tema não encontrado'}), 404
    
    try:
        feed = RSSFeed(
            name=data['name'],
            url=data['url'],
            is_active=data.get('is_active', True),
            theme_id=data['theme_id'],
            user_id=current_user.id
        )
        
        db.session.add(feed)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Feed criado com sucesso', 'feed_id': feed.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar feed: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao criar feed: {str(e)}'}), 500

@automation_bp.route('/feeds/<int:feed_id>', methods=['GET'])
@login_required
def get_feed(feed_id):
    """Obter detalhes de um feed específico"""
    feed = RSSFeed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    
    if not feed:
        return jsonify({'success': False, 'message': 'Feed não encontrado'}), 404
    
    return jsonify({
        'success': True,
        'feed': {
            'id': feed.id,
            'name': feed.name,
            'url': feed.url,
            'theme_id': feed.theme_id,
            'is_active': feed.is_active,
            'last_fetch': feed.last_fetch.isoformat() if feed.last_fetch else None
        }
    })

@automation_bp.route('/feeds/<int:feed_id>', methods=['PUT'])
@login_required
def update_feed(feed_id):
    """Atualizar um feed existente"""
    feed = RSSFeed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    
    if not feed:
        return jsonify({'success': False, 'message': 'Feed não encontrado'}), 404
    
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se o tema existe e pertence ao usuário
    if data.get('theme_id'):
        theme = AutomationTheme.query.filter_by(id=data['theme_id'], user_id=current_user.id).first()
        if not theme:
            return jsonify({'success': False, 'message': 'Tema não encontrado'}), 404
    
    try:
        feed.name = data.get('name', feed.name)
        feed.url = data.get('url', feed.url)
        feed.is_active = data.get('is_active', feed.is_active)
        if data.get('theme_id'):
            feed.theme_id = data['theme_id']
        feed.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Feed atualizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar feed: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao atualizar feed: {str(e)}'}), 500

@automation_bp.route('/feeds/<int:feed_id>', methods=['DELETE'])
@login_required
def delete_feed(feed_id):
    """Excluir um feed"""
    feed = RSSFeed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    
    if not feed:
        return jsonify({'success': False, 'message': 'Feed não encontrado'}), 404
    
    try:
        # Excluir também todos os itens de notícia relacionados ao feed
        NewsItem.query.filter_by(rss_feed_id=feed.id).delete()
        db.session.delete(feed)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Feed excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir feed: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao excluir feed: {str(e)}'}), 500

@automation_bp.route('/settings', methods=['POST'])
@login_required
def save_automation_settings():
    """Salvar configurações de automação"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se a configuração WordPress existe e pertence ao usuário
    wordpress_config_id = data.get('wordpress_config_id')
    if wordpress_config_id:
        wp_config = WordPressConfig.query.filter_by(id=wordpress_config_id, user_id=current_user.id).first()
        if not wp_config:
            return jsonify({'success': False, 'message': 'Configuração WordPress não encontrada'}), 404
    
    try:
        # Buscar ou criar configurações de automação
        settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            settings = AutomationSettings(
                user_id=current_user.id,
                is_active=data.get('is_active', True),
                post_interval_hours=data.get('post_interval_hours', 6),
                min_word_count=data.get('min_word_count', 700),
                max_word_count=data.get('max_word_count', 1500),
                timezone_offset=data.get('timezone_offset', -3),
                active_hours_start=data.get('active_hours_start', 8),
                active_hours_end=data.get('active_hours_end', 22),
                wordpress_config_id=wordpress_config_id
            )
            db.session.add(settings)
        else:
            settings.is_active = data.get('is_active', settings.is_active)
            settings.post_interval_hours = data.get('post_interval_hours', settings.post_interval_hours)
            settings.min_word_count = data.get('min_word_count', settings.min_word_count)
            settings.max_word_count = data.get('max_word_count', settings.max_word_count)
            settings.timezone_offset = data.get('timezone_offset', settings.timezone_offset)
            settings.active_hours_start = data.get('active_hours_start', settings.active_hours_start)
            settings.active_hours_end = data.get('active_hours_end', settings.active_hours_end)
            settings.wordpress_config_id = wordpress_config_id
            settings.updated_at = datetime.utcnow()
        
        # Calcular a próxima execução agendada (se estiver ativo)
        if settings.is_active:
            now = datetime.utcnow()
            next_run = now + timedelta(hours=1)  # Por padrão, inicia dentro de 1 hora
            settings.next_scheduled_run = next_run
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar configurações: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao salvar configurações: {str(e)}'}), 500

@automation_bp.route('/feeds/<int:feed_id>/fetch', methods=['POST'])
@login_required
def fetch_feed(feed_id):
    """Buscar e processar novas notícias de um feed RSS"""
    from services.rss_service import fetch_and_process_feed
    
    feed = RSSFeed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    
    if not feed:
        return jsonify({'success': False, 'message': 'Feed não encontrado'}), 404
    
    try:
        # Buscar e processar o feed
        new_items_count, total_items = fetch_and_process_feed(feed)
        
        # Atualizar a data da última busca
        feed.last_fetch = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{new_items_count} novos itens encontrados de um total de {total_items}',
            'new_items_count': new_items_count,
            'total_items': total_items
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao buscar feed: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao buscar feed: {str(e)}'}), 500

@automation_bp.route('/news/<int:news_item_id>/process', methods=['POST'])
@login_required
def process_news_item(news_item_id):
    """Processar item de notícia manualmente para criar um artigo"""
    from services.ai_service import generate_article_from_news
    
    news_item = NewsItem.query.join(RSSFeed).filter(
        NewsItem.id == news_item_id,
        RSSFeed.user_id == current_user.id
    ).first()
    
    if not news_item:
        return jsonify({'success': False, 'message': 'Item de notícia não encontrado'}), 404
    
    # Verificar se já foi processado
    if news_item.is_processed:
        return jsonify({'success': False, 'message': 'Este item já foi processado'}), 400
    
    # Verificar se existe um modelo de IA configurado
    api_key_claude = APIKey.query.filter_by(user_id=current_user.id, type=APIType.CLAUDE).first()
    api_key_gpt = APIKey.query.filter_by(user_id=current_user.id, type=APIType.GPT).first()
    
    if not api_key_claude and not api_key_gpt:
        return jsonify({'success': False, 'message': 'Configure pelo menos uma chave de API para IA'}), 400
    
    # Por padrão, preferir Claude se disponível
    ai_model = AIModel.CLAUDE if api_key_claude else AIModel.GPT
    
    # Verificar configurações de WordPress
    wp_config = WordPressConfig.query.filter_by(user_id=current_user.id, is_default=True).first()
    if not wp_config:
        wp_config = WordPressConfig.query.filter_by(user_id=current_user.id).first()
    
    if not wp_config:
        return jsonify({'success': False, 'message': 'Configure uma conta WordPress primeiro'}), 400
    
    try:
        # Gerar artigo a partir da notícia
        article = generate_article_from_news(news_item, ai_model, current_user.id, wp_config.id)
        
        # Marcar como processado
        news_item.is_processed = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Artigo criado com sucesso: "{article.title}"',
            'article_id': article.id
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar notícia: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao processar notícia: {str(e)}'}), 500

@automation_bp.route('/schedule', methods=['POST'])
@login_required
def schedule_automation():
    """Agendar geração e publicação automática de artigos"""
    data = request.form  # Usar form data para submissão de formulário HTML
    
    if not data:
        flash('Dados incompletos. Por favor preencha todos os campos.', 'danger')
        return redirect(url_for('automation.index'))
    
    # Verificar dados necessários
    schedule_type = data.get('scheduleType')
    if not schedule_type or schedule_type not in ['themes', 'rss']:
        flash('Tipo de agendamento inválido. Escolha temas ou feeds RSS.', 'danger')
        return redirect(url_for('automation.index'))
    
    ai_model = data.get('aiModel')
    if not ai_model or ai_model not in ['claude', 'gpt']:
        flash('Modelo de IA inválido. Escolha Claude ou GPT.', 'danger')
        return redirect(url_for('automation.index'))
    
    # Validar configurações de publicação
    settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        return jsonify({'success': False, 'message': 'Configure as opções de automação primeiro'}), 400
    
    if not settings.wordpress_config_id:
        return jsonify({'success': False, 'message': 'Configure um site WordPress para publicação'}), 400
    
    # Verificar se há temas ou feeds disponíveis
    if schedule_type == 'themes':
        themes = AutomationTheme.query.filter_by(user_id=current_user.id, is_active=True).all()
        if not themes:
            return jsonify({'success': False, 'message': 'Nenhum tema ativo encontrado'}), 400
    elif schedule_type == 'rss':
        feeds = RSSFeed.query.filter_by(user_id=current_user.id, is_active=True).all()
        if not feeds:
            return jsonify({'success': False, 'message': 'Nenhum feed RSS ativo encontrado'}), 400
    
    try:
        # Preparar agendamento
        num_articles = int(data.get('num_articles', 5))
        interval_hours = int(data.get('interval_hours', 6))
        
        # Pegar a data/hora de início
        schedule_date = data.get('schedule_date')
        schedule_time = data.get('schedule_time')
        
        if not schedule_date or not schedule_time:
            return jsonify({'success': False, 'message': 'Data e hora de início não fornecidas'}), 400
        
        try:
            start_datetime = datetime.strptime(f"{schedule_date}T{schedule_time}", "%Y-%m-%dT%H:%M")
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data/hora inválido'}), 400
        
        # Verificar se a data é no futuro
        if start_datetime < datetime.now():
            return jsonify({'success': False, 'message': 'A data e hora de início devem ser no futuro'}), 400
        
        # Configurar publicação imediata ou não
        publish_immediately = data.get('publish_immediately', False)
        
        # Criar artigos programados
        ai_model_enum = AIModel.CLAUDE if ai_model == 'claude' else AIModel.GPT
        
        # Preparar o agendamento de múltiplos artigos
        scheduled_count = 0
        current_datetime = start_datetime
        
        if schedule_type == 'themes':
            # Usar temas para gerar artigos
            for i in range(num_articles):
                # Selecionar um tema com base na prioridade
                themes_sorted = sorted(themes, key=lambda x: x.priority, reverse=True)
                selected_theme = themes_sorted[i % len(themes_sorted)]
                
                # Criar artigo programado
                article = Article(
                    title=f"Artigo programado: {selected_theme.name}",
                    content="Este conteúdo será gerado automaticamente.",
                    status=ArticleStatus.SCHEDULED,
                    scheduled_date=current_datetime,
                    ai_model=ai_model_enum,
                    is_automated=True,
                    source_type="keyword",
                    keyword=selected_theme.keywords.split(',')[0].strip(),  # Usar primeira palavra-chave
                    user_id=current_user.id,
                    wordpress_config_id=settings.wordpress_config_id,
                    theme_id=selected_theme.id
                )
                
                db.session.add(article)
                scheduled_count += 1
                
                # Avançar para o próximo horário de agendamento
                current_datetime = current_datetime + timedelta(hours=interval_hours)
        
        elif schedule_type == 'rss':
            # Verificar se há notícias não processadas
            news_items = NewsItem.query.join(RSSFeed).filter(
                RSSFeed.user_id == current_user.id,
                NewsItem.is_processed == False
            ).order_by(NewsItem.published_date.desc()).limit(num_articles).all()
            
            if not news_items:
                # Buscar feeds automaticamente
                for feed in feeds:
                    from services.rss_service import fetch_and_process_feed
                    fetch_and_process_feed(feed)
                
                # Buscar novamente as notícias
                news_items = NewsItem.query.join(RSSFeed).filter(
                    RSSFeed.user_id == current_user.id,
                    NewsItem.is_processed == False
                ).order_by(NewsItem.published_date.desc()).limit(num_articles).all()
            
            # Agendar artigos com base nas notícias
            for i, news_item in enumerate(news_items):
                article = Article(
                    title=f"Reescrita: {news_item.title[:100]}",
                    content="Este conteúdo será gerado automaticamente a partir da notícia.",
                    status=ArticleStatus.SCHEDULED,
                    scheduled_date=current_datetime,
                    ai_model=ai_model_enum,
                    is_automated=True,
                    source_type="rss",
                    source_url=news_item.link,
                    user_id=current_user.id,
                    wordpress_config_id=settings.wordpress_config_id,
                    news_item_id=news_item.id
                )
                
                db.session.add(article)
                news_item.is_processed = True
                scheduled_count += 1
                
                # Avançar para o próximo horário de agendamento
                current_datetime = current_datetime + timedelta(hours=interval_hours)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Agendamento configurado com sucesso para {scheduled_count} artigos a partir de {schedule_date} {schedule_time}'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao agendar automação: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao agendar automação: {str(e)}'}), 500