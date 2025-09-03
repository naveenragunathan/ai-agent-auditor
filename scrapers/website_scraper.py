import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List
import re
from urllib.parse import urljoin, urlparse

class WebsiteScraper:
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def scrape(self, url: str) -> Dict:
        """Scrape website and extract structured data"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch website: HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    return {
                        "url": url,
                        "title": self._extract_title(soup),
                        "meta_description": self._extract_meta_description(soup),
                        "meta_keywords": self._extract_meta_keywords(soup),
                        "headers": self._extract_headers(soup),
                        "hero": self._extract_hero_section(soup),
                        "body_text": self._extract_body_text(soup),
                        "cta_elements": self._extract_cta_elements(soup),
                        "trust_signals": self._extract_trust_signals(soup),
                        "social_links": self._extract_social_links(soup),
                        "images": self._extract_images(soup),
                        "forms": self._extract_forms(soup)
                    }
        
        except Exception as e:
            print(f"Error scraping website {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e),
                "title": "",
                "meta_description": "",
                "body_text": "",
                "hero": {},
                "headers": [],
                "cta_elements": [],
                "trust_signals": [],
                "social_links": [],
                "images": [],
                "forms": []
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '').strip() if meta_desc else ""
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        return meta_keywords.get('content', '').strip() if meta_keywords else ""
    
    def _extract_headers(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all header tags (H1-H6)"""
        headers = []
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                headers.append({
                    "level": i,
                    "text": header.get_text().strip(),
                    "tag": f"h{i}"
                })
        return headers
    
    def _extract_hero_section(self, soup: BeautifulSoup) -> Dict:
        """Extract hero section content"""
        hero_data = {
            "headline": "",
            "subheadline": "",
            "cta_text": "",
            "cta_link": "",
            "background_image": ""
        }
        
        # Look for common hero section patterns
        hero_selectors = [
            '.hero', '.banner', '.jumbotron', '.hero-section',
            '.main-banner', '.header-banner', '[class*="hero"]'
        ]
        
        hero_section = None
        for selector in hero_selectors:
            hero_section = soup.select_one(selector)
            if hero_section:
                break
        
        # If no specific hero section found, use the first section or main content
        if not hero_section:
            hero_section = soup.find('main') or soup.find('section') or soup.find('div', class_=re.compile(r'content|main'))
        
        if hero_section:
            # Extract headline (usually H1 or largest heading)
            h1 = hero_section.find('h1')
            if h1:
                hero_data["headline"] = h1.get_text().strip()
            
            # Extract subheadline (p tag or h2 near h1)
            subheadline = hero_section.find('p') or hero_section.find('h2')
            if subheadline:
                hero_data["subheadline"] = subheadline.get_text().strip()
            
            # Extract CTA
            cta_link = hero_section.find('a', class_=re.compile(r'btn|button|cta'))
            if cta_link:
                hero_data["cta_text"] = cta_link.get_text().strip()
                hero_data["cta_link"] = cta_link.get('href', '')
        
        return hero_data
    
    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract main body text content"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit to first 5000 characters
    
    def _extract_cta_elements(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract call-to-action elements"""
        cta_elements = []
        
        # Look for buttons and CTA links
        cta_selectors = [
            'a[class*="btn"]', 'a[class*="button"]', 'a[class*="cta"]',
            'button', 'input[type="submit"]', '.call-to-action a'
        ]
        
        for selector in cta_selectors:
            for element in soup.select(selector):
                cta_elements.append({
                    "text": element.get_text().strip(),
                    "href": element.get('href', ''),
                    "type": element.name,
                    "classes": element.get('class', [])
                })
        
        return cta_elements[:10]  # Limit to first 10 CTAs
    
    def _extract_trust_signals(self, soup: BeautifulSoup) -> List[str]:
        """Extract trust signals like testimonials, reviews, badges"""
        trust_signals = []
        
        # Look for testimonials
        testimonial_selectors = [
            '.testimonial', '.review', '.quote', '[class*="testimonial"]',
            '[class*="review"]', '[class*="quote"]'
        ]
        
        for selector in testimonial_selectors:
            for element in soup.select(selector):
                text = element.get_text().strip()
                if text and len(text) > 20:
                    trust_signals.append(text[:200])
        
        # Look for trust badges/logos
        trust_images = soup.find_all('img', alt=re.compile(r'trust|secure|verified|badge|award', re.I))
        for img in trust_images:
            alt_text = img.get('alt', '')
            if alt_text:
                trust_signals.append(f"Trust badge: {alt_text}")
        
        return trust_signals[:5]
    
    def _extract_social_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract social media links"""
        social_links = []
        social_patterns = {
            'twitter': r'twitter\.com',
            'linkedin': r'linkedin\.com',
            'facebook': r'facebook\.com',
            'instagram': r'instagram\.com',
            'youtube': r'youtube\.com'
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.I):
                    social_links.append({
                        "platform": platform,
                        "url": href,
                        "text": link.get_text().strip()
                    })
                    break
        
        return social_links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract image information"""
        images = []
        for img in soup.find_all('img')[:10]:  # Limit to first 10 images
            images.append({
                "src": img.get('src', ''),
                "alt": img.get('alt', ''),
                "title": img.get('title', '')
            })
        return images
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract form information"""
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                "action": form.get('action', ''),
                "method": form.get('method', 'get'),
                "fields": []
            }
            
            for input_field in form.find_all(['input', 'textarea', 'select']):
                form_data["fields"].append({
                    "type": input_field.get('type', input_field.name),
                    "name": input_field.get('name', ''),
                    "placeholder": input_field.get('placeholder', ''),
                    "required": input_field.has_attr('required')
                })
            
            forms.append(form_data)
        
        return forms
