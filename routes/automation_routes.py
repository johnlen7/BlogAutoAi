import csv
import io
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import AutomationTheme, RSSFeed, NewsItem, AutomationSettings
from models import Article, ArticleStatus, AIModel, RepeatSchedule, LogType, ArticleLog, WordPressConfig

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
    return render_template('automation/feeds.html', feeds=feeds, themes=themes)