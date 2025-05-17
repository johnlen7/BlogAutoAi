import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from models import Article, ArticleStatus, ArticleLog
from services.scheduler_service import get_scheduler_status

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page with article statistics and status"""
    # Get article counts by status
    article_stats = db.session.query(
        ArticleStatus,
        func.count(Article.id)
    ).filter(
        Article.user_id == current_user.id
    ).group_by(
        ArticleStatus
    ).all()
    
    # Format statistics for template
    stats = {
        'total': 0,
        'draft': 0,
        'scheduled': 0,
        'published': 0,
        'failed': 0
    }
    
    for status, count in article_stats:
        stats[status.value] = count
        stats['total'] += count
    
    # Get recent articles (limit to 10)
    recent_articles = Article.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Article.updated_at.desc()
    ).limit(10).all()
    
    # Get scheduled articles
    scheduled_articles = Article.query.filter_by(
        user_id=current_user.id,
        status=ArticleStatus.SCHEDULED
    ).order_by(
        Article.scheduled_date.asc()
    ).limit(5).all()
    
    # Get scheduler status
    scheduler_status = get_scheduler_status()
    
    return render_template(
        'dashboard.html',
        stats=stats,
        recent_articles=recent_articles,
        scheduled_articles=scheduled_articles,
        scheduler_status=scheduler_status
    )

@dashboard_bp.route('/articles')
@login_required
def article_list():
    """Page showing the list of all articles with filtering options"""
    # Get filter parameters
    status = request.args.get('status')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'updated_desc')
    
    # Base query
    query = Article.query.filter_by(user_id=current_user.id)
    
    # Apply status filter if provided
    if status and hasattr(ArticleStatus, status.upper()):
        query = query.filter_by(status=getattr(ArticleStatus, status.upper()))
    
    # Apply search filter if provided
    if search:
        query = query.filter(Article.title.ilike(f'%{search}%'))
    
    # Apply sorting
    if sort == 'title_asc':
        query = query.order_by(Article.title.asc())
    elif sort == 'title_desc':
        query = query.order_by(Article.title.desc())
    elif sort == 'created_asc':
        query = query.order_by(Article.created_at.asc())
    elif sort == 'created_desc':
        query = query.order_by(Article.created_at.desc())
    elif sort == 'scheduled_asc':
        query = query.order_by(Article.scheduled_date.asc())
    elif sort == 'scheduled_desc':
        query = query.order_by(Article.scheduled_date.desc())
    else:  # default: updated_desc
        query = query.order_by(Article.updated_at.desc())
    
    # Execute query
    articles = query.all()
    
    return render_template(
        'article_list.html',
        articles=articles,
        status=status,
        search=search,
        sort=sort
    )

@dashboard_bp.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    """View details of a specific article"""
    article = Article.query.get_or_404(article_id)
    
    # Check if article belongs to current user
    if article.user_id != current_user.id:
        flash('Access denied: This article does not belong to you.', 'danger')
        return redirect(url_for('dashboard.article_list'))
    
    # Get article logs
    logs = ArticleLog.query.filter_by(
        article_id=article.id
    ).order_by(
        ArticleLog.created_at.desc()
    ).all()
    
    return render_template(
        'article_detail.html',
        article=article,
        logs=logs
    )

@dashboard_bp.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """Delete an article"""
    article = Article.query.get_or_404(article_id)
    
    # Check if article belongs to current user
    if article.user_id != current_user.id:
        flash('Access denied: This article does not belong to you.', 'danger')
        return redirect(url_for('dashboard.article_list'))
    
    # Delete logs first (foreign key constraint)
    ArticleLog.query.filter_by(article_id=article.id).delete()
    
    # Delete article
    db.session.delete(article)
    db.session.commit()
    
    flash(f'Article "{article.title}" deleted successfully!', 'success')
    return redirect(url_for('dashboard.article_list'))

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """API endpoint to get dashboard statistics (for AJAX updates)"""
    # Get article counts by status
    article_stats = db.session.query(
        ArticleStatus,
        func.count(Article.id)
    ).filter(
        Article.user_id == current_user.id
    ).group_by(
        ArticleStatus
    ).all()
    
    # Format statistics for response
    stats = {
        'total': 0,
        'draft': 0,
        'scheduled': 0,
        'published': 0,
        'failed': 0
    }
    
    for status, count in article_stats:
        stats[status.value] = count
        stats['total'] += count
    
    # Get scheduler status
    scheduler_status = get_scheduler_status()
    
    return jsonify({
        'stats': stats,
        'scheduler': scheduler_status
    })
