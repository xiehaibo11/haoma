#!/usr/bin/env python3
"""
LiveStream Phone Extractor - Main Scraper Module

This is the main entry point for the live stream phone number extraction tool.
It orchestrates browser automation, phone extraction, and result output.
"""

import argparse
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import yaml
from playwright.sync_api import sync_playwright, Page

from .extractor import PhoneExtractor
from .writer import OutputWriter


class LiveStreamScraper:
    """
    Main scraper class that handles browser automation and phone extraction.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the scraper with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.target_url = config['target']['url']
        self.scraping_config = config.get('scraping', {})
        self.browser_config = config.get('browser', {})
        self.output_config = config.get('output', {})
        self.logging_config = config.get('logging', {})
        
        # Initialize components
        self.extractor = PhoneExtractor(config.get('phone_patterns', []))
        self.writer = OutputWriter(self.output_config)
        
        # State tracking
        self.phones_found: Dict[str, Dict] = {}
        self.iteration = 0
        self.start_time: Optional[float] = None
        self.running = False
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'phones_found': 0,
            'errors': 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n\n[!] Shutdown signal received, saving progress...")
        self.running = False
    
    def log(self, message: str, level: str = "INFO"):
        """
        Log a message if level is appropriate.
        
        Args:
            message: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        config_level = self.logging_config.get('level', "INFO")
        
        if levels.index(level) >= levels.index(config_level):
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def scan_page(self, page: Page) -> int:
        """
        Scan the page for phone numbers.
        
        Args:
            page: Playwright page object
            
        Returns:
            Number of new phones found
        """
        new_count = 0
        max_elements = self.scraping_config.get('max_elements', 100)
        include_context = self.output_config.get('include_context', True)
        
        # Scan entire page body
        try:
            page_text = page.inner_text('body')
            phones = self.extractor.extract(page_text)
            
            for phone in phones:
                if phone.raw not in self.phones_found:
                    self.phones_found[phone.raw] = {
                        'formatted': phone.formatted,
                        'first_seen': datetime.now().isoformat(),
                        'pattern_name': phone.pattern_name,
                        'count': 1
                    }
                    new_count += 1
                    self._on_new_phone(phone)
                else:
                    self.phones_found[phone.raw]['count'] += 1
        except Exception as e:
            self.log(f"Error scanning page body: {e}", "ERROR")
            self.stats['errors'] += 1
        
        # Scan individual elements for context
        if include_context:
            try:
                elements = page.query_selector_all('div, span, p, li, td')
                
                for i, elem in enumerate(elements):
                    if i >= max_elements:
                        break
                    
                    try:
                        text = elem.inner_text()
                        if text and 10 < len(text) < 300:
                            phones = self.extractor.extract(text, context=text.strip())
                            
                            for phone in phones:
                                if phone.raw not in self.phones_found:
                                    self.phones_found[phone.raw] = {
                                        'formatted': phone.formatted,
                                        'first_seen': datetime.now().isoformat(),
                                        'pattern_name': phone.pattern_name,
                                        'context': phone.context,
                                        'count': 1
                                    }
                                    new_count += 1
                                    self._on_new_phone(phone, context=text.strip())
                                else:
                                    self.phones_found[phone.raw]['count'] += 1
                    except:
                        continue
            except Exception as e:
                self.log(f"Error scanning elements: {e}", "ERROR")
        
        return new_count
    
    def _on_new_phone(self, phone, context: str = None):
        """
        Handle newly found phone number.
        
        Args:
            phone: PhoneNumber object
            context: Optional context text
        """
        self.stats['phones_found'] += 1
        
        # Real-time output
        total = len(self.phones_found)
        msg = f"NEW PHONE: {phone.formatted} (Total: {total})"
        self.log(msg, "INFO")
        
        if context:
            preview = context[:80].replace('\n', ' ')
            self.log(f"  Context: {preview}...", "DEBUG")
        
        # Append to CSV for real-time logging
        self.writer.append_single(phone.raw, self.phones_found[phone.raw])
    
    def scroll_page(self, page: Page):
        """
        Scroll the page to load more content.
        
        Args:
            page: Playwright page object
        """
        try:
            scroll_amount = self.scraping_config.get('scroll_amount', 800)
            page.evaluate(f'window.scrollBy(0, {scroll_amount})')
        except Exception as e:
            self.log(f"Error scrolling: {e}", "WARNING")
    
    def print_progress(self):
        """Print periodic progress update."""
        elapsed = int(time.time() - self.start_time)
        duration = self.scraping_config.get('duration', 0)
        
        if duration > 0:
            remaining = duration - elapsed
            progress_msg = f"Elapsed: {elapsed//60}m{elapsed%60}s | Remaining: {remaining//60}m{remaining%60}s"
        else:
            progress_msg = f"Elapsed: {elapsed//60}m{elapsed%60}s"
        
        self.log(f"[{self.iteration}] {progress_msg} | Phones: {len(self.phones_found)} | Errors: {self.stats['errors']}")
    
    def print_summary(self):
        """Print final summary report."""
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"Target URL:        {self.target_url}")
        print(f"Duration:          {int(time.time() - self.start_time)} seconds")
        print(f"Total Checks:      {self.stats['total_checks']}")
        print(f"Phones Found:      {len(self.phones_found)}")
        print(f"Errors:            {self.stats['errors']}")
        
        if self.phones_found:
            print("\nPhone Numbers:")
            print("-" * 70)
            for i, (phone, data) in enumerate(sorted(self.phones_found.items()), 1):
                first_seen = data['first_seen'][:19].replace('T', ' ')
                print(f"  {i}. {data['formatted']} (seen {data['count']} times, first: {first_seen})")
        
        print("-" * 70)
        print("\nOutput Files:")
        for format_type, path in self.writer.get_output_paths().items():
            print(f"  - {format_type.upper()}: {path}")
    
    def run(self):
        """
        Main execution loop.
        
        Returns:
            Dictionary of found phones
        """
        duration = self.scraping_config.get('duration', 300)
        check_interval = self.scraping_config.get('check_interval', 2)
        scroll_interval = self.scraping_config.get('scroll_interval', 5)
        initial_wait = self.scraping_config.get('initial_wait', 5)
        progress_interval = self.logging_config.get('progress_interval', 30)
        backup_interval = self.config.get('advanced', {}).get('backup_interval', 60)
        
        # Print startup banner
        print("=" * 70)
        print("LIVESTREAM PHONE EXTRACTOR v1.0")
        print("=" * 70)
        print(f"Target:    {self.target_url}")
        print(f"Duration:  {duration if duration > 0 else 'Infinite (Ctrl+C to stop)'} seconds")
        print(f"Interval:  {check_interval}s")
        print("-" * 70)
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")
        
        self.running = True
        self.start_time = time.time()
        last_progress = self.start_time
        last_backup = self.start_time
        
        with sync_playwright() as p:
            # Launch browser
            headless = self.browser_config.get('headless', True)
            browser = p.chromium.launch(headless=headless)
            
            # Create context with viewport
            viewport = self.browser_config.get('viewport', {'width': 1280, 'height': 800})
            context = browser.new_context(
                viewport=viewport,
                user_agent=self.config['target'].get('headers', {}).get('User-Agent')
            )
            
            page = context.new_page()
            
            try:
                # Navigate to target
                self.log("Loading target page...")
                timeout = self.config.get('advanced', {}).get('timeout', 30) * 1000
                page.goto(self.target_url, wait_until='networkidle', timeout=timeout)
                
                # Initial wait and scroll
                self.log(f"Waiting {initial_wait}s for content to load...")
                time.sleep(initial_wait)
                
                self.log("Performing initial scroll...")
                for _ in range(3):
                    self.scroll_page(page)
                    time.sleep(1)
                
                self.log("Starting extraction loop...")
                print("-" * 70)
                
                # Main loop
                while self.running:
                    self.iteration += 1
                    self.stats['total_checks'] += 1
                    
                    # Scan for phones
                    self.scan_page(page)
                    
                    # Scroll periodically
                    if self.iteration % scroll_interval == 0:
                        self.scroll_page(page)
                    
                    # Progress update
                    current_time = time.time()
                    if current_time - last_progress >= progress_interval:
                        self.print_progress()
                        last_progress = current_time
                    
                    # Backup
                    if current_time - last_backup >= backup_interval:
                        self.writer.save_backup(self.phones_found)
                        last_backup = current_time
                    
                    # Check duration
                    if duration > 0 and (current_time - self.start_time) >= duration:
                        self.log("Duration reached, stopping...")
                        break
                    
                    # Sleep before next check
                    time.sleep(check_interval)
                
            except Exception as e:
                self.log(f"Fatal error: {e}", "ERROR")
                self.stats['errors'] += 1
            
            finally:
                # Cleanup
                self.log("Closing browser...")
                browser.close()
                
                # Final save
                self.log("Saving final results...")
                self.writer.write_all(self.phones_found)
                self.writer.save_backup(self.phones_found)
                
                # Print summary
                self.print_summary()
        
        return self.phones_found


def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='LiveStream Phone Extractor - Extract phone numbers from live stream comments'
    )
    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--url', '-u',
        help='Target URL (overrides config)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='Duration in seconds (overrides config, 0=infinite)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output directory (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config: {e}")
        sys.exit(1)
    
    # Apply command line overrides
    if args.url:
        config['target']['url'] = args.url
    if args.duration is not None:
        config['scraping']['duration'] = args.duration
    if args.output:
        config['output']['directory'] = args.output
    
    # Validate required config
    if not config.get('target', {}).get('url'):
        print("Error: No target URL specified")
        sys.exit(1)
    
    # Run scraper
    scraper = LiveStreamScraper(config)
    results = scraper.run()
    
    # Exit with appropriate code
    sys.exit(0 if len(results) > 0 else 1)


if __name__ == '__main__':
    main()
