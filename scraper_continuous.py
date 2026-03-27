#!/usr/bin/env python3
"""
Continuous Live Stream Phone Number Scraper
Runs until stopped, saves all phone numbers
"""

import re
import time
import json
import csv
from datetime import datetime
from playwright.sync_api import sync_playwright

class ContinuousScraper:
    def __init__(self, url):
        self.url = url
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        self.phones_found = {}
        self.session_start = datetime.now().isoformat()
        
    def extract_phones(self, text):
        if not text:
            return []
        phones = self.phone_pattern.findall(text)
        return [p for p in phones if len(p) == 11]
    
    def format_phone(self, phone):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    
    def save_to_csv(self, phone, context=""):
        """Append to CSV file immediately when found"""
        with open('phones_live.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                phone,
                self.format_phone(phone),
                context[:100] if context else ""
            ])
    
    def run(self):
        print("=" * 70)
        print("CONTINUOUS LIVE STREAM PHONE SCRAPER")
        print("=" * 70)
        print(f"Target: {self.url}")
        print("Press Ctrl+C to stop")
        print("=" * 70)
        
        # Initialize CSV
        with open('phones_live.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'phone_raw', 'phone_formatted', 'context'])
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                print("\n[1/3] Loading page...")
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                time.sleep(5)
                
                print("[2/3] Scrolling to load comments...")
                for _ in range(5):
                    page.evaluate('window.scrollBy(0, 1000)')
                    time.sleep(1)
                
                print("[3/3] Starting continuous monitoring...\n")
                print("-" * 70)
                print(f"{'Time':<12} {'Phone Number':<20} {'Status':<15} {'Total'}")
                print("-" * 70)
                
                iteration = 0
                last_summary = time.time()
                
                while True:
                    iteration += 1
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Scan entire page
                    try:
                        page_text = page.inner_text('body')
                        phones = self.extract_phones(page_text)
                        
                        for phone in phones:
                            if phone not in self.phones_found:
                                self.phones_found[phone] = {
                                    'first_seen': datetime.now().isoformat(),
                                    'count': 1
                                }
                                formatted = self.format_phone(phone)
                                print(f"{current_time:<12} {formatted:<20} {'NEW FOUND!':<15} {len(self.phones_found)}")
                                self.save_to_csv(phone)
                            else:
                                self.phones_found[phone]['count'] += 1
                    except:
                        pass
                    
                    # Scan individual elements for context
                    try:
                        elements = page.query_selector_all('div, span, p, li')
                        for elem in elements[:100]:  # Limit to first 100 elements
                            try:
                                text = elem.inner_text()
                                if text and 10 < len(text) < 200:
                                    phones = self.extract_phones(text)
                                    for phone in phones:
                                        if phone not in self.phones_found:
                                            self.phones_found[phone] = {
                                                'first_seen': datetime.now().isoformat(),
                                                'count': 1,
                                                'context': text.strip()
                                            }
                                            formatted = self.format_phone(phone)
                                            context_preview = text.strip()[:40] + "..."
                                            print(f"{current_time:<12} {formatted:<20} {'NEW FOUND!':<15} {len(self.phones_found)}")
                                            print(f"            Context: {context_preview}")
                                            self.save_to_csv(phone, text.strip())
                            except:
                                continue
                    except:
                        pass
                    
                    # Periodic scrolling
                    if iteration % 3 == 0:
                        try:
                            page.evaluate('window.scrollBy(0, 800)')
                            page.evaluate('window.scrollBy(0, -400)')  # Scroll back up
                        except:
                            pass
                    
                    # Summary every 30 seconds
                    if time.time() - last_summary >= 30:
                        print(f"\n[{current_time}] Summary: {len(self.phones_found)} unique phones found so far\n")
                        last_summary = time.time()
                        # Save JSON backup
                        with open('phones_backup.json', 'w', encoding='utf-8') as f:
                            json.dump(self.phones_found, f, ensure_ascii=False, indent=2)
                    
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\n\n[!] Stopped by user")
            except Exception as e:
                print(f"\n[!] Error: {e}")
            finally:
                browser.close()
        
        return self.phones_found
    
    def final_report(self):
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)
        print(f"Session started: {self.session_start}")
        print(f"Session ended:   {datetime.now().isoformat()}")
        print(f"Total unique phone numbers found: {len(self.phones_found)}")
        
        if self.phones_found:
            print("\nAll Phone Numbers:")
            print("-" * 70)
            print(f"{'#':<4} {'Phone Number':<20} {'First Seen':<25} {'Count'}")
            print("-" * 70)
            for i, (phone, data) in enumerate(sorted(self.phones_found.items()), 1):
                first_seen = data['first_seen'][:19].replace('T', ' ')
                print(f"{i:<4} {data['formatted']:<20} {first_seen:<25} {data['count']}")
            print("-" * 70)
            
            # Save final results
            with open('phones_final.json', 'w', encoding='utf-8') as f:
                json.dump(self.phones_found, f, ensure_ascii=False, indent=2)
            
            # Save simple text list
            with open('phones_list.txt', 'w', encoding='utf-8') as f:
                for phone, data in sorted(self.phones_found.items()):
                    f.write(f"{data['formatted']}\n")
            
            print(f"\nFiles saved:")
            print(f"  - phones_live.csv (all findings with timestamps)")
            print(f"  - phones_final.json (complete data)")
            print(f"  - phones_list.txt (simple list)")

def main():
    url = "https://live.leisu.com/detail-4244416"
    scraper = ContinuousScraper(url)
    
    try:
        scraper.run()
    finally:
        scraper.final_report()

if __name__ == "__main__":
    main()
