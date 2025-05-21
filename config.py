import os

# Application configuration
class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_secret_key')
    
    # Database configuration
    # Configuração para MySQL/MariaDB
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'blogauto')
    
    # Prioridade para DATABASE_URL se existir, caso contrário cria a URL MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
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
