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
    
    repeat_schedule = db.Column(db.Enum(RepeatSchedule), default=RepeatSchedule.NONE)
    scheduled_date = db.Column(db.DateTime)
    publish_attempt_count = db.Column(db.Integer, default=0)
    last_attempt_date = db.Column(db.DateTime)
    wordpress_post_id = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    wordpress_config_id = db.Column(db.Integer, db.ForeignKey('word_press_config.id'))
    
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
