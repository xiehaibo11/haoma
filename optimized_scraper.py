#!/usr/bin/env python3
"""
Optimized Stream Scraper - Production-grade phone extraction
Handles timeouts, retries, and continuous extraction
"""

import json
import time
import re
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class OptimizedScraper:
    def __init__(self, url, output_file="phones_optimized.json"):
        self.url = url
        self.output_file = output_file
        self.phones = set()
        self.stats = {
            'api_calls': 0,
            'ws_messages': 0,
            'dom_scans': 0,
            'errors': 0
        }
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
        
    def save_progress(self):
        """Save progress immediately"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'url': self.url,
            'total_phones': len(self.phones),
            'phones': sorted(list(self.phones)),
            'stats': self.stats
        }
        
        # Save to JSON
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save to TXT (simple list)
        with open(self.output_file.replace('.json', '.txt'), 'w', encoding='utf-8') as f:
            for phone in sorted(self.phones):
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                f.write(f"{formatted}\n")
        
        return len(self.phones)
        
    def extract_phones(self, text, source=""):
        """Extract phones using multiple patterns"""
        if not text:
            return []
        
        # Limit text size for performance
        if len(text) > 500000:
            text = text[:500000]
        
        found = []
        
        # Pattern 1: Standard 11-digit Chinese mobile
        phones = re.findall(r'1[3-9]\d{9}', text)
        found.extend(phones)
        
        # Pattern 2: With common separators
        separated = re.findall(r'1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}', text)
        for s in separated:
            clean = re.sub(r'[^\d]', '', s)
            if len(clean) == 11:
                found.append(clean)
        
        # Track new phones
        new_count = 0
        for phone in found:
            if len(phone) == 11 and phone not in self.phones:
                self.phones.add(phone)
                new_count += 1
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                self.log(f">>> NEW PHONE [{source}]: {formatted}")
        
        return new_count
        
    def scrape(self, duration=300):
        """Main scraping function"""
        self.log("=" * 70)
        self.log("OPTIMIZED STREAM SCRAPER v2.0")
        self.log("=" * 70)
        self.log(f"Target: {self.url}")
        self.log(f"Duration: {duration} seconds")
        self.log("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            
            # Setup response handler
            def handle_response(response):
                try:
                    url = response.url
                    content_type = response.headers.get('content-type', '')
                    
                    # Process all response types
                    if any(x in content_type for x in ['json', 'html', 'javascript', 'text']):
                        try:
                            text = response.text()
                            self.stats['api_calls'] += 1
                            self.extract_phones(text, f"API:{url[:30]}")
                        except:
                            pass
                except:
                    pass
            
            page.on("response", handle_response)
            
            # Setup WebSocket handler
            def handle_ws(ws):
                def on_message(msg):
                    try:
                        text = msg.text if hasattr(msg, 'text') else str(msg)
                        self.stats['ws_messages'] += 1
                        self.extract_phones(text, "WebSocket")
                    except:
                        pass
                
                ws.on("framereceived", on_message)
                ws.on("framesent", on_message)
            
            context.on("websocket", handle_ws)
            
            try:
                # Navigate with timeout handling
                self.log("Loading page...")
                try:
                    page.goto(self.url, wait_until='domcontentloaded', timeout=30000)
                except PlaywrightTimeout:
                    self.log("Initial load timeout, continuing...", "WARNING")
                
                # Wait and let initial requests complete
                self.log("Waiting for initial content...")
                time.sleep(10)
                
                # Continuous extraction loop
                self.log("Starting continuous extraction...")
                self.log("-" * 70)
                
                start_time = time.time()
                iteration = 0
                last_save = start_time
                last_count = 0
                
                while (time.time() - start_time) < duration:
                    iteration += 1
                    
                    try:
                        # Scan DOM
                        try:
                            body = page.inner_text('body', timeout=5000)
                            self.stats['dom_scans'] += 1
                            self.extract_phones(body, "DOM")
                        except:
                            pass
                        
                        # Scan specific elements
                        try:
                            selectors = ['div', 'span', 'li', 'p', 'a']
                            for selector in selectors:
                                elements = page.query_selector_all(selector)
                                for elem in elements[:50]:
                                    try:
                                        text = elem.inner_text()
                                        if text and 10 < len(text) < 500:
                                            self.extract_phones(text, "Element")
                                    except:
                                        pass
                        except:
                            pass
                        
                        # Check JavaScript variables
                        try:
                            js_vars = ['chat', 'messages', 'users', 'data', 'room', 'stream', 
                                      'userList', 'commentList', 'liveData']
                            js_data = page.evaluate(f'''() => {{
                                const data = {{}};
                                {json.dumps(js_vars)}.forEach(v => {{
                                    if (window[v] !== undefined) {{
                                        try {{
                                            data[v] = JSON.stringify(window[v]).slice(0, 10000);
                                        }} catch(e) {{}}
                                    }}
                                }});
                                return data;
                            }}''')
                            
                            for key, value in js_data.items():
                                if value:
                                    self.extract_phones(value, f"JS:{key}")
                        except:
                            pass
                        
                        # Scroll periodically
                        if iteration % 5 == 0:
                            try:
                                page.evaluate('window.scrollBy(0, 800)')
                            except:
                                pass
                        
                        # Progress report
                        current_count = len(self.phones)
                        elapsed = int(time.time() - start_time)
                        remaining = duration - elapsed
                        
                        if current_count != last_count or iteration % 10 == 0:
                            self.log(f"[{iteration}] Time: {elapsed}s | Phones: {current_count} | API: {self.stats['api_calls']}")
                            last_count = current_count
                        
                        # Save progress every 30 seconds
                        if time.time() - last_save >= 30:
                            saved_count = self.save_progress()
                            self.log(f"Progress saved: {saved_count} phones")
                            last_save = time.time()
                        
                        # Small delay
                        time.sleep(2)
                        
                    except Exception as e:
                        self.stats['errors'] += 1
                        if iteration % 10 == 0:
                            self.log(f"Error in loop: {e}", "ERROR")
                        time.sleep(2)
                
            except KeyboardInterrupt:
                self.log("Stopped by user")
            except Exception as e:
                self.log(f"Fatal error: {e}", "ERROR")
            finally:
                browser.close()
        
        # Final save
        self.save_progress()
        return self.phones
    
    def print_summary(self):
        """Print final summary"""
        self.log("\n" + "=" * 70)
        self.log("EXTRACTION COMPLETE")
        self.log("=" * 70)
        self.log(f"Total unique phones: {len(self.phones)}")
        self.log(f"API calls processed: {self.stats['api_calls']}")
        self.log(f"WebSocket messages: {self.stats['ws_messages']}")
        self.log(f"DOM scans: {self.stats['dom_scans']}")
        self.log(f"Errors: {self.stats['errors']}")
        
        if self.phones:
            self.log("\nPhone Numbers:")
            for phone in sorted(self.phones):
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                self.log(f"  - {formatted}")
        
        self.log(f"\nResults saved to:")
        self.log(f"  - {self.output_file}")
        self.log(f"  - {self.output_file.replace('.json', '.txt')}")


def main():
    url = "https://live.leisu.com/detail-4455336"
    
    scraper = OptimizedScraper(url)
    try:
        scraper.scrape(duration=120)  # 2 minutes
    finally:
        scraper.print_summary()


if __name__ == "__main__":
    main()
