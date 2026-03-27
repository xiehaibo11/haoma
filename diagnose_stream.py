#!/usr/bin/env python3
"""
Stream Diagnostic Tool - Analyze page structure and data sources
"""

import json
import time
from playwright.sync_api import sync_playwright


def analyze_stream(url, duration=30):
    """Analyze live stream page for extractable data"""
    
    print("=" * 70)
    print("STREAM DIAGNOSTIC TOOL")
    print("=" * 70)
    print(f"Target URL: {url}")
    print(f"Analysis duration: {duration} seconds")
    print("=" * 70)
    
    findings = {
        'phone_numbers': set(),
        'usernames': [],
        'user_ids': [],
        'api_endpoints': set(),
        'websocket_urls': set(),
        'page_structure': {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Intercept network requests
        def handle_route(route, request):
            url = request.url
            if 'api' in url or 'ws' in url or 'socket' in url:
                findings['api_endpoints'].add(url)
            route.continue_()
        
        page = context.new_page()
        page.route("**/*", handle_route)
        
        # Intercept WebSocket
        def handle_ws(ws):
            print(f"\n[WebSocket] Connected: {ws.url}")
            findings['websocket_urls'].add(ws.url)
            
            ws.on("framereceived", lambda frame: print(f"[WS Received] {frame.text[:200]}..." if hasattr(frame, 'text') else "[binary]"))
            ws.on("framesent", lambda frame: print(f"[WS Sent] {frame.text[:200]}..." if hasattr(frame, 'text') else "[binary]"))
        
        context.on("websocket", handle_ws)
        
        try:
            print("\n[1/4] Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            print("[2/4] Waiting for content to load...")
            time.sleep(5)
            
            print("[3/4] Analyzing page structure...")
            
            # Get page title and basic info
            title = page.title()
            print(f"\nPage Title: {title}")
            
            # Check for chat elements
            chat_selectors = [
                '.chat-item', '.message-item', '.comment-item', '.danmu-item',
                '[class*="chat"]', '[class*="message"]', '[class*="comment"]',
                '.user-name', '.username', '.nickname'
            ]
            
            for selector in chat_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"\nFound {len(elements)} elements with selector: {selector}")
                    findings['page_structure'][selector] = len(elements)
                    
                    # Sample first few elements
                    for i, elem in enumerate(elements[:5]):
                        try:
                            text = elem.inner_text()
                            if text:
                                print(f"  [{i+1}] {text[:100]}")
                                
                                # Look for phone numbers in the text
                                import re
                                phones = re.findall(r'1[3-9]\d{9}', text)
                                for phone in phones:
                                    findings['phone_numbers'].add(phone)
                                    print(f"      >>> PHONE FOUND: {phone}")
                        except:
                            pass
            
            # Extract all visible text
            print("\n[4/4] Scanning all page text for phone numbers...")
            body_text = page.inner_text('body')
            
            import re
            
            # Find phone numbers
            phones = re.findall(r'1[3-9]\d{9}', body_text)
            findings['phone_numbers'].update(phones)
            
            # Find usernames (patterns like "用户xxxxx" or similar)
            usernames = re.findall(r'用户[a-zA-Z0-9]+', body_text)
            findings['usernames'] = list(set(usernames))[:20]
            
            # Check for user IDs or similar patterns
            user_ids = re.findall(r'ID[：:]?\s*(\d+)', body_text)
            findings['user_ids'] = user_ids[:20]
            
            # Monitor for a short period
            print(f"\n[5/5] Monitoring for {duration} seconds...")
            start = time.time()
            iteration = 0
            
            while time.time() - start < duration:
                iteration += 1
                
                # Scroll to trigger new content
                if iteration % 3 == 0:
                    page.evaluate('window.scrollBy(0, 500)')
                
                # Re-scan for phones
                body_text = page.inner_text('body')
                phones = re.findall(r'1[3-9]\d{9}', body_text)
                new_phones = set(phones) - findings['phone_numbers']
                
                if new_phones:
                    print(f"\n[{iteration}] New phones found: {new_phones}")
                    findings['phone_numbers'].update(new_phones)
                
                if iteration % 5 == 0:
                    print(f"[{iteration}] Monitoring... Phones found so far: {len(findings['phone_numbers'])}")
                
                time.sleep(2)
            
        except Exception as e:
            print(f"\nError during analysis: {e}")
        
        finally:
            browser.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n📞 Phone Numbers Found: {len(findings['phone_numbers'])}")
    if findings['phone_numbers']:
        for phone in sorted(findings['phone_numbers']):
            print(f"   - {phone}")
    else:
        print("   No phone numbers detected in page content")
    
    print(f"\n👤 Usernames Sample ({len(findings['usernames'])} total):")
    for name in findings['usernames'][:10]:
        print(f"   - {name}")
    
    print(f"\n🔗 API/WebSocket Endpoints ({len(findings['api_endpoints'])}):")
    for endpoint in findings['api_endpoints']:
        print(f"   - {endpoint[:80]}...")
    
    print(f"\n📄 Page Structure:")
    for selector, count in findings['page_structure'].items():
        print(f"   - {selector}: {count} elements")
    
    # Save report
    report_file = 'stream_diagnosis.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'url': url,
            'phone_numbers': list(findings['phone_numbers']),
            'usernames': findings['usernames'],
            'user_ids': findings['user_ids'],
            'api_endpoints': list(findings['api_endpoints']),
            'websocket_urls': list(findings['websocket_urls']),
            'page_structure': findings['page_structure']
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Full report saved to: {report_file}")
    
    return findings


if __name__ == "__main__":
    url = "https://live.leisu.com/detail-4455336"
    analyze_stream(url, duration=30)
