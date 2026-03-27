#!/usr/bin/env python3
"""
Live Stream Phone Number Scraper - Extended Session
"""

import re
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

class LiveStreamScraper:
    def __init__(self, url, duration=300):  # 5 minutes default
        self.url = url
        self.duration = duration
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        self.phones_found = {}
        self.start_time = None
        
    def extract_phones(self, text):
        if not text:
            return []
        phones = self.phone_pattern.findall(text)
        return [p for p in phones if len(p) == 11]
    
    def format_phone(self, phone):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    
    def run(self):
        print(f"Starting extended scraper for: {self.url}")
        print(f"Will run for {self.duration} seconds ({self.duration//60} minutes)")
        print("=" * 60)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                print("Loading page...")
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                time.sleep(5)
                
                # Scroll to load comments
                for _ in range(5):
                    page.evaluate('window.scrollBy(0, 800)')
                    time.sleep(1)
                
                self.start_time = time.time()
                iteration = 0
                
                print("\nMONITORING STARTED - Press Ctrl+C to stop early")
                print("-" * 60)
                
                while time.time() - self.start_time < self.duration:
                    iteration += 1
                    
                    # Get page content
                    try:
                        page_text = page.inner_text('body')
                        phones = self.extract_phones(page_text)
                        
                        for phone in phones:
                            if phone not in self.phones_found:
                                self.phones_found[phone] = {
                                    'count': 1,
                                    'first_seen': datetime.now().isoformat(),
                                    'formatted': self.format_phone(phone)
                                }
                                print(f"[NEW] {self.format_phone(phone)} (Total: {len(self.phones_found)})")
                            else:
                                self.phones_found[phone]['count'] += 1
                    except:
                        pass
                    
                    # Check specific elements
                    try:
                        elements = page.query_selector_all('div, span, p, li, td')
                        for elem in elements:
                            try:
                                text = elem.inner_text()
                                if text and 10 < len(text) < 300:
                                    phones = self.extract_phones(text)
                                    for phone in phones:
                                        if phone not in self.phones_found:
                                            self.phones_found[phone] = {
                                                'count': 1,
                                                'first_seen': datetime.now().isoformat(),
                                                'formatted': self.format_phone(phone),
                                                'context': text.strip()[:100]
                                            }
                                            print(f"[NEW] {self.format_phone(phone)}")
                                            print(f"      Context: {text.strip()[:60]}...")
                            except:
                                continue
                    except:
                        pass
                    
                    # Progress every 10 iterations
                    if iteration % 10 == 0:
                        elapsed = int(time.time() - self.start_time)
                        remaining = self.duration - elapsed
                        print(f"[{iteration}] Elapsed: {elapsed//60}m{elapsed%60}s | Remaining: {remaining//60}m{remaining%60}s | Phones: {len(self.phones_found)}")
                    
                    # Scroll periodically
                    if iteration % 5 == 0:
                        try:
                            page.evaluate('window.scrollBy(0, 500)')
                        except:
                            pass
                    
                    time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nStopped by user")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                browser.close()
        
        return self.phones_found
    
    def save_results(self, filename='phones_found_extended.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.phones_found, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to: {filename}")

def main():
    url = "https://live.leisu.com/detail-4244416"
    
    # Run for 3 minutes (180 seconds)
    scraper = LiveStreamScraper(url, duration=180)
    scraper.run()
    scraper.save_results()
    
    # Print summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total phones found: {len(scraper.phones_found)}")
    
    if scraper.phones_found:
        print("\nList:")
        for i, (phone, data) in enumerate(scraper.phones_found.items(), 1):
            print(f"  {i}. {data['formatted']}")

if __name__ == "__main__":
    main()
