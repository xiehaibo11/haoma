# Multi-Stream Phone Extractor v2.0

> **Production-grade, scalable phone number extraction from multiple live streams**

## Overview

This enhanced version adds enterprise features for sustainable, large-scale scraping:

- **Database Persistence**: SQLite with SQLAlchemy ORM
- **Multi-Stream Management**: Handle 100+ streams simultaneously  
- **Rate Limiting**: Global and per-stream rate limits
- **Queue System**: Priority-based task scheduling
- **Username Extraction**: Extract phones from usernames, comments, and profiles
- **Monitoring**: Real-time statistics and health checks
- **Management CLI**: Control and monitor without stopping the scraper

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Stream Scraper                      │
├─────────────────────────────────────────────────────────────┤
│  Scheduler        Database        Extractor       Browser   │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐    ┌────────┐ │
│  │  Queue  │────▶│ SQLite  │────▶│ Username│───▶│Playwrig│ │
│  │ Workers │     │  ORM    │     │ Extract │    │  ht    │ │
│  │Rate Lim │     │         │     │         │    │        │ │
│  └─────────┘     └─────────┘     └─────────┘    └────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              Stream 1      Stream N
              [Live]        [Live]
```

## Quick Start

### 1. Installation

```bash
cd livestream-scraper
pip install -r requirements.txt
playwright install chromium
```

### 2. Add Streams

```bash
# Add single stream
python manage.py add "https://live.leisu.com/detail-4244416" --platform leisu

# Or add from file
echo "https://live.leisu.com/detail-4244416" > streams.txt
echo "https://live.leisu.com/detail-4244417" >> streams.txt
```

### 3. Run Scraper

```bash
# Run with default settings
python manage.py run

# Run with 10 workers
python manage.py run --workers 10 --urls streams.txt
```

### 4. Monitor

```bash
# View statistics
python manage.py stats

# View extracted phones
python manage.py phones --today

# View streams
python manage.py streams
```

## Key Features

### Username-Based Extraction

Extracts phone numbers from:
- **Usernames**: `张三13800138000`
- **Comments**: "Contact me at 138-0013-8000"
- **Profiles**: Bio/description text

Confidence scoring based on:
- Source type (username = highest confidence)
- Presence of contact keywords
- Format validation

### Database Schema

```sql
phone_records:
  - phone_number (indexed)
  - source_stream (indexed)
  - username
  - context
  - confidence_score
  - first_seen / last_seen
  - occurrence_count

stream_records:
  - url (unique)
  - platform
  - status (active/paused/error)
  - last_check
  - phones_found
  - priority
  - check_interval

extraction_logs:
  - stream_url
  - timestamp
  - new_phones_found
  - duration
  - success/error
```

### Rate Limiting

Token bucket algorithm ensures:
- Global: Max 60 requests/minute across all streams
- Per-stream: Configurable intervals (default 30s)
- Automatic backoff on errors

### Priority Queue

Streams are processed by:
1. Priority level (1-10, lower = higher)
2. Last check time (oldest first)
3. Error count (fewer errors prioritized)

## Configuration

### config/config.yaml

```yaml
# Database
database:
  path: "./output/scraper.db"

# Scheduler
scheduler:
  max_workers: 10
  rate_limit: 60  # requests per minute
  check_interval: 30  # seconds

# Browser
browser:
  headless: true
  viewport:
    width: 1280
    height: 800

# Extraction patterns
phone_patterns:
  - name: "china_mobile"
    pattern: "1[3-9]\\d{9}"
    enabled: true

# Logging
logging:
  report_interval: 60  # seconds
```

## Management Commands

```bash
# Statistics
python manage.py stats

# List all streams
python manage.py streams

# List phones (with filters)
python manage.py phones --today --limit 50

# Add new stream
python manage.py add "https://example.com/stream" --platform example --priority 3

# Pause/Resume
python manage.py pause "https://example.com/stream"
python manage.py resume "https://example.com/stream"

# Export data
python manage.py export --format csv --output phones.csv

# Cleanup old logs
python manage.py cleanup --days 30

# Run scraper
python manage.py run --workers 10 --urls streams.txt
```

## Scaling Guidelines

### For 10-50 Streams
```bash
python manage.py run --workers 5
```

### For 50-200 Streams
```bash
python manage.py run --workers 10 --config config/high-volume.yaml
```

High-volume config:
```yaml
scheduler:
  max_workers: 10
  rate_limit: 120  # Higher rate limit
  check_interval: 60  # Less frequent checks
```

### For 200+ Streams
- Use multiple instances with different URL subsets
- Consider upgrading to PostgreSQL
- Use proxies to avoid IP blocks

## Database Exports

```bash
# Export all phones to CSV
python manage.py export --format csv --output all_phones.csv

# Export specific stream
python manage.py phones --stream "https://..." > stream_phones.txt
```

## Monitoring

### Real-time Stats
The scraper prints status every 60 seconds:
```
Status Report (uptime: 15m30s)
  Streams: 25 active / 50 total
  Queue: 12 tasks
  Phones: 156 total (23 today)
  Tasks: 245 completed, 3 failed
  Rate limit: 45.2% utilized
```

### Log Files
- `output/scraper.log` - Detailed operation log
- `output/scraper.db` - SQLite database
- `output/phones_export_*.csv` - Periodic exports

## Advanced Usage

### Custom Platform Extractor

```python
from src.core.username_extractor import UsernamePhoneExtractor

class YouTubeExtractor(UsernamePhoneExtractor):
    def extract_from_comment(self, username, comment):
        # YouTube-specific logic
        results = super().extract_from_comment(username, comment)
        
        # Additional patterns for YouTube
        # ...
        
        return results
```

### Database Query Examples

```python
from src.database.db import Database

db = Database()

# Get all phones from a stream
phones = db.get_phones_by_stream("https://...")

# Export to CSV
db.export_phones("output.csv", "csv")

# Get statistics
stats = db.get_stats()
print(f"Total phones: {stats.total_phones}")
```

## Troubleshooting

### High Memory Usage
- Reduce `max_workers` in config
- Enable `headless: true`
- Lower `max_elements` per scan

### Database Locked
- Ensure only one scraper instance runs
- Use PostgreSQL for multi-instance setups

### Rate Limiting
- Reduce number of workers
- Increase `check_interval`
- Use proxies (see docs/PROXIES.md)

## Performance Benchmarks

| Streams | Workers | Phones/Hour | CPU | RAM |
|---------|---------|-------------|-----|-----|
| 10      | 3       | ~50         | 20% | 500MB |
| 50      | 5       | ~200        | 40% | 1GB   |
| 100     | 10      | ~400        | 70% | 2GB   |

*Benchmarks on 4-core CPU, actual results vary by stream activity*

## Migration from v1.0

1. Backup your existing CSV/JSON files
2. Install new dependencies: `pip install sqlalchemy tabulate`
3. Import old data:
   ```python
   from src.database.db import Database
   db = Database()
   # Load from old CSV and add via db.add_phone()
   ```
4. Update your config file with new sections

## Roadmap v2.x

- [ ] PostgreSQL support
- [ ] Proxy rotation
- [ ] Web dashboard
- [ ] REST API
- [ ] Machine learning for phone detection
- [ ] Discord/Slack notifications
- [ ] Docker deployment

## License

MIT License - See LICENSE file
