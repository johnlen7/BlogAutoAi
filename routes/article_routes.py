import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from models import (
    Article, ArticleStatus, AIModel, RepeatSchedule, 
    WordPressConfig, APIKey, APIType, ArticleLog, LogType
)
from services.ai_service import generate_article_from_news, generate_article_from_theme
from services.wordpress_service import WordPressService

logger = logging.getLogger(__name__)

article_bp = Blueprint('article', __name__)

@article_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new article view"""
    # Get available WordPress configurations
    wp_configs = WordPressConfig.query.filter_by(user_id=current_user.id).all()
    
    # Check if user has WordPress configurations
    if not wp_configs:
        flash('You need to set up a WordPress site before creating articles.', 'warning')
        return redirect(url_for('settings.wordpress_config'))
    
    # Get API keys
    gpt_key = APIKey.query.filter_by(
        user_id=current_user.id, 
        type=APIType.GPT
    ).first()
    
    claude_key = APIKey.query.filter_by(
        user_id=current_user.id, 
        type=APIType.CLAUDE
    ).first()
    
    # Check if user has API keys
    if not gpt_key and not claude_key:
        flash('You need to set up at least one AI API key before creating articles.', 'warning')
        return redirect(url_for('settings.api_keys'))
    
    # Render the creation form template
    return render_template(
        'create_article.html',
        wp_configs=wp_configs,
        has_gpt=bool(gpt_key),
        has_claude=bool(claude_key)
    )

@article_bp.route('/api/wordpress/categories', methods=['GET'])
@login_required
def get_wordpress_categories():
    """API endpoint to get WordPress categories"""
    # Get WordPress configuration
    config_id = request.args.get('config_id')
    
    if not config_id:
        # Get default config
        config = WordPressConfig.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).first()
        
        if not config:
            # Get any config
            config = WordPressConfig.query.filter_by(user_id=current_user.id).first()
            
        if not config:
            return jsonify({
                'success': False,
                'message': 'No WordPress configuration found.'
            }), 404
    else:
        # Get specified config
        config = WordPressConfig.query.get(config_id)
        
        if not config or config.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'WordPress configuration not found or access denied.'
            }), 403
    
    # Initialize WordPress service
    wp_service = WordPressService(config)
    
    # Get categories
    categories = wp_service.get_categories()
    
    return jsonify({
        'success': True,
        'categories': categories
    })

@article_bp.route('/api/generate-content', methods=['POST'])
@login_required
def generate_content():
    """API endpoint to generate article content from keyword or URL"""
    # Get request data
    data = request.json
    content_type = data.get('type', 'keyword')  # 'keyword' or 'url'
    content_value = data.get('value', '')
    model_type_str = data.get('model', 'claude')  # 'claude' or 'gpt'
    
    if not content_value:
        return jsonify({
            'success': False,
            'message': f'Please provide a {content_type}.'
        }), 400
    
    # Convert model type string to enum
    model_type = AIModel.CLAUDE if model_type_str.lower() == 'claude' else AIModel.GPT
    
    # Get API keys
    api_keys = {}
    
    gpt_key = APIKey.query.filter_by(
        user_id=current_user.id, 
        type=APIType.GPT
    ).first()
    
    claude_key = APIKey.query.filter_by(
        user_id=current_user.id, 
        type=APIType.CLAUDE
    ).first()
    
    if gpt_key:
        api_keys[AIModel.GPT.value] = gpt_key.key
    
    if claude_key:
        api_keys[AIModel.CLAUDE.value] = claude_key.key
    
    # Check if we have the right API key
    if model_type.value not in api_keys:
        return jsonify({
            'success': False,
            'message': f"API key for {model_type.value} is not configured."
        }), 400
    
    try:
        # Generate content based on type
        if content_type == 'keyword':
            # Criar tema temporário para geração
            temp_theme = type('TempTheme', (), {'name': 'Tema temporário', 'keywords': content_value, 'id': None})
            article = generate_article_from_theme(temp_theme, model_type, current_user.id, None)
            result = {'title': article.title, 'content': article.content}
        else:  # url
            # Para conteúdo baseado em URL, usamos uma abordagem diferente
            from services.rss_service import fetch_website_content
            
            # Buscar conteúdo da URL
            title, content = fetch_website_content(content_value)
            
            # Criar notícia temporária para geração
            temp_news = type('TempNews', (), {
                'title': title or 'Artigo sem título',
                'content': content or 'Conteúdo não encontrado', 
                'link': content_value,
                'id': None
            })
            
            article = generate_article_from_news(temp_news, model_type, current_user.id, None)
            result = {'title': article.title, 'content': article.content}
        
        return jsonify({
            'success': True,
            'content': result
        })
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error generating content: {str(e)}"
        }), 500

@article_bp.route('/api/save-article', methods=['POST'])
@login_required
def save_article():
    """API endpoint to save/update article"""
    # Get request data
    data = request.json
    
    article_id = data.get('article_id')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    meta_description = data.get('meta_description', '').strip()
    slug = data.get('slug', '').strip()
    tags = data.get('tags', '').strip()
    categories = data.get('categories', '').strip()
    featured_image_url = data.get('featured_image_url', '').strip()
    keyword = data.get('keyword', '').strip()
    source_url = data.get('source_url', '').strip()
    ai_model_str = data.get('ai_model', 'claude')
    wordpress_config_id = data.get('wordpress_config_id')
    
    # Convert AI model string to enum
    ai_model = AIModel.CLAUDE if ai_model_str.lower() == 'claude' else AIModel.GPT
    
    # Validate required fields
    if not title:
        return jsonify({
            'success': False,
            'message': 'Title is required.'
        }), 400
    
    if not content:
        return jsonify({
            'success': False,
            'message': 'Content is required.'
        }), 400
    
    if not wordpress_config_id:
        return jsonify({
            'success': False,
            'message': 'WordPress configuration is required.'
        }), 400
    
    try:
        # Check if we're updating an existing article
        if article_id:
            article = Article.query.get(article_id)
            
            # Check if article exists and belongs to current user
            if not article or article.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Article not found or access denied.'
                }), 404
            
            # Update article
            article.title = title
            article.content = content
            article.meta_description = meta_description
            article.slug = slug
            article.tags = tags
            article.categories = categories
            article.featured_image_url = featured_image_url
            article.wordpress_config_id = wordpress_config_id
            
        else:
            # Create new article
            article = Article(
                title=title,
                content=content,
                meta_description=meta_description,
                slug=slug,
                tags=tags,
                categories=categories,
                featured_image_url=featured_image_url,
                status=ArticleStatus.DRAFT,
                ai_model=ai_model,
                keyword=keyword,
                source_url=source_url,
                user_id=current_user.id,
                wordpress_config_id=wordpress_config_id
            )
            db.session.add(article)
        
        # Save changes
        db.session.commit()
        
        # Add log entry
        log = ArticleLog(
            article_id=article.id,
            message=f"Article {'updated' if article_id else 'created'} as draft",
            log_type=LogType.INFO
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Article {title} saved as draft.",
            'article_id': article.id
        })
        
    except Exception as e:
        logger.error(f"Error saving article: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error saving article: {str(e)}"
        }), 500

@article_bp.route('/edit/<int:article_id>', methods=['GET'])
@login_required
def edit(article_id):
    """Edit an existing article"""
    article = Article.query.get_or_404(article_id)
    
    # Check if article belongs to current user
    if article.user_id != current_user.id:
        flash('Access denied: This article does not belong to you.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get WordPress configurations
    wp_configs = WordPressConfig.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'edit_article.html',
        article=article,
        wp_configs=wp_configs
    )

@article_bp.route('/api/publish-article', methods=['POST'])
@login_required
def publish_article():
    """API endpoint to publish article immediately"""
    # Get request data
    data = request.json
    article_id = data.get('article_id')
    
    if not article_id:
        return jsonify({
            'success': False,
            'message': 'Article ID is required.'
        }), 400
    
    try:
        # Get article
        article = Article.query.get(article_id)
        
        # Check if article exists and belongs to current user
        if not article or article.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Article not found or access denied.'
            }), 404
        
        # Get WordPress configuration
        wp_config = WordPressConfig.query.get(article.wordpress_config_id)
        if not wp_config:
            return jsonify({
                'success': False,
                'message': 'WordPress configuration not found.'
            }), 400
        
        # Initialize WordPress service
        wp_service = WordPressService(wp_config)
        
        # Publish article
        success = wp_service.publish_article(article)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Article '{article.title}' published successfully."
            })
        else:
            return jsonify({
                'success': False,
                'message': "Failed to publish article. Check logs for details."
            }), 500
            
    except Exception as e:
        logger.error(f"Error publishing article: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error publishing article: {str(e)}"
        }), 500

@article_bp.route('/api/schedule-article', methods=['POST'])
@login_required
def schedule_article():
    """API endpoint to schedule article for future publishing"""
    # Get request data
    data = request.json
    article_id = data.get('article_id')
    scheduled_date = data.get('scheduled_date')
    repeat_schedule_str = data.get('repeat_schedule', 'none')
    
    if not article_id:
        return jsonify({
            'success': False,
            'message': 'Article ID is required.'
        }), 400
    
    if not scheduled_date:
        return jsonify({
            'success': False,
            'message': 'Scheduled date is required.'
        }), 400
    
    try:
        # Get article
        article = Article.query.get(article_id)
        
        # Check if article exists and belongs to current user
        if not article or article.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Article not found or access denied.'
            }), 404
        
        # Parse scheduled date
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Please use ISO format.'
            }), 400
        
        # Set repeat schedule
        repeat_schedule = RepeatSchedule.NONE
        if repeat_schedule_str == 'daily':
            repeat_schedule = RepeatSchedule.DAILY
        elif repeat_schedule_str == 'weekly':
            repeat_schedule = RepeatSchedule.WEEKLY
        elif repeat_schedule_str == 'monthly':
            repeat_schedule = RepeatSchedule.MONTHLY
        
        # Update article
        article.status = ArticleStatus.SCHEDULED
        article.scheduled_date = scheduled_datetime
        article.repeat_schedule = repeat_schedule
        
        # Add log entry
        log = ArticleLog(
            article_id=article.id,
            message=f"Article scheduled for publishing on {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            log_type=LogType.INFO
        )
        db.session.add(log)
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Article scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        })
        
    except Exception as e:
        logger.error(f"Error scheduling article: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error scheduling article: {str(e)}"
        }), 500

@article_bp.route('/api/export-article/<int:article_id>/<format_type>')
@login_required
def export_article(article_id, format_type):
    """API endpoint to export article as Markdown or docx"""
    article = Article.query.get_or_404(article_id)
    
    # Check if article belongs to current user
    if article.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Access denied: This article does not belong to you.'
        }), 403
    
    try:
        if format_type == 'markdown':
            # Convert HTML to Markdown
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            markdown_content = h.handle(article.content)
            
            # Create full markdown document
            full_content = f"# {article.title}\n\n"
            if article.meta_description:
                full_content += f"> {article.meta_description}\n\n"
            full_content += markdown_content
            
            # Add tags and categories if available
            if article.tags:
                full_content += f"\n\nTags: {article.tags}\n"
            if article.categories:
                full_content += f"Categories: {article.categories}\n"
            
            # Return as downloadable file
            from flask import Response
            response = Response(
                full_content,
                mimetype="text/markdown",
                headers={"Content-disposition": f"attachment; filename={article.slug}.md"}
            )
            return response
        
        else:
            # For simplicity, we'll just return an error since we can't generate docx in this context
            return jsonify({
                'success': False,
                'message': 'DOCX export is not implemented in this version.'
            }), 501
        
    except Exception as e:
        logger.error(f"Error exporting article: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error exporting article: {str(e)}"
        }), 500
