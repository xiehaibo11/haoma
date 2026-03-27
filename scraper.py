#!/usr/bin/env python3
"""
Live Stream Phone Number Scraper
Extracts mobile phone numbers from live stream comments
"""

import re
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

class LiveStreamScraper:
    def __init__(self, url, duration=60):
        self.url = url
        self.duration = duration
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        self.phones_found = {}
        self.start_time = None
        
    def extract_phones(self, text):
        """Extract phone numbers from text"""
        if not text:
            return []
        phones = self.phone_pattern.findall(text)
        return [p for p in phones if len(p) == 11]
    
    def format_phone(self, phone):
        """Format phone number for display"""
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    
    def run(self):
        """Main scraping logic"""
        print(f"Starting scraper for: {self.url}")
        print(f"Will run for {self.duration} seconds")
        print("=" * 60)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)  # Headless mode for automation
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # Navigate to the page
                print("Loading page...")
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                print("Waiting for live stream to initialize...")
                time.sleep(5)
                
                # Scroll to load more content
                print("Scrolling to load comments...")
                for _ in range(3):
                    page.evaluate('window.scrollBy(0, 500)')
                    time.sleep(1)
                
                # Start monitoring
                self.start_time = time.time()
                iteration = 0
                
                print("\nLIVE MONITORING STARTED")
                print("-" * 60)
                
                while time.time() - self.start_time < self.duration:
                    iteration += 1
                    
                    # Get all text from page
                    try:
                        page_text = page.inner_text('body')
                        phones = self.extract_phones(page_text)
                        
                        # Process findings
                        for phone in phones:
                            if phone not in self.phones_found:
                                self.phones_found[phone] = {
                                    'count': 1,
                                    'first_seen': datetime.now().isoformat(),
                                    'formatted': self.format_phone(phone)
                                }
                                print(f"[{iteration}] NEW PHONE: {self.format_phone(phone)}")
                    except:
                        pass
                    
                    # Check for specific comment elements
                    try:
                        elements = page.query_selector_all('div, span, p, li')
                        for elem in elements:
                            try:
                                text = elem.inner_text()
                                if text and len(text) < 200:
                                    phones = self.extract_phones(text)
                                    for phone in phones:
                                        if phone not in self.phones_found:
                                            self.phones_found[phone] = {
                                                'count': 1,
                                                'first_seen': datetime.now().isoformat(),
                                                'formatted': self.format_phone(phone),
                                                'context': text[:100]
                                            }
                                            print(f"[{iteration}] NEW PHONE: {self.format_phone(phone)}")
                                            print(f"    Context: {text[:80]}...")
                            except:
                                continue
                    except:
                        pass
                    
                    # Progress indicator
                    if iteration % 5 == 0:
                        elapsed = int(time.time() - self.start_time)
                        remaining = self.duration - elapsed
                        print(f"[{iteration}] Elapsed: {elapsed}s | Remaining: {remaining}s | Total phones: {len(self.phones_found)}")
                    
                    # Wait before next check
                    time.sleep(2)
                    
                    # Scroll periodically to trigger new content
                    if iteration % 3 == 0:
                        try:
                            page.evaluate('window.scrollBy(0, 300)')
                        except:
                            pass
                
            except Exception as e:
                print(f"Error: {e}")
            
            finally:
                browser.close()
        
        return self.phones_found
    
    def save_results(self, filename='phones_found.json'):
        """Save results to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.phones_found, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {filename}")
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 60)
        print("SCRAPING SUMMARY")
        print("=" * 60)
        print(f"Target URL: {self.url}")
        print(f"Duration: {self.duration} seconds")
        print(f"Total unique phones found: {len(self.phones_found)}")
        
        if self.phones_found:
            print("\nPhone Numbers Found:")
            print("-" * 60)
            for i, (phone, data) in enumerate(self.phones_found.items(), 1):
                print(f"{i}. {data['formatted']} (seen {data['count']} times)")
            print("-" * 60)
        else:
            print("\nNo phone numbers found")
            print("\nPossible reasons:")
            print("- Stream may be offline")
            print("- Comments may require login")
            print("- Chat may be in a popup/iframe")
            print("- No viewers posted phone numbers")


def main():
    url = "https://live.leisu.com/detail-4244416"
    
    # Run scraper for 60 seconds
    scraper = LiveStreamScraper(url, duration=60)
    scraper.run()
    scraper.save_results()
    scraper.print_summary()


if __name__ == "__main__":
    main()
