"""
Background scraper for leisu.com live streams.
"""

import threading
import time
from typing import Callable, List, Optional

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from extractor import LeisuExtractor, ExtractionResult


class LeisuScraper:
    """
    Background scraper for extracting data from leisu.com.
    Runs in a separate thread and calls back with results.
    """
    
    def __init__(self, url: str, callback: Callable[[List[ExtractionResult]], None]):
        """
        Initialize scraper.
        
        Args:
            url: Target URL to scrape
            callback: Function to call with new results
        """
        self.url = url
        self.callback = callback
        self.running = False
        self.extractor = LeisuExtractor()
        
        # Browser instances
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Settings
        self.check_interval = 5  # Seconds between checks
        self.scroll_interval = 3  # Scroll every N checks
        self.seen_phones = set()  # For deduplication during session
    
    def start(self):
        """Start scraping."""
        self.running = True
        
        try:
            # Initialize browser
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = self.context.new_page()
            
            # Navigate to page
            self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            
            # Wait for content
            time.sleep(5)
            
            check_count = 0
            
            while self.running:
                # Extract data
                results = self._extract_from_page()
                
                # Filter new results
                new_results = []
                for result in results:
                    if result.phone not in self.seen_phones:
                        self.seen_phones.add(result.phone)
                        new_results.append(result)
                
                # Call callback with new results
                if new_results and self.callback:
                    self.callback(new_results)
                
                # Scroll periodically
                check_count += 1
                if check_count % self.scroll_interval == 0:
                    self._scroll_page()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except Exception as e:
            print(f"Scraper error: {e}")
        
        finally:
            self._cleanup()
    
    def stop(self):
        """Stop scraping."""
        self.running = False
    
    def _extract_from_page(self) -> List[ExtractionResult]:
        """
        Extract phone numbers and usernames from current page.
        
        Returns:
            List of extraction results
        """
        results = []
        
        try:
            # Try to find comment/chat elements
            selectors = [
                '.comment-item',
                '.chat-item',
                '.message-item',
                '[class*="comment"]',
                '[class*="chat"]',
                '[class*="message"]',
                'div',  # Fallback
            ]
            
            for selector in selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    
                    for elem in elements[:50]:  # Limit to 50 elements
                        try:
                            # Try to get username
                            username_elem = elem.query_selector(
                                '[class*="user"], [class*="name"], .username'
                            )
                            username = username_elem.inner_text() if username_elem else ""
                            
                            # Get text content
                            text = elem.inner_text()
                            
                            if username or text:
                                # Extract from this element
                                extracted = self.extractor.extract_all(
                                    username=username,
                                    comment=text
                                )
                                results.extend(extracted)
                        except:
                            continue
                    
                    # If we found results, break
                    if results:
                        break
                        
                except:
                    continue
            
            # Fallback: scan entire page
            if not results:
                try:
                    body_text = self.page.inner_text('body')
                    results = self.extractor.extract_all(page_content=body_text)
                except:
                    pass
        
        except Exception as e:
            print(f"Extraction error: {e}")
        
        return results
    
    def _scroll_page(self):
        """Scroll page to load more content."""
        try:
            self.page.evaluate('window.scrollBy(0, 800)')
        except:
            pass
    
    def _cleanup(self):
        """Clean up browser resources."""
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
