#!/usr/bin/env python3
"""
Diagnostic tool to trace extraction issues.
"""

import sys
import time
from playwright.sync_api import sync_playwright


def diagnose():
    """Run diagnostics."""
    print("=" * 70)
    print("DIAGNOSTIC TOOL")
    print("=" * 70)
    print()
    
    url = "https://live.leisu.com/detail-4244416"
    
    print(f"1. Testing URL: {url}")
    print()
    
    try:
        with sync_playwright() as p:
            print("2. Launching browser...")
            browser = p.chromium.launch(headless=True)
            
            print("3. Creating context...")
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            print("4. Opening page...")
            page = context.new_page()
            
            print(f"5. Navigating to {url}...")
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                print("   ✓ Page loaded")
            except Exception as e:
                print(f"   ✗ Timeout: {e}")
                print("   Continuing anyway...")
            
            print("6. Waiting for content...")
            time.sleep(10)
            
            print("7. Checking page title...")
            title = page.title()
            print(f"   Title: {title}")
            
            print("8. Looking for comment elements...")
            selectors = [
                '.comment-item',
                '.chat-item', 
                '.message-item',
                '[class*="comment"]',
                '[class*="chat"]',
                'div'  # fallback
            ]
            
            found = False
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"   ✓ Found {len(elements)} elements with '{selector}'")
                        
                        # Try to extract text from first few
                        for i, elem in enumerate(elements[:3]):
                            try:
                                text = elem.inner_text()
                                if text and len(text) < 200:
                                    print(f"      [{i+1}] {text[:80]}...")
                            except:
                                pass
                        
                        if len(elements) > 0:
                            found = True
                            break
                except Exception as e:
                    print(f"   ✗ Error with {selector}: {e}")
            
            if not found:
                print("   ✗ No comment elements found")
            
            print()
            print("9. Scanning for phone numbers in page...")
            import re
            body_text = page.inner_text('body')
            phones = re.findall(r'1[3-9]\d{9}', body_text)
            
            if phones:
                print(f"   ✓ Found {len(phones)} phone patterns")
                for phone in set(phones)[:5]:
                    print(f"      - {phone}")
            else:
                print("   ✗ No phone patterns found")
            
            print()
            print("10. Closing browser...")
            browser.close()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    diagnose()
    input("\nPress Enter to exit...")
