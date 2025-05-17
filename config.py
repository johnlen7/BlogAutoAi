import os

# Application configuration
class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_secret_key')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///blogauto.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # APScheduler configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }
    
    # API defaults
    DEFAULT_CLAUDE_MODEL = "claude-3-opus-20240229"  # Using Claude 3 Opus (versão disponível na API)
    DEFAULT_GPT_MODEL = "gpt-4o-mini"  # Using GPT-4o-mini as requested
    
    # Unsplash API
    UNSPLASH_API_URL = "https://api.unsplash.com"
    
    # WordPress defaults
    WP_API_ENDPOINT = "/wp-json/wp/v2"
    
    # Scheduler check interval (in seconds)
    DEFAULT_SCHEDULER_INTERVAL = 900  # 15 minutes
    
    # Application defaults
    DEFAULT_ARTICLE_META_LENGTH = 155
    DEFAULT_ARTICLE_TAGS_COUNT = 5
