import csv
import io
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import (
    AutomationTheme, RSSFeed, NewsItem, AutomationSettings,
    Article, ArticleStatus, AIModel, RepeatSchedule, LogType, 
    ArticleLog, WordPressConfig, APIKey, APIType, SchedulerLog
)
from services.automation_monitor import AutomationMonitor

logger = logging.getLogger(__name__)

automation_bp = Blueprint('automation', __name__, url_prefix='/automation')

@automation_bp.route('/', methods=['GET'])
@login_required
def index():
    """Página inicial de automação - 100% funcional"""
    # Buscar configurações de automação do usuário
    automation_settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
    
    # Buscar contagem de temas e feeds
    theme_count = AutomationTheme.query.filter_by(user_id=current_user.id).count()
    feed_count = RSSFeed.query.filter_by(user_id=current_user.id).count()
    
    # Buscar configurações WordPress para o usuário
    wordpress_configs = WordPressConfig.query.filter_by(user_id=current_user.id).all()
    
    # Buscar artigos programados
    scheduled_articles = Article.query.filter_by(
        user_id=current_user.id,
        status=ArticleStatus.SCHEDULED
    ).order_by(Article.scheduled_date.asc()).all()
    
    # Total de artigos publicados automaticamente
    auto_published_count = Article.query.filter_by(
        user_id=current_user.id,
        status=ArticleStatus.PUBLISHED,
        is_automated=True
    ).count()
    
    # Obter status de automação e saúde do sistema
    automation_status = AutomationMonitor.get_automation_status(current_user.id)
    system_health = AutomationMonitor.check_health()
    
    # Sempre mostrar a página principal de automação (funcional)
    return render_template('automation/index.html', 
                          automation_settings=automation_settings,
                          theme_count=theme_count,
                          feed_count=feed_count,
                          wordpress_configs=wordpress_configs,
                          scheduled_articles=scheduled_articles,
                          auto_published_count=auto_published_count,
                          automation_status=automation_status,
                          system_health=system_health)

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
    # Processar dados do formulário (form data)
    if request.method == 'POST':
        # Obter dados do formulário
        is_active = 'is_active' in request.form
        post_interval_hours = request.form.get('post_interval_hours', type=int, default=6)
        min_word_count = request.form.get('min_word_count', type=int, default=700)
        max_word_count = request.form.get('max_word_count', type=int, default=1500)
        timezone_offset = request.form.get('timezone_offset', type=int, default=-3)
        active_hours_start = request.form.get('active_hours_start', type=int, default=8)
        active_hours_end = request.form.get('active_hours_end', type=int, default=22)
        wordpress_config_id = request.form.get('wordpress_config_id', type=int)
        
        # Validações
        if not wordpress_config_id:
            flash('Por favor, selecione um site WordPress', 'error')
            return redirect(url_for('automation.index'))
        
        # Verificar se a configuração WordPress existe e pertence ao usuário
        wp_config = WordPressConfig.query.filter_by(id=wordpress_config_id, user_id=current_user.id).first()
        if not wp_config:
            flash('Configuração WordPress não encontrada', 'error')
            return redirect(url_for('automation.index'))
    
        try:
            # Buscar ou criar configurações de automação
            settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
            
            if not settings:
                settings = AutomationSettings(
                    user_id=current_user.id,
                    is_active=is_active,
                    post_interval_hours=post_interval_hours,
                    min_word_count=min_word_count,
                    max_word_count=max_word_count,
                    timezone_offset=timezone_offset,
                    active_hours_start=active_hours_start,
                    active_hours_end=active_hours_end,
                    wordpress_config_id=wordpress_config_id
                )
                db.session.add(settings)
            else:
                settings.is_active = is_active
                settings.post_interval_hours = post_interval_hours
                settings.min_word_count = min_word_count
                settings.max_word_count = max_word_count
                settings.timezone_offset = timezone_offset
                settings.active_hours_start = active_hours_start
                settings.active_hours_end = active_hours_end
                settings.wordpress_config_id = wordpress_config_id
                settings.updated_at = datetime.utcnow()
            
            # Calcular a próxima execução agendada (se estiver ativo)
            if settings.is_active:
                now = datetime.utcnow()
                next_run = now + timedelta(hours=1)  # Por padrão, inicia dentro de 1 hora
                settings.next_scheduled_run = next_run
            
            db.session.commit()
            
            flash('Configurações de automação salvas com sucesso!', 'success')
            return redirect(url_for('automation.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar configurações: {str(e)}")
            flash(f'Erro ao salvar configurações: {str(e)}', 'error')
            return redirect(url_for('automation.index'))

@automation_bp.route('/feeds/<int:feed_id>/fetch', methods=['POST'])
@login_required
def fetch_feed(feed_id):
    """Buscar e processar novas notícias de um feed RSS com tratamento de erros aprimorado"""
    from services.rss_service import fetch_and_process_feed
    
    feed = RSSFeed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    
    if not feed:
        return jsonify({'success': False, 'message': 'Feed não encontrado'}), 404
    
    try:
        # Buscar e processar o feed
        new_items, total_items = fetch_and_process_feed(feed)
        new_items_count = len(new_items) if new_items else 0
        
        # Atualizar a data da última busca
        feed.last_fetch = datetime.utcnow()
        db.session.commit()
        
        # Registrar ação no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "update",
            f"Feed '{feed.name}' atualizado: {new_items_count} novos itens",
            "success"
        )
        
        return jsonify({
            'success': True, 
            'message': f'{new_items_count} novos itens encontrados de um total de {total_items}',
            'new_items_count': new_items_count,
            'total_items': total_items
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao buscar feed: {str(e)}")
        
        # Registrar falha no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "error",
            f"Erro ao processar feed '{feed.name}': {str(e)[:100]}...",
            "error"
        )
        
        return jsonify({'success': False, 'message': f'Erro ao buscar feed: {str(e)}'}), 500

@automation_bp.route('/news/<int:news_item_id>/process', methods=['POST'])
@login_required
def process_news_item(news_item_id):
    """Processar item de notícia manualmente para criar um artigo"""
    
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
        # Usar o novo processador de notícias mais robusto
        from services.news_processor import process_news_item as process_news_function
        
        # Processar a notícia com tratamento de erros melhorado
        article, success, message = process_news_function(
            news_item=news_item, 
            ai_model=ai_model, 
            user_id=current_user.id, 
            wp_config_id=wp_config.id
        )
        
        if success and article:
            # Processo completo bem-sucedido
            return jsonify({
                'success': True, 
                'message': f'Artigo criado com sucesso: "{article.title}"',
                'article_id': article.id
            })
        elif article:
            # Artigo criado mas com alguns problemas
            return jsonify({
                'success': True, 
                'warning': True,
                'message': f'Artigo criado como rascunho, mas com avisos: {message}',
                'article_id': article.id
            })
        else:
            # Falha completa
            return jsonify({
                'success': False, 
                'message': f'Falha ao processar notícia: {message}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar notícia: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao processar notícia: {str(e)}'}), 500

@automation_bp.route('/monitoring', methods=['GET'])
@login_required
def monitoring():
    """Página de monitoramento e status da automação"""
    # Obter status de automação e saúde do sistema
    automation_status = AutomationMonitor.get_automation_status(current_user.id)
    system_health = AutomationMonitor.check_health()
    
    return render_template('automation/monitoring.html',
                          automation_status=automation_status,
                          system_health=system_health)

@automation_bp.route('/repair_scheduled_articles', methods=['GET'])
@login_required
def repair_scheduled_articles():
    """Corrige artigos agendados com problemas"""
    try:
        # Encontrar artigos com status SCHEDULED mas sem data
        invalid_articles = Article.query.filter(
            Article.status == ArticleStatus.SCHEDULED,
            Article.scheduled_date == None,
            Article.user_id == current_user.id
        ).all()
        
        # Configurar data de agendamento para agora + 1 hora
        now = datetime.utcnow()
        next_hour = now + timedelta(hours=1)
        
        count = 0
        for article in invalid_articles:
            article.scheduled_date = next_hour
            count += 1
            # Incrementar a próxima data em 1 hora para cada artigo
            next_hour = next_hour + timedelta(hours=1)
        
        db.session.commit()
        
        # Registrar ação no monitor
        if count > 0:
            AutomationMonitor.register_event(
                current_user.id,
                "repair",
                f"Corrigidos {count} artigos agendados sem data",
                "success"
            )
            flash(f'{count} artigos agendados foram reparados com sucesso.', 'success')
        else:
            flash('Nenhum artigo com problemas foi encontrado.', 'info')
            
        return redirect(url_for('automation.monitoring'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao reparar artigos agendados: {str(e)}")
        flash(f'Erro ao reparar artigos: {str(e)}', 'danger')
        return redirect(url_for('automation.monitoring'))

@automation_bp.route('/fetch_all_feeds', methods=['GET'])
@login_required
def fetch_all_feeds():
    """Atualiza todos os feeds RSS do usuário usando processador aprimorado"""
    try:
        from services.news_processor import fetch_process_all_feeds
        
        # Usar o novo processador aprimorado para buscar e processar todos os feeds
        stats = fetch_process_all_feeds(current_user.id)
        
        if stats['feeds_processed'] == 0:
            flash('Nenhum feed RSS ativo encontrado.', 'info')
            return redirect(url_for('automation.monitoring'))
        
        # Registrar ação no monitor
        message = (f"Processados {stats['feeds_processed']} feeds ({stats['new_items']} novas notícias). "
                  f"{stats['feeds_with_errors']} feeds com erros.")
                  
        status = "warning" if stats['feeds_with_errors'] > 0 else "success"
        
        AutomationMonitor.register_event(
            current_user.id,
            "update",
            message,
            status
        )
        
        # Exibir mensagem para o usuário
        if stats['feeds_with_errors'] > 0:
            flash(f'{stats["feeds_processed"]} feeds atualizados com {stats["new_items"]} novas notícias. '
                  f'Atenção: {stats["feeds_with_errors"]} feeds tiveram erros durante o processamento.', 'warning')
        else:
            flash(f'{stats["feeds_processed"]} feeds foram atualizados com {stats["new_items"]} novas notícias encontradas.', 'success')
            
        return redirect(url_for('automation.monitoring'))
    except Exception as e:
        logger.error(f"Erro ao atualizar feeds: {str(e)}")
        flash(f'Erro ao atualizar feeds: {str(e)}', 'danger')
        return redirect(url_for('automation.monitoring'))

@automation_bp.route('/clear_logs', methods=['GET'])
@login_required
def clear_logs():
    """Limpa logs antigos do sistema"""
    try:
        # Remover logs com mais de 30 dias
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = db.session.query(SchedulerLog).filter(
            SchedulerLog.created_at < thirty_days_ago
        ).delete()
        
        db.session.commit()
        
        # Registrar ação no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "maintenance",
            f"Removidos {result} logs antigos",
            "success"
        )
        
        flash(f'{result} logs antigos foram removidos com sucesso.', 'success')
        return redirect(url_for('automation.monitoring'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao limpar logs: {str(e)}")
        flash(f'Erro ao limpar logs: {str(e)}', 'danger')
        return redirect(url_for('automation.monitoring'))

@automation_bp.route('/restart_scheduler', methods=['GET'])
@login_required
def restart_scheduler():
    """Reinicia o agendador de tarefas"""
    try:
        from services.scheduler_service import restart_scheduler as restart_scheduler_service
        
        # Reiniciar o agendador
        restart_scheduler_service()
        
        # Registrar ação no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "maintenance",
            "Agendador de tarefas reiniciado",
            "success"
        )
        
        flash('O agendador de tarefas foi reiniciado com sucesso.', 'success')
        return redirect(url_for('automation.monitoring'))
    except Exception as e:
        logger.error(f"Erro ao reiniciar agendador: {str(e)}")
        flash(f'Erro ao reiniciar agendador: {str(e)}', 'danger')
        return redirect(url_for('automation.monitoring'))

@automation_bp.route('/schedule_automation', methods=['POST'])
@login_required
def schedule_automation():
    """Agendar geração e publicação automática de artigos"""
    if request.is_json:
        data = request.json  # Obter dados JSON da requisição
    else:
        data = request.form  # Usar form data para submissão de formulário HTML
    
    if not data:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Dados incompletos. Por favor preencha todos os campos.'})
        else:
            flash('Dados incompletos. Por favor preencha todos os campos.', 'danger')
            return redirect(url_for('automation.index'))
    
    # Verificar dados necessários
    schedule_type = data.get('content_type')
    if not schedule_type or schedule_type not in ['themes', 'rss']:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Tipo de agendamento inválido. Escolha temas ou feeds RSS.'})
        else:
            flash('Tipo de agendamento inválido. Escolha temas ou feeds RSS.', 'danger')
            return redirect(url_for('automation.index'))
    
    ai_model = data.get('ai_model')
    if not ai_model or ai_model not in ['claude', 'gpt']:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Modelo de IA inválido. Escolha Claude ou GPT.'})
        else:
            flash('Modelo de IA inválido. Escolha Claude ou GPT.', 'danger')
            return redirect(url_for('automation.index'))
    
    # Validar configurações de publicação
    settings = AutomationSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Configure as opções de automação primeiro antes de agendar artigos.'})
        else:
            flash('Configure as opções de automação primeiro antes de agendar artigos.', 'danger')
            return redirect(url_for('automation.index'))
    
    if not settings.wordpress_config_id:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Configure um site WordPress para publicação nas configurações de automação.'})
        else:
            flash('Configure um site WordPress para publicação nas configurações de automação.', 'danger')
            return redirect(url_for('automation.index'))
    
    # Verificar se há temas ou feeds disponíveis
    if schedule_type == 'themes':
        themes = AutomationTheme.query.filter_by(user_id=current_user.id, is_active=True).all()
        if not themes:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Nenhum tema ativo encontrado. Por favor, crie pelo menos um tema.'})
            else:
                flash('Nenhum tema ativo encontrado. Por favor, crie pelo menos um tema.', 'danger')
                return redirect(url_for('automation.index'))
    elif schedule_type == 'rss':
        feeds = RSSFeed.query.filter_by(user_id=current_user.id, is_active=True).all()
        if not feeds:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Nenhum feed RSS ativo encontrado. Por favor, adicione pelo menos um feed.'})
            else:
                flash('Nenhum feed RSS ativo encontrado. Por favor, adicione pelo menos um feed.', 'danger')
                return redirect(url_for('automation.index'))
    
    try:
        # Preparar agendamento
        try:
            num_articles = int(data.get('num_articles', 5))
        except (ValueError, TypeError):
            num_articles = 5
            
        try:
            interval_hours = int(data.get('interval', 6))  # Nome do campo ajustado
        except (ValueError, TypeError):
            interval_hours = 6
        
        # Pegar a data/hora de início
        schedule_date = data.get('schedule_date')
        schedule_time = data.get('schedule_time', '08:00')
        
        if not schedule_date:
            flash('Data e hora de início não fornecidas. Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('automation.index'))
        
        try:
            start_datetime = datetime.strptime(f"{schedule_date}T{schedule_time}", "%Y-%m-%dT%H:%M")
        except ValueError:
            flash('Formato de data/hora inválido. Use o formato correto.', 'danger')
            return redirect(url_for('automation.index'))
        
        # Verificar se a data é no futuro
        if start_datetime < datetime.now():
            flash('A data e hora de início devem ser no futuro', 'danger')
            return redirect(url_for('automation.index'))
        
        # Configurar publicação imediata ou não
        publish_immediately = 'publish_immediately' in data
        
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
            # Obter todos os feeds RSS ativos do usuário
            feeds = RSSFeed.query.filter_by(user_id=current_user.id, is_active=True).all()
            
            if not feeds:
                flash('Nenhum feed RSS encontrado. Por favor, adicione pelo menos um feed.', 'warning')
                return redirect(url_for('automation.index'))
            
            # Buscar notícias não processadas    
            news_items = NewsItem.query.join(RSSFeed).filter(
                RSSFeed.user_id == current_user.id,
                NewsItem.is_processed == False
            ).order_by(NewsItem.published_date.desc()).limit(num_articles).all()
            
            if not news_items:
                # Buscar feeds automaticamente para obter novos itens
                for feed in feeds:
                    try:
                        from services.rss_service import fetch_and_process_feed
                        fetch_and_process_feed(feed)
                    except Exception as e:
                        flash(f"Erro ao processar feed {feed.name}: {str(e)}", "danger")
                        logger.error(f"Erro ao processar feed {feed.name}: {str(e)}")
                
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
        
        # Atualizar próximo horário de execução nas configurações
        if settings and scheduled_count > 0:
            settings.next_scheduled_run = start_datetime
            db.session.commit()
        
        # Registrar a ação bem-sucedida no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "schedule",
            f"Agendamento configurado para {scheduled_count} artigos a partir de {schedule_date} {schedule_time}",
            "success"
        )
        
        # Responder de acordo com o tipo de requisição
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': f'Agendamento configurado com sucesso para {scheduled_count} artigos a partir de {schedule_date} {schedule_time}',
                'scheduled_count': scheduled_count,
                'start_time': start_datetime.isoformat()
            })
        else:
            flash(f'Agendamento configurado com sucesso para {scheduled_count} artigos a partir de {schedule_date} {schedule_time}', 'success')
            return redirect(url_for('automation.index'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao agendar automação: {str(e)}")
        
        # Registrar o erro no monitor
        AutomationMonitor.register_event(
            current_user.id,
            "schedule",
            f"Falha ao agendar automação: {str(e)}",
            "error"
        )
        
        if request.is_json:
            return jsonify({
                'success': False, 
                'message': f'Erro ao agendar automação: {str(e)}'
            })
        else:
            flash(f'Erro ao agendar automação: {str(e)}', 'danger')
            return redirect(url_for('automation.index'))