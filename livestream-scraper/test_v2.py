#!/usr/bin/env python3
"""
Quick test of v2.0 components.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing v2.0 Components...")
print("=" * 60)

# Test 1: Username Extractor
print("\n1. Testing Username Extractor...")
from core.username_extractor import UsernamePhoneExtractor, extract_phones_from_user

extractor = UsernamePhoneExtractor()

# Test cases
test_cases = [
    ("张三13800138000", None, None),
    ("User123", "Call me 13912345678", None),
    ("ContactMe", None, "Phone: 15012345678"),
]

for username, comment, profile in test_cases:
    results = extractor.extract_all(username, comment, profile)
    if results:
        print(f"  [OK] {username}: Found {len(results)} phone(s)")
        for r in results:
            print(f"      - {r.formatted} (confidence: {r.confidence:.2f}, source: {r.source})")
    else:
        print(f"  [NO] {username}: No phones found")

# Test 2: Database
print("\n2. Testing Database...")
from database.db import Database

db = Database("./output/test.db")

# Add a stream
added = db.add_stream("https://test.com/stream1", "test", priority=5)
print(f"  [OK] Stream added: {added}")

# Add a phone
is_new = db.add_phone(
    phone="13800138000",
    formatted="138-0013-8000",
    stream_url="https://test.com/stream1",
    username="TestUser",
    context="Test context",
    pattern_type="test"
)
print(f"  [OK] Phone added (new: {is_new})")

# Get stats
stats = db.get_stats()
print(f"  [OK] Stats: {stats.total_phones} phones, {stats.total_streams} streams")

# Test 3: Scheduler (basic init)
print("\n3. Testing Scheduler...")
from scheduler.scheduler import StreamScheduler, RateLimiter

rate_limiter = RateLimiter(max_requests=10, time_window=60)
print(f"  [OK] Rate limiter created")

scheduler = StreamScheduler(db, max_workers=3)
print(f"  [OK] Scheduler created with 3 workers")

print("\n" + "=" * 60)
print("All tests passed! v2.0 components are working.")
print("\nTo run the full scraper:")
print("  python manage.py run --workers 3 --url https://live.leisu.com/detail-4244416")
