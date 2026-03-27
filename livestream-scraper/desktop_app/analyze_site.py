#!/usr/bin/env python3
"""
Analyze leisu.com website structure to find where comments are.
"""

from playwright.sync_api import sync_playwright
import time
import re

url = 'https://live.leisu.com/detail-4336493'

def analyze():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        print(f'Loading {url}...')
        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(10)
        
        title = page.title()
        print(f'\nPage title: {title}')
        
        # Check iframes
        iframes = page.query_selector_all('iframe')
        print(f'\n=== Found {len(iframes)} iframes ===')
        
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src') or iframe.get_attribute('data-src') or 'no src'
                print(f'\nIframe {i+1}: {src[:80]}')
                
                frame = iframe.content_frame()
                if frame:
                    print('  Frame accessible: YES')
                    
                    # Look for chat in iframe
                    selectors = ['.chat-list', '.comment-list', '.message-list', 
                                '.danmu', '.bullet', '.screen']
                    
                    for sel in selectors:
                        try:
                            elements = frame.query_selector_all(sel)
                            if len(elements) > 0:
                                print(f'  Found {sel}: {len(elements)} elements')
                                text = elements[0].inner_text()
                                if text.strip():
                                    print(f'    Sample: {text.strip()[:60]}')
                        except:
                            pass
                    
                    # Check for phones
                    try:
                        body = frame.inner_text('body')
                        phones = re.findall(r'1[3-9]\d{9}', body)
                        if phones:
                            print(f'  Phones in iframe: {len(phones)}')
                    except:
                        pass
                else:
                    print('  Frame accessible: NO (cross-origin)')
            except Exception as e:
                print(f'  Error: {e}')
        
        # Check main page for any chat elements
        print('\n=== Checking main page ===')
        selectors = ['.chat', '.comment', '.message', '.danmu', 
                    '[class*=chat]', '[class*=comment]']
        
        for sel in selectors:
            try:
                elements = page.query_selector_all(sel)
                if len(elements) > 0:
                    print(f'{sel}: {len(elements)} elements')
            except:
                pass
        
        # Check network activity
        print('\n=== Analyzing page source ===')
        source = page.content()
        
        # Look for websocket
        ws_urls = re.findall(r'wss?://[^\s"\'<>]+', source)
        if ws_urls:
            print(f'WebSocket URLs: {ws_urls[:3]}')
        
        # Look for chat-related URLs
        chat_urls = re.findall(r'https?://[^\s"\'<>]*(?:chat|comment|danmu)[^\s"\'<>]*', source)
        if chat_urls:
            print(f'Chat API URLs: {list(set(chat_urls))[:3]}')
        
        # Look for data attributes
        print('\n=== Looking for data attributes ===')
        elements_with_data = page.query_selector_all('[data-*]')
        print(f'Elements with data-* attributes: {len(elements_with_data)}')
        
        browser.close()
        print('\nAnalysis complete.')

if __name__ == '__main__':
    analyze()
