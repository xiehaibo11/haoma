"""
Improved scraper for leisu.com with better element detection and debugging.
"""

import threading
import time
import re
from typing import Callable, List, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from extractor import LeisuExtractor, ExtractionResult


class LeisuScraper:
    """
    Improved background scraper for leisu.com live streams.
    """
    
    def __init__(self, url: str, callback: Callable[[List[ExtractionResult]], None],
                 log_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize scraper.
        
        Args:
            url: Target URL
            callback: Function to call with new results
            log_callback: Function to call with log messages
        """
        self.url = url
        self.callback = callback
        self.log_callback = log_callback
        self.running = False
        self.extractor = LeisuExtractor()
        
        # Browser
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Settings
        self.check_interval = 3  # Check every 3 seconds
        self.scroll_interval = 5  # Scroll every 5 checks
        self.seen_phones = set()
        
        # Statistics
        self.stats = {
            'checks': 0,
            'found': 0,
            'errors': 0
        }
    
    def log(self, message: str):
        """Log a message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}"
        print(full_msg)
        if self.log_callback:
            self.log_callback(full_msg)
    
    def start(self):
        """Start scraping."""
        self.running = True
        
        try:
            self.log("Initializing browser...")
            self.playwright = sync_playwright().start()
            
            # Launch browser with mobile viewport (better for leisu.com)
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Use mobile viewport - leisu.com often shows chat better on mobile
            self.context = self.browser.new_context(
                viewport={'width': 375, 'height': 812},  # iPhone X size
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            )
            
            self.page = self.context.new_page()
            
            self.log(f"Navigating to {self.url}...")
            self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            
            self.log("Page loaded, waiting for content...")
            time.sleep(5)
            
            # Try to find and click on chat/comment section
            self._init_chat_section()
            
            check_count = 0
            
            while self.running:
                self.stats['checks'] += 1
                
                # Extract data
                results = self._extract_data()
                
                if results:
                    new_results = []
                    for result in results:
                        if result.phone not in self.seen_phones:
                            self.seen_phones.add(result.phone)
                            new_results.append(result)
                            self.stats['found'] += 1
                    
                    if new_results:
                        self.log(f"Found {len(new_results)} new phone(s)")
                        if self.callback:
                            self.callback(new_results)
                
                # Scroll periodically
                check_count += 1
                if check_count % self.scroll_interval == 0:
                    self._scroll_page()
                
                time.sleep(self.check_interval)
                
        except Exception as e:
            self.log(f"Error: {e}")
            self.stats['errors'] += 1
        
        finally:
            self._cleanup()
    
    def _init_chat_section(self):
        """Try to find and initialize chat section."""
        try:
            # Look for chat/comment tabs or buttons
            chat_selectors = [
                'text=聊天',
                'text=评论',
                'text=弹幕',
                '[class*="chat"]',
                '[class*="comment"]',
                '[class*="message"]',
            ]
            
            for selector in chat_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        element.click()
                        self.log(f"Clicked chat element: {selector}")
                        time.sleep(2)
                        return
                except:
                    continue
            
            self.log("Chat section initialized (or not found)")
            
        except Exception as e:
            self.log(f"Chat init warning: {e}")
    
    def _extract_data(self) -> List[ExtractionResult]:
        """
        Extract data from page using multiple strategies.
        """
        all_results = []
        
        # Strategy 1: Try specific leisu.com selectors
        results = self._extract_from_leisu_selectors()
        if results:
            all_results.extend(results)
        
        # Strategy 2: Try generic selectors
        if not all_results:
            results = self._extract_from_generic_selectors()
            if results:
                all_results.extend(results)
        
        # Strategy 3: Scan entire page
        if not all_results:
            results = self._extract_from_page_text()
            if results:
                all_results.extend(results)
        
        return all_results
    
    def _extract_from_leisu_selectors(self) -> List[ExtractionResult]:
        """Extract using leisu.com specific selectors."""
        results = []
        
        # Common patterns on leisu.com
        selectors = [
            # Comment/Chat containers
            '.comment-item',
            '.chat-item',
            '.message-item',
            '.danmu-item',
            '[class*="comment-list"] > div',
            '[class*="chat-list"] > div',
            '[class*="message-list"] > div',
            
            # Specific to leisu
            '.live-chat-item',
            '.live-comment',
            '[data-type="comment"]',
            '[data-type="chat"]',
            
            # Generic fallbacks
            '.list-item',
            '.item',
        ]
        
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                
                if elements:
                    self.log(f"Found {len(elements)} elements with '{selector}'")
                    
                    for elem in elements[:30]:  # Process first 30
                        try:
                            # Get username
                            username = ""
                            username_selectors = [
                                '.username',
                                '.user-name',
                                '.name',
                                '[class*="user"]',
                                '[class*="name"]',
                            ]
                            
                            for us in username_selectors:
                                try:
                                    user_elem = elem.query_selector(us)
                                    if user_elem:
                                        username = user_elem.inner_text().strip()
                                        break
                                except:
                                    continue
                            
                            # Get message text
                            text = ""
                            text_selectors = [
                                '.content',
                                '.message',
                                '.text',
                                '.comment',
                                'p',
                                'span',
                            ]
                            
                            for ts in text_selectors:
                                try:
                                    text_elem = elem.query_selector(ts)
                                    if text_elem:
                                        text = text_elem.inner_text().strip()
                                        break
                                except:
                                    continue
                            
                            # If no specific text, get all text
                            if not text:
                                try:
                                    text = elem.inner_text().strip()
                                except:
                                    pass
                            
                            # Extract phones
                            if username or text:
                                extracted = self.extractor.extract_all(
                                    username=username,
                                    comment=text
                                )
                                results.extend(extracted)
                        
                        except Exception as e:
                            continue
                    
                    # If we found results, don't try other selectors
                    if results:
                        return results
                        
            except Exception as e:
                continue
        
        return results
    
    def _extract_from_generic_selectors(self) -> List[ExtractionResult]:
        """Extract using generic selectors."""
        results = []
        
        try:
            # Get all divs and spans that might contain comments
            elements = self.page.query_selector_all('div, span, p, li')
            
            for elem in elements[:50]:
                try:
                    text = elem.inner_text()
                    if text and 10 < len(text) < 200:
                        # Check if contains phone-like pattern
                        if re.search(r'1[3-9]\d{9}', text):
                            extracted = self.extractor.extract_all(comment=text)
                            results.extend(extracted)
                except:
                    continue
        
        except Exception as e:
            self.log(f"Generic extraction error: {e}")
        
        return results
    
    def _extract_from_page_text(self) -> List[ExtractionResult]:
        """Extract from entire page text as last resort."""
        results = []
        
        try:
            body_text = self.page.inner_text('body')
            
            # Check if any phone numbers exist
            if re.search(r'1[3-9]\d{9}', body_text):
                self.log("Scanning entire page for phones...")
                
                # Split by newlines to get individual messages
                lines = body_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line and 10 < len(line) < 200:
                        extracted = self.extractor.extract_all(comment=line)
                        results.extend(extracted)
        
        except Exception as e:
            self.log(f"Page text extraction error: {e}")
        
        return results
    
    def _scroll_page(self):
        """Scroll page to load more content."""
        try:
            self.page.evaluate('window.scrollBy(0, 500)')
        except:
            pass
    
    def stop(self):
        """Stop scraping."""
        self.running = False
        self.log("Stopping scraper...")
    
    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        
        self.log(f"Scraper stopped. Stats: {self.stats}")
    
    def get_stats(self) -> dict:
        """Get scraping statistics."""
        return self.stats.copy()
