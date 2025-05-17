import enum
from datetime import datetime
from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relationships
    wordpress_configs = db.relationship('WordPressConfig', backref='user', lazy=True)
    api_keys = db.relationship('APIKey', backref='user', lazy=True)
    articles = db.relationship('Article', backref='author', lazy=True)
    
    # Novos relacionamentos para automação
    automation_themes = db.relationship('AutomationTheme', backref='user', lazy=True)
    rss_feeds = db.relationship('RSSFeed', backref='user', lazy=True)
    news_items = db.relationship('NewsItem', backref='user', lazy=True)
    automation_settings = db.relationship('AutomationSettings', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class WordPressConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    site_url = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    app_password = db.Column(db.String(256), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<WordPressConfig {self.name}>'


class APIType(enum.Enum):
    CLAUDE = "claude"
    GPT = "gpt"
    UNSPLASH = "unsplash"


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(APIType), nullable=False)
    key = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<APIKey {self.type.value}>'


class ArticleStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class AIModel(enum.Enum):
    CLAUDE = "claude"
    GPT = "gpt"


class RepeatSchedule(enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    meta_description = db.Column(db.String(320))
    slug = db.Column(db.String(256))
    tags = db.Column(db.String(256))
    categories = db.Column(db.String(256))
    featured_image_url = db.Column(db.String(512))
    
    status = db.Column(db.Enum(ArticleStatus), default=ArticleStatus.DRAFT)
    ai_model = db.Column(db.Enum(AIModel))
    keyword = db.Column(db.String(128))
    source_url = db.Column(db.String(512))
    # Campo para indicar qual a fonte do conteúdo (keyword, url, rss)
    source_type = db.Column(db.String(20), default="keyword")
    repeat_schedule = db.Column(db.Enum(RepeatSchedule), default=RepeatSchedule.NONE)
    scheduled_date = db.Column(db.DateTime)
    publish_attempt_count = db.Column(db.Integer, default=0)
    last_attempt_date = db.Column(db.DateTime)
    wordpress_post_id = db.Column(db.Integer)
    
    is_automated = db.Column(db.Boolean, default=False)  # Flag para artigos gerados automaticamente
    word_count = db.Column(db.Integer)  # Contagem de palavras do artigo
    
    # Relações para automação
    theme_id = db.Column(db.Integer, db.ForeignKey('automation_theme.id'), nullable=True)
    news_item_id = db.Column(db.Integer, db.ForeignKey('news_item.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    wordpress_config_id = db.Column(db.Integer, db.ForeignKey('word_press_config.id'))
    theme_id = db.Column(db.Integer, db.ForeignKey('automation_theme.id'), nullable=True)
    news_item_id = db.Column(db.Integer, db.ForeignKey('news_item.id'), nullable=True)
    
    # Relationship to the WordPress config
    wordpress_config = db.relationship('WordPressConfig')
    
    # Relationship with article logs
    logs = db.relationship('ArticleLog', backref='article', lazy=True)
    
    def __repr__(self):
        return f'<Article {self.title}>'


class LogType(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class ArticleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    log_type = db.Column(db.Enum(LogType), default=LogType.INFO)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    
    def __repr__(self):
        return f'<ArticleLog {self.log_type.value}: {self.message[:30]}>'


class SchedulerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    log_type = db.Column(db.Enum(LogType), default=LogType.INFO)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SchedulerLog {self.log_type.value}: {self.message[:30]}>'


# Classes de automação diretamente neste arquivo para evitar dependências circulares

class ContentSourceType(enum.Enum):
    KEYWORD = "keyword"
    RSS = "rss" 
    URL = "url"

class AutomationTheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    keywords = db.Column(db.Text, nullable=False)  # Armazena palavras-chave separadas por vírgula
    priority = db.Column(db.Integer, default=0)  # Quanto maior, maior a prioridade
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<AutomationTheme {self.name}>'


class RSSFeed(db.Model):
    __tablename__ = 'rss_feed'  # Define explicitamente o nome da tabela
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    last_fetch = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    theme_id = db.Column(db.Integer, db.ForeignKey('automation_theme.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<RSSFeed {self.name}>'


class NewsItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    link = db.Column(db.String(512), nullable=False)
    guid = db.Column(db.String(512), nullable=False, unique=True)
    published_date = db.Column(db.DateTime)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rss_feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<NewsItem {self.title}>'


class AutomationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_interval_hours = db.Column(db.Integer, default=6)  # Intervalo em horas entre postagens
    min_word_count = db.Column(db.Integer, default=700)
    max_word_count = db.Column(db.Integer, default=1500)
    timezone_offset = db.Column(db.Integer, default=-3)  # Padrão: UTC-3 (Brasília)
    active_hours_start = db.Column(db.Integer, default=8)  # Horário de início (ex: 8 = 8h da manhã)
    active_hours_end = db.Column(db.Integer, default=22)  # Horário de término (ex: 22 = 22h/10h da noite)
    is_active = db.Column(db.Boolean, default=True)
    next_scheduled_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    wordpress_config_id = db.Column(db.Integer, db.ForeignKey('word_press_config.id'))
    
    def __repr__(self):
        return f'<AutomationSettings user_id={self.user_id}>'
