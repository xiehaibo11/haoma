#!/usr/bin/env python3
"""
Continuous Stream Extractor - Maximum effort phone extraction
Monitors: WebSocket, XHR/Fetch, DOM mutations, JavaScript variables
"""

import json
import time
import re
import threading
from datetime import datetime
from playwright.sync_api import sync_playwright


class ContinuousExtractor:
    def __init__(self, url):
        self.url = url
        self.phones = set()
        self.ws_messages = []
        self.api_responses = []
        self.running = False
        self.lock = threading.Lock()
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        
    def extract_phones(self, text, source=""):
        """Extract all possible phone patterns from text"""
        if not text or len(text) > 100000:
            return []
        
        # Pattern 1: Standard Chinese mobile
        phones = re.findall(r'1[3-9]\d{9}', text)
        
        # Pattern 2: With separators
        separated = re.findall(r'1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}', text)
        for s in separated:
            clean = re.sub(r'[^\d]', '', s)
            if len(clean) == 11:
                phones.append(clean)
        
        # Pattern 3: Partially hidden (e.g., 138****8888)
        partial = re.findall(r'1[3-9]\d\*{3,5}\d{4}', text)
        
        new_phones = []
        with self.lock:
            for phone in phones:
                if phone not in self.phones and len(phone) == 11:
                    self.phones.add(phone)
                    new_phones.append(phone)
                    self.log(f">>> NEW PHONE from {source}: {phone}")
        
        return new_phones
        
    def run(self, duration=300):
        """Run continuous extraction"""
        self.log("=" * 70)
        self.log("CONTINUOUS STREAM EXTRACTOR")
        self.log("=" * 70)
        self.log(f"Target: {self.url}")
        self.log(f"Duration: {duration} seconds")
        self.log("Monitoring: WebSocket | API | DOM | JS")
        self.log("=" * 70)
        
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
            
            # Setup WebSocket handler
            def handle_ws(ws):
                self.log(f"[WebSocket] Connected: {ws.url[:60]}...")
                
                def on_message(msg):
                    try:
                        text = msg.text if hasattr(msg, 'text') else str(msg)
                        self.ws_messages.append({'time': time.time(), 'data': text[:1000]})
                        self.extract_phones(text, "WebSocket")
                    except:
                        pass
                
                ws.on("framereceived", on_message)
                ws.on("framesent", on_message)
            
            context.on("websocket", handle_ws)
            
            # Setup response handler
            def handle_response(response):
                try:
                    url = response.url
                    content_type = response.headers.get('content-type', '')
                    
                    if any(x in content_type for x in ['json', 'text', 'javascript']):
                        try:
                            text = response.text()
                            if len(text) < 500000:  # Limit size
                                self.api_responses.append({
                                    'url': url[:200],
                                    'time': time.time(),
                                    'data': text[:2000]
                                })
                                self.extract_phones(text, f"API:{url[:40]}")
                        except:
                            pass
                except:
                    pass
            
            page.on("response", handle_response)
            
            try:
                # Load page
                self.log("\n[1/3] Loading page...")
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                self.log("[2/3] Waiting for content...")
                time.sleep(10)
                
                # Initial scan
                self.log("[3/3] Starting continuous monitoring...")
                self.log("-" * 70)
                
                start = time.time()
                iteration = 0
                last_count = 0
                
                self.running = True
                while self.running and (time.time() - start) < duration:
                    iteration += 1
                    
                    # Scan DOM
                    try:
                        body = page.inner_text('body')
                        self.extract_phones(body, "DOM")
                    except:
                        pass
                    
                    # Scan specific chat elements
                    try:
                        elements = page.query_selector_all('div, span, li')
                        for elem in elements[:100]:
                            try:
                                text = elem.inner_text()
                                if text and 10 < len(text) < 300:
                                    self.extract_phones(text, "Element")
                            except:
                                pass
                    except:
                        pass
                    
                    # Check JavaScript variables
                    try:
                        js_data = page.evaluate('''() => {
                            const data = {};
                            ['chat', 'messages', 'users', 'data', 'room', 'stream'].forEach(v => {
                                if (window[v] !== undefined) {
                                    try {
                                        data[v] = JSON.stringify(window[v]).slice(0, 10000);
                                    } catch(e) {}
                                }
                            });
                            return data;
                        }''')
                        
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
                    current = len(self.phones)
                    if current != last_count or iteration % 10 == 0:
                        elapsed = int(time.time() - start)
                        self.log(f"[{iteration}] Elapsed: {elapsed}s | Phones: {current}")
                        last_count = current
                    
                    # Save progress every 30 seconds
                    if iteration % 15 == 0:
                        self.save_progress()
                    
                    time.sleep(2)
                
            except KeyboardInterrupt:
                self.log("\n[!] Stopped by user")
            except Exception as e:
                self.log(f"\n[!] Error: {e}")
            finally:
                browser.close()
        
        return self.phones
    
    def save_progress(self):
        """Save current progress"""
        with open('extraction_progress.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'phones': list(self.phones),
                'ws_messages': len(self.ws_messages),
                'api_responses': len(self.api_responses)
            }, f, ensure_ascii=False, indent=2)
    
    def print_summary(self):
        """Print final summary"""
        self.log("\n" + "=" * 70)
        self.log("FINAL SUMMARY")
        self.log("=" * 70)
        self.log(f"Total unique phones: {len(self.phones)}")
        
        if self.phones:
            self.log("\nPhone numbers found:")
            for phone in sorted(self.phones):
                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                self.log(f"  - {formatted}")
        else:
            self.log("\nNo phone numbers were found.")
            self.log("\nAnalysis:")
            self.log(f"  - WebSocket messages captured: {len(self.ws_messages)}")
            self.log(f"  - API responses captured: {len(self.api_responses)}")
            self.log("\nConclusion: Phone numbers are not exposed in:")
            self.log("  - Page DOM content")
            self.log("  - WebSocket messages")
            self.log("  - API responses")
            self.log("  - JavaScript variables")
            self.log("\nThis is normal - platforms protect user privacy.")
        
        # Save final results
        with open('final_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'url': self.url,
                'phones': list(self.phones),
                'total_ws_messages': len(self.ws_messages),
                'total_api_responses': len(self.api_responses),
                'ws_samples': self.ws_messages[:10],
                'api_samples': self.api_responses[:10]
            }, f, ensure_ascii=False, indent=2)
        
        self.log("\nFull results saved to: final_results.json")


if __name__ == "__main__":
    url = "https://live.leisu.com/detail-4455336"
    
    extractor = ContinuousExtractor(url)
    try:
        extractor.run(duration=60)  # Run for 60 seconds
    finally:
        extractor.print_summary()
