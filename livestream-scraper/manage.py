#!/usr/bin/env python3
"""
Management CLI for the Multi-Stream Scraper.

Provides commands for:
- Viewing statistics
- Managing streams (add, remove, pause, resume)
- Exporting data
- Cleaning up old data
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from tabulate import tabulate

from src.database.db import Database


def cmd_stats(args):
    """Show database statistics."""
    db = Database(args.db)
    stats = db.get_stats()
    
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    
    print(f"\nTotal phone numbers: {stats.total_phones}")
    print(f"Total streams: {stats.total_streams}")
    print(f"Active streams: {stats.active_streams}")
    print(f"Phones found today: {stats.today_phones}")
    
    if stats.top_streams:
        print("\nTop Streams:")
        table = [[s['url'][:50], s['phones_found'], s['status']] 
                for s in stats.top_streams]
        print(tabulate(table, headers=['URL', 'Phones', 'Status'], tablefmt='grid'))
    
    print()


def cmd_streams(args):
    """List all streams."""
    db = Database(args.db)
    
    with db.session() as s:
        from src.database.db import StreamRecord
        streams = s.query(StreamRecord).order_by(StreamRecord.phones_found.desc()).all()
        
        print("\n" + "=" * 70)
        print("ALL STREAMS")
        print("=" * 70 + "\n")
        
        if not streams:
            print("No streams found.")
            return
        
        table = []
        for stream in streams:
            table.append([
                stream.id,
                stream.url[:40] + "..." if len(stream.url) > 40 else stream.url,
                stream.platform or "N/A",
                stream.status,
                stream.phones_found,
                stream.last_check.strftime('%Y-%m-%d %H:%M') if stream.last_check else 'Never'
            ])
        
        print(tabulate(table, 
                      headers=['ID', 'URL', 'Platform', 'Status', 'Phones', 'Last Check'],
                      tablefmt='grid'))
        print()


def cmd_phones(args):
    """List extracted phone numbers."""
    db = Database(args.db)
    
    with db.session() as s:
        from src.database.db import PhoneRecord
        
        query = s.query(PhoneRecord)
        
        if args.stream:
            query = query.filter(PhoneRecord.source_stream == args.stream)
        
        if args.today:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(PhoneRecord.first_seen >= today)
        
        query = query.order_by(PhoneRecord.first_seen.desc())
        
        if args.limit:
            query = query.limit(args.limit)
        
        phones = query.all()
        
        print("\n" + "=" * 70)
        print("EXTRACTED PHONE NUMBERS")
        print("=" * 70 + "\n")
        
        if not phones:
            print("No phones found.")
            return
        
        table = []
        for phone in phones:
            table.append([
                phone.formatted_number or phone.phone_number,
                phone.username or "N/A",
                phone.source_stream[:30] + "..." if len(phone.source_stream) > 30 else phone.source_stream,
                phone.first_seen.strftime('%Y-%m-%d %H:%M'),
                phone.occurrence_count
            ])
        
        print(tabulate(table,
                      headers=['Phone', 'Username', 'Stream', 'First Seen', 'Count'],
                      tablefmt='grid'))
        print()


def cmd_add_stream(args):
    """Add a new stream."""
    db = Database(args.db)
    
    added = db.add_stream(
        url=args.url,
        platform=args.platform,
        priority=args.priority,
        check_interval=args.interval
    )
    
    if added:
        print(f"✓ Added stream: {args.url}")
    else:
        print(f"✗ Stream already exists: {args.url}")


def cmd_pause_stream(args):
    """Pause a stream."""
    db = Database(args.db)
    db.update_stream_status(args.url, 'paused')
    print(f"✓ Paused stream: {args.url}")


def cmd_resume_stream(args):
    """Resume a stream."""
    db = Database(args.db)
    db.update_stream_status(args.url, 'active')
    print(f"✓ Resumed stream: {args.url}")


def cmd_export(args):
    """Export phone numbers."""
    db = Database(args.db)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.format == 'csv':
        filepath = args.output or f"phones_export_{timestamp}.csv"
        db.export_phones(filepath, 'csv')
    else:
        filepath = args.output or f"phones_export_{timestamp}.json"
        db.export_phones(filepath, 'json')
    
    print(f"✓ Exported to: {filepath}")


def cmd_cleanup(args):
    """Clean up old data."""
    db = Database(args.db)
    
    print(f"Cleaning up logs older than {args.days} days...")
    db.cleanup_old_records(args.days)
    print("✓ Cleanup complete")


def cmd_run(args):
    """Run the scraper."""
    from src.multi_stream_scraper import MultiStreamScraper, load_urls_from_file
    
    # Load config
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}
    
    # Override with CLI args
    if args.workers:
        config.setdefault('scheduler', {})['max_workers'] = args.workers
    
    # Create scraper
    scraper = MultiStreamScraper(config)
    
    # Add URLs
    if args.urls:
        urls = load_urls_from_file(args.urls)
        scraper.add_streams(urls, args.platform)
    elif args.url:
        scraper.add_streams([args.url], args.platform)
    
    # Run
    scraper.run()


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Stream Scraper Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--db', default='./output/scraper.db',
                       help='Path to database file')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Streams command
    streams_parser = subparsers.add_parser('streams', help='List all streams')
    streams_parser.set_defaults(func=cmd_streams)
    
    # Phones command
    phones_parser = subparsers.add_parser('phones', help='List phone numbers')
    phones_parser.add_argument('--stream', help='Filter by stream URL')
    phones_parser.add_argument('--today', action='store_true', help='Show only today')
    phones_parser.add_argument('--limit', type=int, help='Limit results')
    phones_parser.set_defaults(func=cmd_phones)
    
    # Add stream command
    add_parser = subparsers.add_parser('add', help='Add a stream')
    add_parser.add_argument('url', help='Stream URL')
    add_parser.add_argument('--platform', default='generic', help='Platform name')
    add_parser.add_argument('--priority', type=int, default=5, help='Priority (1-10)')
    add_parser.add_argument('--interval', type=int, default=30, help='Check interval (seconds)')
    add_parser.set_defaults(func=cmd_add_stream)
    
    # Pause command
    pause_parser = subparsers.add_parser('pause', help='Pause a stream')
    pause_parser.add_argument('url', help='Stream URL')
    pause_parser.set_defaults(func=cmd_pause_stream)
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume a stream')
    resume_parser.add_argument('url', help='Stream URL')
    resume_parser.set_defaults(func=cmd_resume_stream)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export phone numbers')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                              help='Export format')
    export_parser.add_argument('--output', help='Output file path')
    export_parser.set_defaults(func=cmd_export)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=30,
                               help='Remove logs older than N days')
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the scraper')
    run_parser.add_argument('--config', default='config/config.yaml',
                           help='Config file path')
    run_parser.add_argument('--urls', help='File with URLs to scrape')
    run_parser.add_argument('--url', help='Single URL to scrape')
    run_parser.add_argument('--workers', type=int, help='Number of workers')
    run_parser.add_argument('--platform', default='generic', help='Platform name')
    run_parser.set_defaults(func=cmd_run)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Install tabulate if not available
    try:
        args.func(args)
    except ImportError as e:
        if 'tabulate' in str(e):
            print("Installing required package: tabulate")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tabulate'])
            print("Please run the command again.")
        else:
            raise


if __name__ == '__main__':
    main()
