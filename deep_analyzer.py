#!/usr/bin/env python3
"""
Deep Stream Analyzer - Comprehensive page analysis
"""

import json
import time
import re
from playwright.sync_api import sync_playwright


def deep_analyze(url):
    """Deep analysis of stream page"""
    
    print("=" * 70)
    print("DEEP STREAM ANALYZER")
    print("=" * 70)
    print(f"Target: {url}")
    
    phones_found = set()
    all_texts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36'
        )
        
        page = context.new_page()
        
        # Capture all network requests
        network_log = []
        def handle_route(route, request):
            network_log.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type
            })
            route.continue_()
        
        page.route("**/*", handle_route)
        
        try:
            print("\n[Step 1] Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            print("[Step 2] Waiting for dynamic content...")
            time.sleep(10)
            
            # Get full HTML
            print("[Step 3] Analyzing HTML structure...")
            html = page.content()
            
            # Look for all text-containing elements
            print("[Step 4] Extracting all text content...")
            
            # Try different selectors
            selectors_to_try = [
                'div', 'span', 'p', 'li', 'a', 'td', 'tr',
                '[class*="chat"]', '[class*="message"]',
                '[class*="user"]', '[class*="name"]',
                '[id*="chat"]', '[id*="message"]'
            ]
            
            for selector in selectors_to_try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"  Selector '{selector}': {len(elements)} elements")
                    
                    for elem in elements[:50]:  # Limit per selector
                        try:
                            text = elem.inner_text().strip()
                            if text and len(text) < 500 and text not in all_texts:
                                all_texts.append(text)
                                
                                # Look for phone patterns
                                phones = re.findall(r'1[3-9]\d{9}', text)
                                for phone in phones:
                                    if phone not in phones_found:
                                        phones_found.add(phone)
                                        print(f"    >>> FOUND PHONE: {phone} in: {text[:80]}")
                        except:
                            pass
            
            print("\n[Step 5] Analyzing JavaScript data...")
            
            # Check if there are any data objects in window
            js_result = page.evaluate('''() => {
                const result = {};
                // Check common variable names
                const vars = ['chat', 'messages', 'comments', 'users', 'data', 
                             'room', 'stream', 'live', 'config', 'initData',
                             'userList', 'messageList', 'chatData'];
                for (const v of vars) {
                    if (window[v] !== undefined) {
                        try {
                            const str = JSON.stringify(window[v]);
                            result[v] = str.substring(0, 5000);
                        } catch(e) {
                            result[v] = String(window[v]).substring(0, 500);
                        }
                    }
                }
                return result;
            }''')
            
            print(f"  JavaScript variables found: {list(js_result.keys())}")
            
            for var_name, var_data in js_result.items():
                if var_data:
                    phones = re.findall(r'1[3-9]\d{9}', var_data)
                    for phone in phones:
                        if phone not in phones_found:
                            phones_found.add(phone)
                            print(f"    >>> FOUND PHONE in JS variable '{var_name}': {phone}")
            
            print("\n[Step 6] Checking for iframes...")
            iframes = page.query_selector_all('iframe')
            print(f"  Found {len(iframes)} iframes")
            
            for i, iframe in enumerate(iframes):
                try:
                    frame = iframe.content_frame()
                    if frame:
                        frame_text = frame.inner_text('body')
                        print(f"  IFrame {i+1} text length: {len(frame_text)}")
                        phones = re.findall(r'1[3-9]\d{9}', frame_text)
                        for phone in phones:
                            if phone not in phones_found:
                                phones_found.add(phone)
                                print(f"    >>> FOUND PHONE in iframe: {phone}")
                except:
                    pass
            
            print("\n[Step 7] Monitoring network requests...")
            api_calls = [n for n in network_log if 'api' in n['url'].lower()]
            print(f"  API calls captured: {len(api_calls)}")
            for call in api_calls[:10]:
                print(f"    - {call['method']} {call['url'][:80]}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal unique phone numbers found: {len(phones_found)}")
    if phones_found:
        for phone in sorted(phones_found):
            print(f"  - {phone}")
    else:
        print("  No phone numbers detected")
        print("\n  Possible reasons:")
        print("  1. Phone numbers are not displayed in the chat interface")
        print("  2. The data is loaded via encrypted/obfuscated channels")
        print("  3. Phone numbers are not present in this stream")
        print("  4. Login/authentication may be required to view user data")
    
    print(f"\nTotal unique text snippets collected: {len(all_texts)}")
    if all_texts:
        print("\n  Sample texts:")
        for text in all_texts[:10]:
            print(f"    - {text[:60]}...")
    
    # Save results
    with open('deep_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({
            'url': url,
            'phones_found': list(phones_found),
            'sample_texts': all_texts[:100],
            'js_variables': list(js_result.keys()) if 'js_result' in dir() else [],
            'network_calls': network_log[:50]
        }, f, ensure_ascii=False, indent=2)
    
    print("\nDetailed report saved to: deep_analysis.json")
    
    return phones_found


if __name__ == "__main__":
    url = "https://live.leisu.com/detail-4455336"
    deep_analyze(url)
