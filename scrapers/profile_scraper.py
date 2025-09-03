import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import os
import tweepy

class ProfileScraper:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    async def scrape(self, profile_url: str) -> Dict:
        """Scrape creator profile from various platforms"""
        try:
            if "twitter.com" in profile_url or "x.com" in profile_url:
                return await self._scrape_twitter(profile_url)
            elif "linkedin.com" in profile_url:
                return await self._scrape_linkedin(profile_url)
            elif "instagram.com" in profile_url:
                return await self._scrape_instagram(profile_url)
            else:
                return await self._scrape_generic_profile(profile_url)
        
        except Exception as e:
            print(f"Error scraping profile {profile_url}: {str(e)}")
            return {
                "platform": "unknown",
                "url": profile_url,
                "error": str(e),
                "bio": "",
                "follower_count": 0,
                "following_count": 0,
                "post_count": 0,
                "recent_posts": [],
                "tone": "unknown"
            }
    
    async def _scrape_twitter(self, url: str) -> Dict:
        """Scrape Twitter/X profile"""
        profile_data = {
            "platform": "twitter",
            "url": url,
            "bio": "",
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0,
            "recent_posts": [],
            "tone": "professional"
        }
        
        try:
            # Extract username from URL
            username = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
            if not username:
                return profile_data
            
            username = username.group(1)
            
            # If Twitter API is available, use it
            if self.twitter_bearer_token:
                try:
                    client = tweepy.Client(bearer_token=self.twitter_bearer_token)
                    user = client.get_user(username=username, user_fields=['description', 'public_metrics'])
                    
                    if user.data:
                        profile_data.update({
                            "bio": user.data.description or "",
                            "follower_count": user.data.public_metrics.get('followers_count', 0),
                            "following_count": user.data.public_metrics.get('following_count', 0),
                            "post_count": user.data.public_metrics.get('tweet_count', 0)
                        })
                        
                        # Get recent tweets
                        tweets = client.get_users_tweets(user.data.id, max_results=10)
                        if tweets.data:
                            profile_data["recent_posts"] = [tweet.text for tweet in tweets.data[:5]]
                
                except Exception as api_error:
                    print(f"Twitter API error: {api_error}")
                    # Fall back to web scraping
                    return await self._scrape_generic_profile(url)
            else:
                # Web scraping fallback
                return await self._scrape_generic_profile(url)
        
        except Exception as e:
            print(f"Twitter scraping error: {e}")
        
        return profile_data
    
    async def _scrape_linkedin(self, url: str) -> Dict:
        """Scrape LinkedIn profile (limited due to anti-scraping measures)"""
        profile_data = {
            "platform": "linkedin",
            "url": url,
            "bio": "",
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0,
            "recent_posts": [],
            "tone": "professional"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract basic info (LinkedIn heavily restricts scraping)
                        title_tag = soup.find('title')
                        if title_tag:
                            title_text = title_tag.get_text()
                            profile_data["bio"] = title_text.split('|')[0].strip() if '|' in title_text else title_text
        
        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
        
        return profile_data
    
    async def _scrape_instagram(self, url: str) -> Dict:
        """Scrape Instagram profile (limited due to anti-scraping measures)"""
        profile_data = {
            "platform": "instagram",
            "url": url,
            "bio": "",
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0,
            "recent_posts": [],
            "tone": "casual"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Try to extract basic info from meta tags
                        description_meta = soup.find('meta', property='og:description')
                        if description_meta:
                            profile_data["bio"] = description_meta.get('content', '')
        
        except Exception as e:
            print(f"Instagram scraping error: {e}")
        
        return profile_data
    
    async def _scrape_generic_profile(self, url: str) -> Dict:
        """Generic profile scraping for any URL"""
        profile_data = {
            "platform": "generic",
            "url": url,
            "bio": "",
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0,
            "recent_posts": [],
            "tone": "professional"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract bio from various sources
                        bio_sources = [
                            soup.find('meta', property='og:description'),
                            soup.find('meta', attrs={'name': 'description'}),
                            soup.find('p', class_=re.compile(r'bio|about|description')),
                            soup.find('div', class_=re.compile(r'bio|about|description'))
                        ]
                        
                        for source in bio_sources:
                            if source:
                                if source.name == 'meta':
                                    profile_data["bio"] = source.get('content', '')
                                else:
                                    profile_data["bio"] = source.get_text().strip()
                                break
                        
                        # Try to extract recent content
                        content_elements = soup.find_all(['article', 'div'], class_=re.compile(r'post|tweet|update|content'))
                        recent_posts = []
                        for element in content_elements[:5]:
                            text = element.get_text().strip()
                            if text and len(text) > 20:
                                recent_posts.append(text[:200])
                        
                        profile_data["recent_posts"] = recent_posts
        
        except Exception as e:
            print(f"Generic profile scraping error: {e}")
        
        return profile_data
