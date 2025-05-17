import os
import logging
import requests
import json
from typing import Dict, Any, Optional, List, Tuple

import anthropic
from openai import OpenAI

from models import AIModel
from config import Config

logger = logging.getLogger(__name__)

class AIService:
    """Service to interact with AI models for content generation"""
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize AI service with API keys
        
        Args:
            api_keys: Dictionary with model names as keys and API keys as values
        """
        self.api_keys = api_keys
        self._anthropic_client = None
        self._openai_client = None
    
    @property
    def anthropic_client(self):
        """Lazy loading of Anthropic client"""
        if not self._anthropic_client and self.api_keys.get(AIModel.CLAUDE.value):
            self._anthropic_client = anthropic.Anthropic(
                api_key=self.api_keys[AIModel.CLAUDE.value]
            )
        return self._anthropic_client
    
    @property
    def openai_client(self):
        """Lazy loading of OpenAI client"""
        if not self._openai_client and self.api_keys.get(AIModel.GPT.value):
            self._openai_client = OpenAI(
                api_key=self.api_keys[AIModel.GPT.value]
            )
        return self._openai_client
    
    def generate_article_from_keyword(
        self, 
        keyword: str, 
        model_type: AIModel,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete article based on a keyword
        
        Args:
            keyword: The primary keyword for the article
            model_type: Which AI model to use (CLAUDE or GPT)
            title: Optional title to use (if None, will be generated)
            
        Returns:
            Dictionary containing article components (title, content, meta, tags, etc.)
        """
        logger.info(f"Generating article for keyword: {keyword} using {model_type.value}")
        
        # Generate title if not provided
        if not title:
            title = self.generate_title(keyword, model_type)
        
        # Generate the complete article
        article_content = self._generate_article_content(keyword, title, model_type)
        
        # Generate metadata
        meta_description = self.generate_meta_description(title, article_content, model_type)
        tags = self.generate_tags(keyword, article_content, model_type)
        slug = self.generate_slug(title)
        
        # Return full article package
        return {
            "title": title,
            "content": article_content,
            "meta_description": meta_description,
            "tags": tags,
            "slug": slug
        }
    
    def generate_article_from_url(
        self,
        url: str,
        model_type: AIModel,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an article based on the content from a URL
        
        Args:
            url: URL to extract information from
            model_type: Which AI model to use (CLAUDE or GPT)
            title: Optional title to use (if None, will be generated)
            
        Returns:
            Dictionary containing article components
        """
        logger.info(f"Generating article from URL: {url} using {model_type.value}")
        
        # Get topic and key points from the URL
        topic, key_points = self._extract_info_from_url(url, model_type)
        
        # Generate title if not provided
        if not title:
            title = self.generate_title(topic, model_type)
        
        # Generate article content
        article_content = self._generate_article_from_key_points(
            topic, key_points, title, model_type
        )
        
        # Generate metadata
        meta_description = self.generate_meta_description(title, article_content, model_type)
        tags = self.generate_tags(topic, article_content, model_type)
        slug = self.generate_slug(title)
        
        return {
            "title": title,
            "content": article_content,
            "meta_description": meta_description,
            "tags": tags,
            "slug": slug
        }
    
    def generate_title(self, keyword: str, model_type: AIModel) -> str:
        """Generate an SEO-optimized title based on keyword"""
        logger.info(f"Generating title for keyword: {keyword}")
        
        prompt = (
            f"Create an SEO-optimized, attention-grabbing blog post title for an article about '{keyword}'. "
            f"The title should be engaging, include the keyword, and be under 60 characters if possible. "
            f"Return only the title text with no quotes or additional commentary."
        )
        
        if model_type == AIModel.CLAUDE:
            return self._query_claude(prompt, max_tokens=50)
        else:
            return self._query_gpt(prompt, max_tokens=50)
    
    def generate_meta_description(self, title: str, content: str, model_type: AIModel) -> str:
        """Generate SEO meta description from article content"""
        logger.info(f"Generating meta description for: {title}")
        
        # Extract first part of content to reduce token usage
        content_sample = content[:3000] if len(content) > 3000 else content
        
        prompt = (
            f"Create an SEO-optimized meta description for a blog post titled '{title}'. "
            f"The content of the article is about: {content_sample}\n\n"
            f"The meta description should be compelling, include key information, and be between "
            f"120-155 characters. Return only the meta description text."
        )
        
        if model_type == AIModel.CLAUDE:
            return self._query_claude(prompt, max_tokens=200)
        else:
            return self._query_gpt(prompt, max_tokens=200)
    
    def generate_tags(self, keyword: str, content: str, model_type: AIModel) -> List[str]:
        """Generate relevant tags for the article"""
        logger.info(f"Generating tags for keyword: {keyword}")
        
        # Extract part of content to reduce token usage
        content_sample = content[:2000] if len(content) > 2000 else content
        
        prompt = (
            f"Generate 5-7 relevant tags for a WordPress blog post about '{keyword}' "
            f"with the following content: {content_sample}\n\n"
            f"Return the tags as a comma-separated list with no additional text. "
            f"Each tag should be 1-3 words and relevant to the content."
        )
        
        if model_type == AIModel.CLAUDE:
            tags_text = self._query_claude(prompt, max_tokens=200)
        else:
            tags_text = self._query_gpt(prompt, max_tokens=200)
        
        # Process the tags
        tags = [tag.strip() for tag in tags_text.split(',')]
        return tags
    
    def generate_slug(self, title: str) -> str:
        """Generate a URL slug from an article title"""
        # Convert to lowercase
        slug = title.lower()
        
        # Replace special characters with hyphens
        import re
        slug = re.sub(r'[^a-z0-9\s]', '', slug)  # Remove non-alphanumeric except spaces
        slug = re.sub(r'\s+', '-', slug)          # Replace spaces with hyphens
        slug = re.sub(r'-+', '-', slug)           # Replace multiple hyphens with single hyphen
        
        return slug.strip('-')  # Remove leading/trailing hyphens
    
    def search_unsplash_image(self, keyword: str, api_key: str) -> Optional[str]:
        """Search for relevant image on Unsplash"""
        logger.info(f"Searching Unsplash for images related to: {keyword}")
        
        if not api_key:
            logger.warning("No Unsplash API key provided")
            return None
        
        url = f"{Config.UNSPLASH_API_URL}/search/photos"
        headers = {"Authorization": f"Client-ID {api_key}"}
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if response.status_code == 200 and data.get('results') and len(data['results']) > 0:
                return data['results'][0]['urls']['regular']
            else:
                logger.warning(f"No images found for {keyword}")
                return None
        except Exception as e:
            logger.error(f"Error searching Unsplash: {str(e)}")
            return None
    
    def _generate_article_content(self, keyword: str, title: str, model_type: AIModel) -> str:
        """Generate the complete article content based on keyword and title"""
        logger.info(f"Generating article content for: {title}")
        
        prompt = (
            f"Write a comprehensive, engaging, and SEO-optimized WordPress blog post with the title: '{title}' "
            f"focusing on the topic: '{keyword}'.\n\n"
            f"Requirements:\n"
            f"1. Create a well-structured article with an introduction, multiple sections with H2 and H3 headings, and a conclusion.\n"
            f"2. Include 5-7 sections with informative subheadings.\n"
            f"3. Add relevant examples, statistics (if applicable), and practical advice.\n"
            f"4. Write in a conversational, engaging tone that keeps readers interested.\n"
            f"5. Optimize content for SEO while maintaining readability and value for the reader.\n"
            f"6. The article should be approximately 1200-1500 words.\n"
            f"7. Format using WordPress-compatible HTML tags for headings (h2, h3), paragraphs (p), lists (ul, li), etc.\n\n"
            f"Return only the formatted blog post content with no additional commentary."
        )
        
        if model_type == AIModel.CLAUDE:
            return self._query_claude(prompt, max_tokens=5000)
        else:
            return self._query_gpt(prompt, max_tokens=5000)
    
    def _extract_info_from_url(self, url: str, model_type: AIModel) -> Tuple[str, List[str]]:
        """Extract the main topic and key points from a URL"""
        logger.info(f"Extracting information from URL: {url}")
        
        # In a real implementation, we would scrape the content from the URL
        # For simplicity, we'll just use the URL as input for the AI
        
        prompt = (
            f"I have a blog article from this URL: {url}\n\n"
            f"Without accessing the article directly, please:\n"
            f"1. Based on the URL, infer what the main topic of this article likely is.\n"
            f"2. Generate 5-7 likely key points that might be covered in this article.\n\n"
            f"Format your response as JSON with two fields: 'topic' (string) and 'key_points' (array of strings)."
        )
        
        if model_type == AIModel.CLAUDE:
            response = self._query_claude(prompt, max_tokens=1000)
        else:
            response = self._query_gpt(prompt, max_tokens=1000, response_format="json_object")
        
        # Parse the response
        try:
            if model_type == AIModel.CLAUDE:
                # Parse text response from Claude
                import re
                json_str = re.search(r'{.*}', response, re.DOTALL)
                if json_str:
                    data = json.loads(json_str.group())
                else:
                    # Fallback parsing for non-JSON formatted response
                    lines = response.strip().split('\n')
                    topic = lines[0].replace('Topic:', '').strip()
                    key_points = []
                    for line in lines[1:]:
                        if line.strip() and not line.startswith('Key Points:'):
                            key_points.append(line.replace('-', '').strip())
                    data = {"topic": topic, "key_points": key_points}
            else:
                # Parse JSON response from GPT
                data = json.loads(response)
                
            return data.get("topic", url), data.get("key_points", [])
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return url, [f"Content from {url}"]
    
    def _generate_article_from_key_points(
        self, 
        topic: str, 
        key_points: List[str],
        title: str,
        model_type: AIModel
    ) -> str:
        """Generate article content based on a topic and key points"""
        logger.info(f"Generating article from key points for: {title}")
        
        key_points_str = "\n".join([f"- {point}" for point in key_points])
        
        prompt = (
            f"Write a comprehensive, engaging, and SEO-optimized WordPress blog post with the title: '{title}' "
            f"focusing on the topic: '{topic}'.\n\n"
            f"Key points to cover in the article:\n{key_points_str}\n\n"
            f"Requirements:\n"
            f"1. Create a well-structured article with an introduction, multiple sections with H2 and H3 headings, and a conclusion.\n"
            f"2. Cover all the key points provided, organizing them logically.\n"
            f"3. Add relevant examples, statistics (if applicable), and practical advice.\n"
            f"4. Write in a conversational, engaging tone that keeps readers interested.\n"
            f"5. Optimize content for SEO while maintaining readability and value for the reader.\n"
            f"6. The article should be approximately 1200-1500 words.\n"
            f"7. Format using WordPress-compatible HTML tags for headings (h2, h3), paragraphs (p), lists (ul, li), etc.\n\n"
            f"Return only the formatted blog post content with no additional commentary."
        )
        
        if model_type == AIModel.CLAUDE:
            return self._query_claude(prompt, max_tokens=5000)
        else:
            return self._query_gpt(prompt, max_tokens=5000)
    
    def _query_claude(self, prompt: str, max_tokens: int = 1000) -> str:
        """Query Claude API with a prompt"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            # Use a fallback to a more stable Claude model if needed
            try:
                response = self.anthropic_client.messages.create(
                    model=Config.DEFAULT_CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            except Exception as model_error:
                # Try with fallback model as last resort
                logger.warning(f"Error with primary Claude model, trying fallback: {str(model_error)}")
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",  # Fallback to a more standard model
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
        except Exception as e:
            logger.error(f"Error querying Claude API: {str(e)}")
            raise
    
    def _query_gpt(self, prompt: str, max_tokens: int = 1000, response_format: str = None) -> str:
        """Query GPT API with a prompt"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            kwargs = {
                "model": Config.DEFAULT_GPT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            
            if response_format == "json_object":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.openai_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error querying GPT API: {str(e)}")
            raise
