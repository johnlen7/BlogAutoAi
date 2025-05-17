import logging
from datetime import datetime, timedelta
from typing import List, Optional

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger

from app import db
from models import Article, ArticleStatus, SchedulerLog, LogType, RepeatSchedule, WordPressConfig
from services.wordpress_service import WordPressService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def init_scheduler(app: Flask) -> None:
    """
    Initialize the APScheduler for article publishing
    
    Args:
        app: Flask application
    """
    global scheduler
    
    logger.info("Initializing scheduler service")
    
    # Create a scheduler without persistent jobstore to avoid pickle issues
    # We'll manually manage the scheduling in the database
    scheduler = BackgroundScheduler()
    
    # Add jobs with in-memory storage
    scheduler.add_job(
        func=check_scheduled_articles,
        trigger=IntervalTrigger(minutes=15),  # Check every 15 minutes
        id='check_scheduled_articles',
        name='Check for scheduled articles to publish',
        replace_existing=True
    )
    
    # Add a job to run the status cleanup task daily
    scheduler.add_job(
        func=cleanup_task,
        trigger='cron',
        hour=0,  # Run at midnight
        minute=0,
        id='cleanup_task',
        name='Clean up old scheduled articles and logs',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    
    # Register shutdown handler
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if scheduler and scheduler.running:
            scheduler.shutdown()

def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the global scheduler instance"""
    return scheduler

def check_scheduled_articles() -> None:
    """
    Check for articles scheduled to be published and publish them
    This function is called by the scheduler
    """
    logger.info("Checking for scheduled articles")
    
    # Log the scheduler run
    log = SchedulerLog(
        message="Checking for scheduled articles to publish",
        log_type=LogType.INFO
    )
    db.session.add(log)
    db.session.commit()
    
    try:
        # Get all articles scheduled for publishing
        current_time = datetime.utcnow()
        
        # Find articles scheduled before now
        scheduled_articles = Article.query.filter(
            Article.status == ArticleStatus.SCHEDULED,
            Article.scheduled_date <= current_time
        ).all()
        
        if not scheduled_articles:
            logger.info("No articles scheduled for publication")
            return
        
        logger.info(f"Found {len(scheduled_articles)} articles to publish")
        
        # Process each article
        for article in scheduled_articles:
            publish_scheduled_article(article)
            
        # Commit all changes
        db.session.commit()
        
        # Success log
        log = SchedulerLog(
            message=f"Successfully processed {len(scheduled_articles)} scheduled articles",
            log_type=LogType.SUCCESS
        )
        db.session.add(log)
        db.session.commit()
        
    except Exception as e:
        error_message = f"Error in scheduler check_scheduled_articles: {str(e)}"
        logger.error(error_message)
        
        # Log the error
        log = SchedulerLog(
            message=error_message,
            log_type=LogType.ERROR
        )
        db.session.add(log)
        db.session.commit()

def publish_scheduled_article(article: Article) -> None:
    """
    Publish a scheduled article
    
    Args:
        article: The article to publish
    """
    logger.info(f"Publishing scheduled article: {article.title}")
    
    try:
        # Get WordPress config
        wp_config = WordPressConfig.query.get(article.wordpress_config_id)
        if not wp_config:
            error_msg = f"WordPress configuration not found for article ID: {article.id}"
            logger.error(error_msg)
            
            # Update article status
            article.status = ArticleStatus.FAILED
            article.publish_attempt_count += 1
            article.last_attempt_date = datetime.utcnow()
            
            # Add log entry
            log = SchedulerLog(
                message=error_msg,
                log_type=LogType.ERROR
            )
            db.session.add(log)
            return
        
        # Initialize WordPress service
        wp_service = WordPressService(wp_config)
        
        # Publish the article
        success = wp_service.publish_article(article)
        
        if success:
            logger.info(f"Successfully published article: {article.title}")
            
            # Handle repeat schedule if needed
            reschedule_article(article)
        else:
            logger.warning(f"Failed to publish article: {article.title}")
            
    except Exception as e:
        error_msg = f"Error publishing article {article.id}: {str(e)}"
        logger.error(error_msg)
        
        # Update article status
        article.status = ArticleStatus.FAILED
        article.publish_attempt_count += 1
        article.last_attempt_date = datetime.utcnow()
        
        # Add log entry
        log = SchedulerLog(
            message=error_msg,
            log_type=LogType.ERROR
        )
        db.session.add(log)

def reschedule_article(article: Article) -> None:
    """
    Handle article rescheduling for recurring content
    
    Args:
        article: The article to potentially reschedule
    """
    if article.repeat_schedule == RepeatSchedule.NONE:
        return
    
    logger.info(f"Processing repeat schedule: {article.repeat_schedule.value} for article: {article.title}")
    
    # Calculate next publication date
    next_date = None
    original_date = article.scheduled_date
    
    if article.repeat_schedule == RepeatSchedule.DAILY:
        next_date = original_date + timedelta(days=1)
    elif article.repeat_schedule == RepeatSchedule.WEEKLY:
        next_date = original_date + timedelta(weeks=1)
    elif article.repeat_schedule == RepeatSchedule.MONTHLY:
        # Calculate next month (approximation of 30 days)
        next_date = original_date + timedelta(days=30)
    
    if next_date:
        # Create a new article copy
        new_article = Article(
            title=article.title,
            content=article.content,
            meta_description=article.meta_description,
            slug=article.slug,
            tags=article.tags,
            categories=article.categories,
            featured_image_url=article.featured_image_url,
            status=ArticleStatus.SCHEDULED,
            ai_model=article.ai_model,
            keyword=article.keyword,
            source_url=article.source_url,
            repeat_schedule=article.repeat_schedule,
            scheduled_date=next_date,
            user_id=article.user_id,
            wordpress_config_id=article.wordpress_config_id
        )
        
        db.session.add(new_article)
        logger.info(f"Rescheduled article: {article.title} for {next_date}")
        
        # Add log entry
        log = SchedulerLog(
            message=f"Auto-rescheduled article {article.id} for {next_date}",
            log_type=LogType.INFO
        )
        db.session.add(log)

def cleanup_task() -> None:
    """
    Cleanup task to remove old data or perform maintenance
    This function is called by the scheduler daily
    """
    logger.info("Running daily cleanup task")
    
    try:
        # Remove old scheduler logs (older than 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        SchedulerLog.query.filter(SchedulerLog.created_at < thirty_days_ago).delete()
        
        # Log cleanup
        log = SchedulerLog(
            message="Performed daily cleanup of old scheduler logs",
            log_type=LogType.INFO
        )
        db.session.add(log)
        db.session.commit()
        
    except Exception as e:
        error_msg = f"Error in cleanup task: {str(e)}"
        logger.error(error_msg)
        
        # Log the error
        log = SchedulerLog(
            message=error_msg,
            log_type=LogType.ERROR
        )
        db.session.add(log)
        db.session.commit()

def get_scheduler_status() -> dict:
    """
    Get the current status of the scheduler
    
    Returns:
        Dictionary with scheduler status information
    """
    if not scheduler:
        return {
            "status": "not_running",
            "jobs": 0,
            "next_run": None
        }
    
    # Get job info
    jobs = scheduler.get_jobs()
    
    # Find the next scheduled run
    next_run = None
    for job in jobs:
        next_job_run = job.next_run_time
        if next_job_run:
            if not next_run or next_job_run < next_run:
                next_run = next_job_run
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": len(jobs),
        "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None
    }
