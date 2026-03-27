#!/usr/bin/env python3
"""
Multi-Stream Phone Number Scraper

A production-grade, scalable scraper for extracting phone numbers from
multiple live streams simultaneously with database persistence.

Usage:
    python -m src.multi_stream_scraper --config config/config.yaml
    python -m src.multi_stream_scraper --urls urls.txt --workers 10
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import yaml
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from database.db import Database
from scheduler.scheduler import StreamScheduler, ScrapingTask
from core.username_extractor import UsernamePhoneExtractor, BatchExtractor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('./output/scraper.log')
    ]
)
logger = logging.getLogger(__name__)


class MultiStreamScraper:
    """
    Production-grade multi-stream phone number scraper.
    
    Features:
    - Database persistence (SQLite)
    - Multi-threaded scraping
    - Rate limiting
    - Automatic retry
    - Username-based extraction
    - Real-time monitoring
    """
    
    def __init__(self, config: Dict):
        """
        Initialize multi-stream scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False
        
        # Initialize database
        db_path = config.get('database', {}).get('path', './output/scraper.db')
        self.db = Database(db_path)
        
        # Initialize scheduler
        scheduler_config = config.get('scheduler', {})
        self.scheduler = StreamScheduler(
            db=self.db,
            max_workers=scheduler_config.get('max_workers', 5),
            global_rate_limit=scheduler_config.get('rate_limit', 60),
            default_check_interval=scheduler_config.get('check_interval', 30)
        )
        
        # Initialize extractor
        self.extractor = UsernamePhoneExtractor()
        self.batch_extractor = BatchExtractor()
        
        # Browser management
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Statistics
        self.stats = {
            'streams_processed': 0,
            'phones_found': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received, stopping gracefully...")
        self.running = False
    
    def _init_browser(self):
        """Initialize browser instance."""
        browser_config = self.config.get('browser', {})
        
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=browser_config.get('headless', True),
            args=['--disable-blink-features=AutomationControlled']
        )
        
        viewport = browser_config.get('viewport', {'width': 1280, 'height': 800})
        self.context = self.browser.new_context(
            viewport=viewport,
            user_agent=browser_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        )
        
        logger.info("Browser initialized")
    
    def _close_browser(self):
        """Close browser instance."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    def scrape_stream(self, task: ScrapingTask) -> Dict:
        """
        Scrape a single stream for phone numbers.
        
        Args:
            task: ScrapingTask with stream information
            
        Returns:
            Dictionary with scraping results
        """
        result = {
            'success': False,
            'new_phones': 0,
            'total_phones': 0,
            'error': None
        }
        
        page: Optional[Page] = None
        
        try:
            # Create new page for this task
            page = self.context.new_page()
            
            # Navigate to stream
            logger.debug(f"Navigating to {task.stream_url}")
            page.goto(task.stream_url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            time.sleep(self.config.get('scraping', {}).get('initial_wait', 5))
            
            # Extract data from page
            users_data = self._extract_users_from_page(page)
            
            # Process extractions
            extraction_results = self.batch_extractor.process_with_deduplication(users_data)
            
            # Store results
            new_phones = 0
            for phone, extraction in extraction_results.items():
                is_new = self.db.add_phone(
                    phone=phone,
                    formatted=extraction.formatted,
                    stream_url=task.stream_url,
                    username=extraction.username,
                    context=extraction.context,
                    pattern_type=f"{extraction.source}_confidence_{extraction.confidence:.2f}"
                )
                
                if is_new:
                    new_phones += 1
                    logger.info(f"New phone found: {extraction.formatted} "
                              f"(from {extraction.source}, user: {extraction.username})")
            
            result['success'] = True
            result['new_phones'] = new_phones
            result['total_phones'] = len(extraction_results)
            
            logger.debug(f"Scraped {task.stream_url}: {new_phones} new phones")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error scraping {task.stream_url}: {e}")
        
        finally:
            if page:
                page.close()
        
        return result
    
    def _extract_users_from_page(self, page: Page) -> List[Dict]:
        """
        Extract user data from page.
        
        This is a generic implementation. Platform-specific extractors
        should override this for better accuracy.
        
        Args:
            page: Playwright page
            
        Returns:
            List of user dictionaries
        """
        users = []
        
        # Common selectors for comments/chat
        selectors = [
            '.comment-item',
            '.chat-item',
            '.message-item',
            '.danmu-item',
            '[class*="comment"]',
            '[class*="chat"]',
            '[class*="message"]',
            'div',  # Fallback
        ]
        
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                
                for elem in elements[:100]:  # Limit to 100 elements
                    try:
                        # Try to extract username
                        username_elem = elem.query_selector(
                            '[class*="user"], [class*="name"], .username, .nickname'
                        )
                        username = username_elem.inner_text() if username_elem else ""
                        
                        # Get comment text
                        text = elem.inner_text()
                        
                        if username or text:
                            users.append({
                                'username': username,
                                'comment': text,
                                'profile': ''
                            })
                    except:
                        continue
                
                if users:  # If we found users with this selector, stop
                    break
                    
            except:
                continue
        
        # If no structured data found, scan entire page
        if not users:
            try:
                body_text = page.inner_text('body')
                # Create a single pseudo-user for page content
                users.append({
                    'username': '',
                    'comment': body_text,
                    'profile': ''
                })
            except:
                pass
        
        return users
    
    def add_streams(self, urls: List[str], platform: str = None):
        """
        Add multiple streams to scrape.
        
        Args:
            urls: List of stream URLs
            platform: Platform identifier
        """
        for url in urls:
            self.scheduler.add_stream(url, platform)
        
        logger.info(f"Added {len(urls)} streams")
    
    def run(self):
        """
        Main execution loop.
        """
        logger.info("=" * 70)
        logger.info("MULTI-STREAM PHONE EXTRACTOR v2.0")
        logger.info("=" * 70)
        
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            # Initialize browser
            self._init_browser()
            
            # Register scraping handler with scheduler
            self.scheduler.on_task_complete = self.scrape_stream
            
            # Start scheduler
            self.scheduler.start()
            
            logger.info("Scraper running. Press Ctrl+C to stop.")
            
            # Main loop - just wait and periodically report stats
            last_report = time.time()
            report_interval = self.config.get('logging', {}).get('report_interval', 60)
            
            while self.running:
                time.sleep(1)
                
                # Periodic status report
                if time.time() - last_report >= report_interval:
                    self._print_status()
                    last_report = time.time()
            
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        
        finally:
            # Cleanup
            logger.info("Shutting down...")
            self.scheduler.stop()
            self._close_browser()
            
            # Final report
            self._print_final_report()
    
    def _print_status(self):
        """Print current status."""
        scheduler_stats = self.scheduler.get_stats()
        db_stats = self.db.get_stats()
        
        uptime = int(scheduler_stats['uptime_seconds'])
        
        logger.info("-" * 70)
        logger.info(f"Status Report (uptime: {uptime//60}m{uptime%60}s)")
        logger.info(f"  Streams: {db_stats.active_streams} active / {db_stats.total_streams} total")
        logger.info(f"  Queue: {scheduler_stats['queue_size']} tasks")
        logger.info(f"  Phones: {db_stats.total_phones} total ({db_stats.today_phones} today)")
        logger.info(f"  Tasks: {scheduler_stats['tasks_completed']} completed, "
                   f"{scheduler_stats['tasks_failed']} failed")
        logger.info(f"  Rate limit: {scheduler_stats['rate_limiter']['utilization']:.1f}% utilized")
        logger.info("-" * 70)
    
    def _print_final_report(self):
        """Print final report."""
        db_stats = self.db.get_stats()
        
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)
        print(f"Total streams tracked: {db_stats.total_streams}")
        print(f"Total phones extracted: {db_stats.total_phones}")
        print(f"Phones found today: {db_stats.today_phones}")
        
        if db_stats.top_streams:
            print("\nTop Streams by Phone Count:")
            for stream in db_stats.top_streams:
                print(f"  - {stream['url']}: {stream['phones_found']} phones")
        
        # Export results
        output_dir = Path(self.config.get('output', {}).get('directory', './output'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_path = output_dir / f"phones_export_{timestamp}.csv"
        json_path = output_dir / f"phones_export_{timestamp}.json"
        
        self.db.export_phones(str(csv_path), 'csv')
        self.db.export_phones(str(json_path), 'json')
        
        print(f"\nExported to:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")
        print("=" * 70)


def load_urls_from_file(filepath: str) -> List[str]:
    """
    Load URLs from a text file.
    
    Args:
        filepath: Path to file with one URL per line
        
    Returns:
        List of URLs
    """
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    return urls


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Multi-Stream Phone Number Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with config file
  python -m src.multi_stream_scraper --config config/config.yaml
  
  # Add URLs from file
  python -m src.multi_stream_scraper --urls streams.txt --workers 10
  
  # Add single URL
  python -m src.multi_stream_scraper --url "https://live.example.com/stream"
        """
    )
    
    parser.add_argument('--config', '-c', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--urls', '-f', help='File containing URLs (one per line)')
    parser.add_argument('--url', '-u', help='Single URL to scrape')
    parser.add_argument('--workers', '-w', type=int, default=5,
                       help='Number of concurrent workers')
    parser.add_argument('--platform', '-p', default='generic',
                       help='Platform identifier')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}, using defaults")
        config = {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config: {e}")
        sys.exit(1)
    
    # Apply command line overrides
    if args.workers:
        if 'scheduler' not in config:
            config['scheduler'] = {}
        config['scheduler']['max_workers'] = args.workers
    
    # Create scraper
    scraper = MultiStreamScraper(config)
    
    # Add URLs
    if args.urls:
        urls = load_urls_from_file(args.urls)
        scraper.add_streams(urls, args.platform)
    elif args.url:
        scraper.add_streams([args.url], args.platform)
    else:
        # Load from database (existing streams)
        pass
    
    # Run
    scraper.run()


if __name__ == '__main__':
    main()
