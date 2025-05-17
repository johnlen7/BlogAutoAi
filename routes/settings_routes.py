import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from models import WordPressConfig, APIKey, APIType, Article
from services.wordpress_service import WordPressService

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    """Main settings page"""
    return render_template('settings/index.html')

@settings_bp.route('/settings/wordpress', methods=['GET', 'POST'])
@login_required
def wordpress_config():
    """WordPress configuration settings"""
    configs = WordPressConfig.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        # Get form data
        action = request.form.get('action')
        
        if action == 'add':
            # Add new configuration
            name = request.form.get('name', '').strip()
            site_url = request.form.get('site_url', '').strip()
            username = request.form.get('username', '').strip()
            app_password = request.form.get('app_password', '').strip()
            is_default = request.form.get('is_default') == 'on'
            
            # Validate inputs
            if not name or not site_url or not username or not app_password:
                flash('All fields are required.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Normalize site URL
            if not site_url.startswith(('http://', 'https://')):
                site_url = 'https://' + site_url
            
            # Remove trailing slash
            site_url = site_url.rstrip('/')
            
            # Check if a config with the same name already exists
            existing = WordPressConfig.query.filter_by(
                user_id=current_user.id,
                name=name
            ).first()
            
            if existing:
                flash(f'A configuration with the name "{name}" already exists.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # If this is the default, update other configs
            if is_default:
                WordPressConfig.query.filter_by(
                    user_id=current_user.id,
                    is_default=True
                ).update({
                    'is_default': False
                })
            
            # Create new configuration
            config = WordPressConfig(
                name=name,
                site_url=site_url,
                username=username,
                app_password=app_password,
                is_default=is_default,
                user_id=current_user.id
            )
            
            db.session.add(config)
            db.session.commit()
            
            flash(f'WordPress configuration "{name}" added successfully.', 'success')
            return redirect(url_for('settings.wordpress_config'))
            
        elif action == 'edit':
            # Edit existing configuration
            config_id = request.form.get('config_id')
            name = request.form.get('name', '').strip()
            site_url = request.form.get('site_url', '').strip()
            username = request.form.get('username', '').strip()
            app_password = request.form.get('app_password', '').strip()
            is_default = request.form.get('is_default') == 'on'
            
            # Validate config_id
            if not config_id:
                flash('Invalid configuration.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Get configuration
            config = WordPressConfig.query.get(config_id)
            
            if not config or config.user_id != current_user.id:
                flash('Configuration not found or access denied.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Validate inputs
            if not name or not site_url or not username:
                flash('Name, site URL, and username are required.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Normalize site URL
            if not site_url.startswith(('http://', 'https://')):
                site_url = 'https://' + site_url
            
            # Remove trailing slash
            site_url = site_url.rstrip('/')
            
            # Check if a different config with the same name already exists
            existing = WordPressConfig.query.filter(
                WordPressConfig.user_id == current_user.id,
                WordPressConfig.name == name,
                WordPressConfig.id != config.id
            ).first()
            
            if existing:
                flash(f'A different configuration with the name "{name}" already exists.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # If this is the default, update other configs
            if is_default and not config.is_default:
                WordPressConfig.query.filter_by(
                    user_id=current_user.id,
                    is_default=True
                ).update({
                    'is_default': False
                })
            
            # Update configuration
            config.name = name
            config.site_url = site_url
            config.username = username
            config.is_default = is_default
            
            # Update password only if provided
            if app_password:
                config.app_password = app_password
            
            db.session.commit()
            
            flash(f'WordPress configuration "{name}" updated successfully.', 'success')
            return redirect(url_for('settings.wordpress_config'))
            
        elif action == 'delete':
            # Delete configuration
            config_id = request.form.get('config_id')
            
            # Validate config_id
            if not config_id:
                flash('Invalid configuration.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Get configuration
            config = WordPressConfig.query.get(config_id)
            
            if not config or config.user_id != current_user.id:
                flash('Configuration not found or access denied.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Check if there are articles using this configuration
            articles_count = Article.query.filter_by(
                wordpress_config_id=config.id
            ).count()
            
            if articles_count > 0:
                flash(f'Cannot delete configuration: {articles_count} articles are using it.', 'danger')
                return redirect(url_for('settings.wordpress_config'))
            
            # Delete configuration
            db.session.delete(config)
            db.session.commit()
            
            flash(f'WordPress configuration "{config.name}" deleted successfully.', 'success')
            return redirect(url_for('settings.wordpress_config'))
        
        else:
            flash('Invalid action.', 'danger')
    
    return render_template('settings/wordpress.html', configs=configs)

@settings_bp.route('/api/test-wordpress', methods=['POST'])
@login_required
def test_wordpress_connection():
    """API endpoint to test WordPress connection"""
    data = request.json
    
    # If testing an existing configuration
    if data.get('config_id'):
        config_id = data.get('config_id')
        config = WordPressConfig.query.get(config_id)
        
        if not config or config.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Configuration not found or access denied.'
            }), 403
    
    # If testing a new configuration
    else:
        site_url = data.get('site_url', '').strip()
        username = data.get('username', '').strip()
        app_password = data.get('app_password', '').strip()
        
        if not site_url or not username or not app_password:
            return jsonify({
                'success': False,
                'message': 'Site URL, username, and application password are required.'
            }), 400
        
        # Normalize site URL
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        
        # Remove trailing slash
        site_url = site_url.rstrip('/')
        
        # Create temporary config
        config = WordPressConfig(
            name='temp',
            site_url=site_url,
            username=username,
            app_password=app_password,
            user_id=current_user.id
        )
    
    try:
        # Test connection
        wp_service = WordPressService(config)
        success = wp_service.validate_connection()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Connection successful! Your WordPress credentials are working.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Connection failed. Please check your WordPress URL and credentials.'
            })
            
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        }), 500

@settings_bp.route('/settings/api-keys', methods=['GET', 'POST'])
@login_required
def api_keys():
    """API keys configuration settings"""
    # Get existing API keys
    gpt_key = APIKey.query.filter_by(
        user_id=current_user.id,
        type=APIType.GPT
    ).first()
    
    claude_key = APIKey.query.filter_by(
        user_id=current_user.id,
        type=APIType.CLAUDE
    ).first()
    
    unsplash_key = APIKey.query.filter_by(
        user_id=current_user.id,
        type=APIType.UNSPLASH
    ).first()
    
    # Handle form submission
    if request.method == 'POST':
        api_type = request.form.get('api_type')
        api_key = request.form.get('api_key', '').strip()
        
        if not api_type or not api_key:
            flash('API type and key are required.', 'danger')
            return redirect(url_for('settings.api_keys'))
        
        # Convert type string to enum
        try:
            api_type_enum = getattr(APIType, api_type.upper())
        except (AttributeError, KeyError):
            flash('Invalid API type.', 'danger')
            return redirect(url_for('settings.api_keys'))
        
        # Check if key already exists
        existing_key = APIKey.query.filter_by(
            user_id=current_user.id,
            type=api_type_enum
        ).first()
        
        if existing_key:
            # Update existing key
            existing_key.key = api_key
            db.session.commit()
            flash(f'{api_type.upper()} API key updated successfully.', 'success')
        else:
            # Create new key
            new_key = APIKey(
                type=api_type_enum,
                key=api_key,
                user_id=current_user.id
            )
            db.session.add(new_key)
            db.session.commit()
            flash(f'{api_type.upper()} API key added successfully.', 'success')
        
        return redirect(url_for('settings.api_keys'))
    
    return render_template(
        'settings/api_keys.html', 
        gpt_key=gpt_key,
        claude_key=claude_key,
        unsplash_key=unsplash_key
    )

@settings_bp.route('/settings/api-keys/delete/<api_type>', methods=['POST'])
@login_required
def delete_api_key(api_type):
    """Delete an API key"""
    try:
        # Convert type string to enum
        api_type_enum = getattr(APIType, api_type.upper())
    except (AttributeError, KeyError):
        flash('Invalid API type.', 'danger')
        return redirect(url_for('settings.api_keys'))
    
    # Get key
    key = APIKey.query.filter_by(
        user_id=current_user.id,
        type=api_type_enum
    ).first()
    
    if not key:
        flash(f'No {api_type.upper()} API key found.', 'warning')
        return redirect(url_for('settings.api_keys'))
    
    # Delete key
    db.session.delete(key)
    db.session.commit()
    
    flash(f'{api_type.upper()} API key deleted successfully.', 'success')
    return redirect(url_for('settings.api_keys'))

@settings_bp.route('/api/test-api-key', methods=['POST'])
@login_required
def test_api_key():
    """API endpoint to test API key validity"""
    data = request.json
    api_type = data.get('api_type')
    api_key = data.get('api_key', '').strip()
    
    if not api_type or not api_key:
        return jsonify({
            'success': False,
            'message': 'API type and key are required.'
        }), 400
    
    # Test key based on type
    if api_type.lower() == 'gpt':
        # Test OpenAI key
        from openai import OpenAI
        import httpx
        
        try:
            client = OpenAI(api_key=api_key)
            # Make a simple request to test the key
            response = client.models.list()
            return jsonify({
                'success': True,
                'message': 'OpenAI API key is valid and working! You can now use GPT-4o-mini for content generation.'
            })
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'Invalid OpenAI API key. Please check your key and try again.'
                })
            else:
                logger.error(f"Error testing OpenAI API key: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f"API Error: {str(e)}"
                }), 500
        except Exception as e:
            logger.error(f"Error testing OpenAI API key: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error: {str(e)}"
            }), 500
    
    elif api_type.lower() == 'claude':
        # Test Anthropic key
        import anthropic
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # Make a simple request to test the key validity
            models = client.models.list()
            return jsonify({
                'success': True,
                'message': 'Claude API key is valid and working! You can now use Claude 3 Opus for content generation.'
            })
        except anthropic.AuthenticationError:
            return jsonify({
                'success': False,
                'message': 'Invalid Anthropic API key. Please check your key and try again.'
            })
        except Exception as e:
            logger.error(f"Error testing Claude API key: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error: {str(e)}"
            }), 500
    
    elif api_type.lower() == 'unsplash':
        # Test Unsplash key
        import requests
        
        try:
            response = requests.get(
                'https://api.unsplash.com/users/unsplash',
                headers={'Authorization': f'Client-ID {api_key}'}
            )
            
            if response.status_code == 200:
                return jsonify({
                    'success': True,
                    'message': 'Unsplash API key is valid.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Invalid Unsplash API key. Status code: {response.status_code}'
                })
        except Exception as e:
            logger.error(f"Error testing Unsplash API key: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Error: {str(e)}"
            }), 500
    
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid API type.'
        }), 400
