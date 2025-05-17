import enum
from datetime import datetime
from app import db
from flask_login import UserMixin

# Classes de enumeração
class ContentSource(enum.Enum):
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
    
    # Relacionamentos
    rss_feeds = db.relationship('RSSFeed', backref='theme', lazy=True)
    articles = db.relationship('Article', backref='theme', lazy=True)
    
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
    
    # Relacionamentos
    news_items = db.relationship('NewsItem', backref='rss_feed', lazy=True)
    
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
    
    # Relacionamento com artigos gerados a partir desta notícia
    articles = db.relationship('Article', backref='news_source', lazy=True, foreign_keys='Article.news_item_id')
    
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
    
    # Relação com a configuração WordPress
    wordpress_config = db.relationship('WordPressConfig')
    
    def __repr__(self):
        return f'<AutomationSettings user_id={self.user_id}>'