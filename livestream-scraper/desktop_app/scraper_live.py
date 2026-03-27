"""
Live stream scraper with retry logic and dynamic content handling.
Optimized for real-time comment extraction from leisu.com
"""

import threading
import time
from typing import Callable, List, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from extractor_fixed import LeisuExtractor, ExtractionResult


class LiveStreamScraper:
    """
    Production scraper for live streams with:
    - Retry logic for timeouts
    - Dynamic content detection
    - Real-time comment extraction
    - Graceful error handling
    """
    
    def __init__(self, url: str, on_data: Callable, on_log: Optional[Callable] = None):
        self.url = url
        self.on_data = on_data
        self.on_log = on_log
        self.running = False
        self.extractor = LeisuExtractor()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        self.seen_texts = set()  # Track seen comments to avoid duplicates
        self.retry_count = 0
        self.max_retries = 3
    
    def log(self, msg: str):
        """Log message."""
        ts = datetime.now().strftime('%H:%M:%S')
        full = f"[{ts}] {msg}"
        print(full)
        if self.on_log:
            self.on_log(full)
    
    def start(self):
        """Start scraping with retry logic."""
        self.running = True
        
        while self.running and self.retry_count < self.max_retries:
            try:
                self._run_scraper()
                break  # Success
            except Exception as e:
                self.retry_count += 1
                self.log(f"Error (attempt {self.retry_count}/{self.max_retries}): {e}")
                self._cleanup()
                
                if self.running and self.retry_count < self.max_retries:
                    wait = self.retry_count * 5
                    self.log(f"Retrying in {wait}s...")
                    time.sleep(wait)
        
        if self.retry_count >= self.max_retries:
            self.log("Max retries reached. Stopping.")
        
        self._cleanup()
    
    def _run_scraper(self):
        """Main scraping loop."""
        self.log("Initializing browser...")
        self.playwright = sync_playwright().start()
        
        # Launch with desktop viewport (better for leisu)
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled',
                  '--disable-web-security',
                  '--disable-features=IsolateOrigins,site-per-process']
        )
        
        # Desktop viewport
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = self.context.new_page()
        
        # Navigate with longer timeout
        self.log(f"Loading {self.url}...")
        try:
            self.page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
        except Exception as e:
            self.log(f"Navigation timeout, continuing anyway...")
        
        # Wait for page to settle
        time.sleep(8)
        
        # Try to activate chat/comment section
        self._activate_chat()
        
        self.log("Starting extraction loop...")
        check_count = 0
        
        while self.running:
            check_count += 1
            
            try:
                # Extract data
                results = self._extract_comments()
                
                # Process new results
                new_results = []
                for r in results:
                    text_key = f"{r.username}:{r.context[:50]}"
                    if text_key not in self.seen_texts:
                        self.seen_texts.add(text_key)
                        new_results.append(r)
                
                if new_results:
                    self.log(f"Found {len(new_results)} new comment(s)")
                    if self.on_data:
                        self.on_data(new_results)
                
                # Scroll periodically
                if check_count % 4 == 0:
                    self._scroll()
                
                # Reset retry on success
                self.retry_count = 0
                
            except Exception as e:
                self.log(f"Extract error: {e}")
            
            time.sleep(3)  # Check every 3 seconds
    
    def _activate_chat(self):
        """Try to activate chat section."""
        selectors = [
            'text=聊天', 'text=评论', 'text=弹幕', 'text=互动',
            '.chat-tab', '.comment-tab', '[class*="chat"]', '[class*="comment"]'
        ]
        
        for sel in selectors:
            try:
                elem = self.page.query_selector(sel)
                if elem and elem.is_visible():
                    elem.click()
                    self.log(f"Activated chat: {sel}")
                    time.sleep(2)
                    return
            except:
                pass
    
    def _extract_comments(self) -> List[ExtractionResult]:
        """Extract comments from page."""
        all_results = []
        
        # Strategy 1: Try to find comment containers
        comment_selectors = [
            '.comment-item', '.chat-item', '.message-item',
            '.danmu-item', '.live-comment',
            '[class*="comment-list"] > div',
            '[class*="chat-list"] > div',
            '[class*="message-list"] > div',
            '.list-item', '.item'
        ]
        
        for selector in comment_selectors:
            try:
                elements = self.page.query_selector_all(selector)
                if elements:
                    for elem in elements[:30]:  # Process first 30
                        results = self._process_element(elem)
                        all_results.extend(results)
                    
                    if all_results:
                        return all_results
            except:
                pass
        
        # Strategy 2: Extract all visible text with phone patterns
        try:
            body_text = self.page.inner_text('body')
            lines = body_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and 5 < len(line) < 200:
                    # Check if contains phone pattern
                    import re
                    if re.search(r'1[3-9]\d{9}', line):
                        results = self.extractor.extract_all(comment=line)
                        all_results.extend(results)
        except:
            pass
        
        return all_results
    
    def _process_element(self, elem) -> List[ExtractionResult]:
        """Process a single element."""
        results = []
        
        try:
            # Get username
            username = ""
            user_selectors = ['.username', '.user-name', '.name', 
                            '[class*="user"]', '[class*="name"]']
            for sel in user_selectors:
                try:
                    user_elem = elem.query_selector(sel)
                    if user_elem:
                        username = user_elem.inner_text().strip()
                        break
                except:
                    pass
            
            # Get message text
            text = ""
            text_selectors = ['.content', '.message', '.text', 
                            '.comment', 'p', 'span']
            for sel in text_selectors:
                try:
                    text_elem = elem.query_selector(sel)
                    if text_elem:
                        text = text_elem.inner_text().strip()
                        break
                except:
                    pass
            
            # If no specific text, get all
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
        
        except:
            pass
        
        return results
    
    def _scroll(self):
        """Scroll to load more."""
        try:
            self.page.evaluate('window.scrollBy(0, 600)')
        except:
            pass
    
    def stop(self):
        """Stop scraping."""
        self.running = False
        self.log("Stopping...")
    
    def _cleanup(self):
        """Cleanup resources."""
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
