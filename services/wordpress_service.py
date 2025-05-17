import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64

from models import Article, ArticleStatus, LogType, ArticleLog, WordPressConfig
from app import db

logger = logging.getLogger(__name__)

class WordPressService:
    """Service to interact with WordPress REST API"""
    
    def __init__(self, wp_config: WordPressConfig):
        """
        Initialize WordPress service with configuration
        
        Args:
            wp_config: WordPress configuration object
        """
        self.wp_config = wp_config
        self.site_url = wp_config.site_url.rstrip('/')
        self.api_endpoint = f"{self.site_url}/wp-json/wp/v2"
        self.username = wp_config.username
        self.app_password = wp_config.app_password
        
        # Auth header for WordPress API
        credentials = f"{self.username}:{self.app_password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        self.auth_header = {'Authorization': f'Basic {encoded_credentials}'}
    
    def validate_connection(self) -> bool:
        """
        Test connection to WordPress site with provided credentials
        
        Returns:
            Boolean indicating if connection is successful
        """
        logger.info(f"Validating WordPress connection to {self.site_url}")
        
        try:
            # Try to get user info - requires authentication
            response = requests.get(
                f"{self.api_endpoint}/users/me",
                headers=self.auth_header,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("WordPress connection successful")
                return True
            else:
                logger.warning(f"WordPress connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"WordPress connection error: {str(e)}")
            return False
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get list of available categories from WordPress"""
        logger.info(f"Fetching categories from {self.site_url}")
        
        try:
            response = requests.get(
                f"{self.api_endpoint}/categories",
                headers=self.auth_header,
                params={"per_page": 100},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch categories: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Get list of available tags from WordPress"""
        logger.info(f"Fetching tags from {self.site_url}")
        
        try:
            response = requests.get(
                f"{self.api_endpoint}/tags",
                headers=self.auth_header,
                params={"per_page": 100},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch tags: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching tags: {str(e)}")
            return []
    
    def create_or_get_tags(self, tag_names: List[str]) -> List[int]:
        """
        Create tags if they don't exist or get IDs if they do
        
        Args:
            tag_names: List of tag names to create or get
            
        Returns:
            List of tag IDs
        """
        logger.info(f"Creating or getting tags: {tag_names}")
        
        tag_ids = []
        
        # Get existing tags
        existing_tags = self.get_tags()
        existing_tag_map = {tag['name'].lower(): tag['id'] for tag in existing_tags}
        
        for tag_name in tag_names:
            # Check if tag already exists
            if tag_name.lower() in existing_tag_map:
                tag_ids.append(existing_tag_map[tag_name.lower()])
                continue
            
            # Create new tag
            try:
                response = requests.post(
                    f"{self.api_endpoint}/tags",
                    headers=self.auth_header,
                    json={"name": tag_name},
                    timeout=10
                )
                
                if response.status_code in (200, 201):
                    tag_data = response.json()
                    tag_ids.append(tag_data['id'])
                    logger.info(f"Created tag: {tag_name} with ID: {tag_data['id']}")
                else:
                    logger.warning(f"Failed to create tag {tag_name}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error creating tag {tag_name}: {str(e)}")
        
        return tag_ids
    
    def create_or_get_categories(self, category_names: List[str]) -> List[int]:
        """
        Create categories if they don't exist or get IDs if they do
        
        Args:
            category_names: List of category names to create or get
            
        Returns:
            List of category IDs
        """
        logger.info(f"Creating or getting categories: {category_names}")
        
        category_ids = []
        
        # Get existing categories
        existing_categories = self.get_categories()
        existing_category_map = {cat['name'].lower(): cat['id'] for cat in existing_categories}
        
        for category_name in category_names:
            # Check if category already exists
            if category_name.lower() in existing_category_map:
                category_ids.append(existing_category_map[category_name.lower()])
                continue
            
            # Create new category
            try:
                response = requests.post(
                    f"{self.api_endpoint}/categories",
                    headers=self.auth_header,
                    json={"name": category_name},
                    timeout=10
                )
                
                if response.status_code in (200, 201):
                    category_data = response.json()
                    category_ids.append(category_data['id'])
                    logger.info(f"Created category: {category_name} with ID: {category_data['id']}")
                else:
                    logger.warning(f"Failed to create category {category_name}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {str(e)}")
        
        return category_ids
    
    def upload_featured_image(self, image_url: str) -> Optional[int]:
        """
        Upload an image from URL to WordPress media library
        
        Args:
            image_url: URL of the image to upload
            
        Returns:
            Media ID if successful, None otherwise
        """
        logger.info(f"Uploading featured image from URL: {image_url}")
        
        if not image_url:
            return None
        
        try:
            # Download the image
            image_response = requests.get(image_url, timeout=10)
            if image_response.status_code != 200:
                logger.warning(f"Failed to download image: {image_response.status_code}")
                return None
            
            # Get filename from URL
            import urllib.parse
            import os
            parsed_url = urllib.parse.urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                filename = "featured-image.jpg"
            
            # Upload to WordPress
            upload_headers = self.auth_header.copy()
            upload_headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            response = requests.post(
                f"{self.api_endpoint}/media",
                headers=upload_headers,
                data=image_response.content,
                timeout=30
            )
            
            if response.status_code in (200, 201):
                media_data = response.json()
                logger.info(f"Uploaded image with ID: {media_data['id']}")
                return media_data['id']
            else:
                logger.warning(f"Failed to upload image: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None
    
    def create_post(self, article: Article) -> Optional[int]:
        """
        Create a new post in WordPress
        
        Args:
            article: Article object to publish
            
        Returns:
            WordPress post ID if successful, None otherwise
        """
        logger.info(f"Creating post: {article.title}")
        
        try:
            # Process tags and categories
            tag_names = [tag.strip() for tag in article.tags.split(',')] if article.tags else []
            category_names = [cat.strip() for cat in article.categories.split(',')] if article.categories else []
            
            tag_ids = self.create_or_get_tags(tag_names)
            category_ids = self.create_or_get_categories(category_names)
            
            # Upload featured image if available
            featured_media_id = None
            if article.featured_image_url:
                featured_media_id = self.upload_featured_image(article.featured_image_url)
            
            # Prepare post data
            post_data = {
                "title": article.title,
                "content": article.content,
                "status": "publish",  # or draft, pending, private
                "slug": article.slug,
                "excerpt": article.meta_description,
                "tags": tag_ids,
                "categories": category_ids
            }
            
            if featured_media_id:
                post_data["featured_media"] = featured_media_id
            
            # Create the post
            response = requests.post(
                f"{self.api_endpoint}/posts",
                headers=self.auth_header,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in (200, 201):
                post_data = response.json()
                post_id = post_data['id']
                
                # Log success
                log = ArticleLog(
                    article_id=article.id,
                    message=f"Successfully published to WordPress with post ID: {post_id}",
                    log_type=LogType.SUCCESS
                )
                db.session.add(log)
                
                logger.info(f"Created post with ID: {post_id}")
                return post_id
            else:
                error_msg = f"Failed to create post: {response.status_code}"
                if response.content:
                    error_msg += f" - {response.content.decode('utf-8')}"
                
                # Log error
                log = ArticleLog(
                    article_id=article.id,
                    message=error_msg,
                    log_type=LogType.ERROR
                )
                db.session.add(log)
                
                logger.warning(error_msg)
                return None
        except Exception as e:
            error_msg = f"Error creating post: {str(e)}"
            
            # Log error
            log = ArticleLog(
                article_id=article.id,
                message=error_msg,
                log_type=LogType.ERROR
            )
            db.session.add(log)
            
            logger.error(error_msg)
            return None
    
    def schedule_post(self, article: Article) -> Optional[int]:
        """
        Schedule a post in WordPress for future publishing
        
        Args:
            article: Article object with scheduled_date set
            
        Returns:
            WordPress post ID if successful, None otherwise
        """
        logger.info(f"Scheduling post: {article.title} for {article.scheduled_date}")
        
        if not article.scheduled_date:
            error_msg = "Cannot schedule post without a scheduled date"
            log = ArticleLog(
                article_id=article.id,
                message=error_msg,
                log_type=LogType.ERROR
            )
            db.session.add(log)
            logger.warning(error_msg)
            return None
        
        try:
            # Process tags and categories
            tag_names = [tag.strip() for tag in article.tags.split(',')] if article.tags else []
            category_names = [cat.strip() for cat in article.categories.split(',')] if article.categories else []
            
            tag_ids = self.create_or_get_tags(tag_names)
            category_ids = self.create_or_get_categories(category_names)
            
            # Upload featured image if available
            featured_media_id = None
            if article.featured_image_url:
                featured_media_id = self.upload_featured_image(article.featured_image_url)
            
            # Format date for WordPress (ISO 8601)
            date_str = article.scheduled_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Prepare post data
            post_data = {
                "title": article.title,
                "content": article.content,
                "status": "future",
                "date": date_str,
                "slug": article.slug,
                "excerpt": article.meta_description,
                "tags": tag_ids,
                "categories": category_ids
            }
            
            if featured_media_id:
                post_data["featured_media"] = featured_media_id
            
            # Create the scheduled post
            response = requests.post(
                f"{self.api_endpoint}/posts",
                headers=self.auth_header,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in (200, 201):
                post_data = response.json()
                post_id = post_data['id']
                
                # Log success
                log = ArticleLog(
                    article_id=article.id,
                    message=f"Successfully scheduled post for {date_str} with post ID: {post_id}",
                    log_type=LogType.SUCCESS
                )
                db.session.add(log)
                
                logger.info(f"Scheduled post with ID: {post_id} for {date_str}")
                return post_id
            else:
                error_msg = f"Failed to schedule post: {response.status_code}"
                if response.content:
                    error_msg += f" - {response.content.decode('utf-8')}"
                
                # Log error
                log = ArticleLog(
                    article_id=article.id,
                    message=error_msg,
                    log_type=LogType.ERROR
                )
                db.session.add(log)
                
                logger.warning(error_msg)
                return None
        except Exception as e:
            error_msg = f"Error scheduling post: {str(e)}"
            
            # Log error
            log = ArticleLog(
                article_id=article.id,
                message=error_msg,
                log_type=LogType.ERROR
            )
            db.session.add(log)
            
            logger.error(error_msg)
            return None
    
    def update_post(self, post_id: int, article: Article) -> bool:
        """
        Update an existing WordPress post
        
        Args:
            post_id: WordPress post ID to update
            article: Article object with updated content
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"Updating post ID: {post_id}")
        
        try:
            # Process tags and categories
            tag_names = [tag.strip() for tag in article.tags.split(',')] if article.tags else []
            category_names = [cat.strip() for cat in article.categories.split(',')] if article.categories else []
            
            tag_ids = self.create_or_get_tags(tag_names)
            category_ids = self.create_or_get_categories(category_names)
            
            # Prepare post data
            post_data = {
                "title": article.title,
                "content": article.content,
                "slug": article.slug,
                "excerpt": article.meta_description,
                "tags": tag_ids,
                "categories": category_ids
            }
            
            # Update featured image if changed
            if article.featured_image_url:
                featured_media_id = self.upload_featured_image(article.featured_image_url)
                if featured_media_id:
                    post_data["featured_media"] = featured_media_id
            
            # Update the post
            response = requests.put(
                f"{self.api_endpoint}/posts/{post_id}",
                headers=self.auth_header,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in (200, 201):
                # Log success
                log = ArticleLog(
                    article_id=article.id,
                    message=f"Successfully updated WordPress post ID: {post_id}",
                    log_type=LogType.SUCCESS
                )
                db.session.add(log)
                
                logger.info(f"Updated post ID: {post_id}")
                return True
            else:
                error_msg = f"Failed to update post: {response.status_code}"
                if response.content:
                    error_msg += f" - {response.content.decode('utf-8')}"
                
                # Log error
                log = ArticleLog(
                    article_id=article.id,
                    message=error_msg,
                    log_type=LogType.ERROR
                )
                db.session.add(log)
                
                logger.warning(error_msg)
                return False
        except Exception as e:
            error_msg = f"Error updating post: {str(e)}"
            
            # Log error
            log = ArticleLog(
                article_id=article.id,
                message=error_msg,
                log_type=LogType.ERROR
            )
            db.session.add(log)
            
            logger.error(error_msg)
            return False
    
    def delete_post(self, post_id: int) -> bool:
        """
        Delete a WordPress post
        
        Args:
            post_id: WordPress post ID to delete
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"Deleting post ID: {post_id}")
        
        try:
            response = requests.delete(
                f"{self.api_endpoint}/posts/{post_id}",
                headers=self.auth_header,
                params={"force": True},  # Permanently delete
                timeout=10
            )
            
            if response.status_code in (200, 201, 204):
                logger.info(f"Deleted post ID: {post_id}")
                return True
            else:
                logger.warning(f"Failed to delete post: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error deleting post: {str(e)}")
            return False
    
    def publish_article(self, article: Article) -> bool:
        """
        Publish an article to WordPress
        
        Args:
            article: Article object to publish
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"Publishing article: {article.title}")
        
        # Update attempt counters
        article.publish_attempt_count += 1
        article.last_attempt_date = datetime.utcnow()
        
        # Check if article is already published
        if article.wordpress_post_id:
            # Update existing post
            result = self.update_post(article.wordpress_post_id, article)
            if result:
                article.status = ArticleStatus.PUBLISHED
            else:
                article.status = ArticleStatus.FAILED
            db.session.commit()
            return result
            
        # Create new post
        post_id = self.create_post(article)
        if post_id:
            article.wordpress_post_id = post_id
            article.status = ArticleStatus.PUBLISHED
            db.session.commit()
            return True
        else:
            article.status = ArticleStatus.FAILED
            db.session.commit()
            return False
