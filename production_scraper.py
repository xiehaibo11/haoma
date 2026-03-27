#!/usr/bin/env python3
"""
Production Stream Scraper - Continuous phone extraction
Features:
- Multiple concurrent streams
- Automatic retry and error recovery
- Real-time progress saving
- CSV and JSON output
"""

import json
import csv
import time
import re
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class ProductionScraper:
    def __init__(self, urls, output_dir="./output"):
        self.urls = urls if isinstance(urls, list) else [urls]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.phones = {}  # phone -> {url, timestamp, source}
        self.stats = {
            'urls_processed': 0,
            'api_calls': 0,
            'errors': 0,
            'start_time': None
        }
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        self.log("Shutdown signal received, saving progress...")
        self.running = False
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
        
    def save_all(self):
        """Save all results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = self.output_dir / f"phones_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': len(self.phones),
                'phones': self.phones
            }, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        csv_file = self.output_dir / f"phones_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['phone', 'formatted', 'source_url', 'timestamp', 'source_type'])
            for phone, data in sorted(self.phones.items()):
                writer.writerow([
                    phone,
                    f"{phone[:3]}-{phone[3:7]}-{phone[7:]}",
                    data.get('url', ''),
                    data.get('timestamp', ''),
                    data.get('source', '')
                ])
        
        # Save simple list
        txt_file = self.output_dir / f"phones_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for phone in sorted(self.phones.keys()):
                f.write(f"{phone[:3]}-{phone[3:7]}-{phone[7:]}\n")
        
        return len(self.phones), json_file.name
        
    def extract_phones(self, text, url, source):
        """Extract phones and track metadata"""
        if not text or len(text) > 1000000:
            return 0
        
        found = []
        
        # Standard Chinese mobile
        phones = re.findall(r'1[3-9]\d{9}', text)
        found.extend(phones)
        
        # With separators
        separated = re.findall(r'1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}', text)
        for s in separated:
            clean = re.sub(r'[^\d]', '', s)
            if len(clean) == 11:
                found.append(clean)
        
        new_count = 0
        for phone in found:
            if len(phone) == 11 and phone not in self.phones:
                self.phones[phone] = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'source': source
                }
                new_count += 1
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                self.log(f"NEW PHONE: {formatted} [from {source[:30]}...]")
        
        return new_count
        
    def scrape_single(self, url, duration=300):
        """Scrape a single URL"""
        self.log(f"\n{'='*70}")
        self.log(f"Scraping: {url}")
        self.log(f"{'='*70}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            
            # Response handler
            def handle_response(response):
                try:
                    content_type = response.headers.get('content-type', '')
                    if any(x in content_type for x in ['json', 'html', 'javascript', 'text']):
                        text = response.text()
                        self.stats['api_calls'] += 1
                        self.extract_phones(text, url, f"API:{response.url[:40]}")
                except:
                    pass
            
            page.on("response", handle_response)
            
            try:
                # Load page
                self.log("Loading page...")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                except PlaywrightTimeout:
                    self.log("Load timeout, continuing...", "WARNING")
                
                time.sleep(10)
                self.log("Starting extraction loop...")
                
                start = time.time()
                iteration = 0
                last_save = start
                last_count = len(self.phones)
                
                while self.running and (time.time() - start) < duration:
                    iteration += 1
                    
                    try:
                        # Scan DOM
                        body = page.inner_text('body', timeout=5000)
                        self.extract_phones(body, url, "DOM")
                        
                        # Scan elements
                        for selector in ['div', 'span', 'li']:
                            elements = page.query_selector_all(selector)
                            for elem in elements[:30]:
                                try:
                                    text = elem.inner_text()
                                    if text and 10 < len(text) < 300:
                                        self.extract_phones(text, url, "Element")
                                except:
                                    pass
                        
                        # Scroll periodically
                        if iteration % 5 == 0:
                            page.evaluate('window.scrollBy(0, 800)')
                        
                        # Progress report
                        current = len(self.phones)
                        if current != last_count or iteration % 10 == 0:
                            elapsed = int(time.time() - start)
                            self.log(f"[{iteration}] Elapsed: {elapsed}s | Total phones: {current}")
                            last_count = current
                        
                        # Save every 30 seconds
                        if time.time() - last_save >= 30:
                            count, file = self.save_all()
                            self.log(f"Progress saved: {count} phones -> {file}")
                            last_save = time.time()
                        
                        time.sleep(2)
                        
                    except Exception as e:
                        self.stats['errors'] += 1
                        time.sleep(2)
                
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
            finally:
                browser.close()
        
        self.stats['urls_processed'] += 1
        
    def run(self, duration_per_url=300):
        """Run scraper for all URLs"""
        self.log("=" * 70)
        self.log("PRODUCTION STREAM SCRAPER")
        self.log("=" * 70)
        self.log(f"Total URLs: {len(self.urls)}")
        self.log(f"Duration per URL: {duration_per_url}s")
        self.log(f"Output directory: {self.output_dir}")
        self.log("=" * 70)
        
        self.running = True
        self.stats['start_time'] = time.time()
        
        try:
            for url in self.urls:
                if not self.running:
                    break
                self.scrape_single(url, duration_per_url)
        finally:
            self.log("\n" + "=" * 70)
            self.log("SCRAPING COMPLETE")
            self.log("=" * 70)
            
            final_count, final_file = self.save_all()
            
            self.log(f"\nFinal Results:")
            self.log(f"  Total phones: {final_count}")
            self.log(f"  URLs processed: {self.stats['urls_processed']}")
            self.log(f"  API calls: {self.stats['api_calls']}")
            self.log(f"  Errors: {self.stats['errors']}")
            self.log(f"  Output file: {final_file}")
            
            if self.phones:
                self.log(f"\nAll Phone Numbers:")
                for phone in sorted(self.phones.keys()):
                    formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                    self.log(f"  - {formatted}")


def main():
    # Can add multiple URLs here
    urls = [
        "https://live.leisu.com/detail-4455336",
        # Add more URLs as needed
    ]
    
    scraper = ProductionScraper(urls, output_dir="./output")
    scraper.run(duration_per_url=120)  # 2 minutes per URL


if __name__ == "__main__":
    main()
