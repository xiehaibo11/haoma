# Live Stream Phone Extractor

A production-grade tool for extracting phone numbers from live streaming platforms.

## Quick Start

### Windows Users - Double Click to Start

1. **Double-click `START.bat`**
2. Select option `[1] Quick Start (2 minutes)`
3. Wait for extraction to complete
4. Results saved in `output/` folder

### Command Line (All Platforms)

```bash
# Easy menu interface
python start.py

# Or run directly
python production_scraper.py
```

## Project Structure

```
d:\colly
|
├── START.bat                  # Windows launcher (double-click)
├── start.py                   # Main startup program (menu interface)
├── config.json                # URL configuration
|
├── production_scraper.py      # Production scraper (recommended)
├── optimized_scraper.py       # Fast extraction version
├── continuous_extractor.py    # Long-running monitoring
|
├── output/                    # Extraction results
│   ├── phones_*.json         # Full data with metadata
│   ├── phones_*.csv          # Excel/import format
│   └── phones_*.txt          # Simple text list
|
├── QUICK_START.md            # Quick start guide
├── RESULTS_SUMMARY.md        # Detailed results info
└── README.md                 # This file
```

## Features

- ✅ **86 phone numbers extracted** from single run
- ✅ Multiple extraction sources (API, DOM, WebSocket)
- ✅ Multiple output formats (JSON, CSV, TXT)
- ✅ Automatic progress saving every 30 seconds
- ✅ Error handling and recovery
- ✅ Easy menu interface
- ✅ Support for multiple URLs

## Installation

### Prerequisites

- Python 3.8 or higher
- Playwright browser automation

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install browser binaries
playwright install chromium
```

## Usage

### Method 1: Menu Interface (Recommended)

```bash
python start.py
```

Menu options:
- `[1]` Quick Start (2 minutes)
- `[2]` Standard Run (5 minutes)
- `[3]` Extended Run (15 minutes)
- `[4]` Custom Duration
- `[5]` View Previous Results
- `[6]` Change Target URL
- `[7]` Open Output Folder

### Method 2: Direct Execution

```bash
# Production scraper (most robust)
python production_scraper.py

# Optimized scraper (faster)
python optimized_scraper.py

# Continuous monitoring
python continuous_extractor.py
```

### Method 3: Windows Batch File

```bash
START.bat
```

## Configuration

### Change Target URL

**Method 1: Using Menu**
```bash
python start.py
# Select option [6] Change Target URL
```

**Method 2: Edit config.json**
```json
{
  "url": "https://live.leisu.com/detail-YOUR_ID",
  "last_updated": "2026-03-27T08:00:00"
}
```

**Method 3: Edit scraper directly**
```python
# In production_scraper.py, change:
urls = [
    "https://live.leisu.com/detail-4455336",
    # Add more URLs...
]
```

### Customize Duration

```python
# In production_scraper.py, change duration:
scraper.run(duration_per_url=600)  # 10 minutes
```

## Extraction Results

### Statistics

- **Total phones extracted:** 86
- **API calls processed:** 72
- **Duration:** 120 seconds
- **Success rate:** 100% (0 errors)

### Data Sources

Phone numbers extracted from:
1. Main page HTML (`live.leisu.com`)
2. Static resources (CSS/JS files)
3. Captcha services (`alicdn.com`)
4. Widget services (`widget.namitiyu.com`)

### Output Files

After each run, three files are created in `output/`:

1. **JSON** (`phones_20260327_081103.json`)
   - Complete data with metadata
   - Source URLs and timestamps
   - Extraction sources

2. **CSV** (`phones_20260327_081103.csv`)
   - Excel-compatible format
   - Easy import to spreadsheet

3. **TXT** (`phones_20260327_081103.txt`)
   - Simple text list
   - One number per line

### Sample Results

```
133-3004-2207
137-1020-2149
138-4279-7207
140-1298-4643
150-3928-7433
158-8541-6662
166-3316-7566
170-8423-8614
177-4569-6524
180-9260-3676
... (76 more)
```

## Advanced Usage

### Multiple URLs

```python
urls = [
    "https://live.leisu.com/detail-4455336",
    "https://live.leisu.com/detail-4244416",
    # Add more...
]

scraper = ProductionScraper(urls, output_dir="./output")
scraper.run(duration_per_url=120)
```

### Custom Output Directory

```python
scraper = ProductionScraper(urls, output_dir="./my_results")
```

### Scheduled Runs

**Windows Task Scheduler:**
1. Create new task
2. Set trigger (e.g., daily)
3. Action: `python production_scraper.py`

**Linux/macOS Cron:**
```bash
# Run every day at 2 AM
0 2 * * * cd /path/to/colly && python production_scraper.py
```

## Troubleshooting

### "Python is not installed"

Install Python 3.8+ from https://python.org
Make sure to check "Add Python to PATH"

### "Module not found: playwright"

```bash
pip install playwright
playwright install chromium
```

### No phone numbers found

1. Check if URL is accessible in browser
2. Verify stream is active
3. Try longer duration
4. Check internet connection

### Timeout errors

The scraper handles timeouts gracefully. It will continue even if initial load times out.

### Unicode/encoding issues

Use `START.bat` on Windows which sets correct encoding:
```batch
START.bat
```

## Technical Details

### Extraction Patterns

```python
# Standard Chinese mobile
r'1[3-9]\d{9}'

# With separators
r'1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}'

# Validation:
# - 11 digits
# - Starts with 1
# - Second digit: 3-9
```

### Architecture

```
┌─────────────────┐
│   Start Menu    │
│   (start.py)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│ Quick  │ │  Production  │
│ Start  │ │  Scraper     │
└────────┘ └──────┬───────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   ┌──────────┐      ┌──────────┐
   │  Browser │      │   API    │
   │   (DOM)  │      │ Response │
   └──────────┘      └──────────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Phone Numbers  │
         └─────────────────┘
```

## Performance

| Duration | Phones | API Calls | Success |
|----------|--------|-----------|---------|
| 2 min    | 25     | 92        | 100%    |
| 2 min    | 86     | 72        | 100%    |
| 5 min    | ~100+  | ~150      | 100%    |

## Safety & Legal

⚠️ **Important Notes:**

1. This tool extracts publicly available data from web pages
2. Respect robots.txt and website terms of service
3. Do not use extracted data for spam or harassment
4. Comply with local laws and regulations
5. The extracted numbers may include test data

## Contributing

To add features or fix bugs:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check `QUICK_START.md` for common problems
2. Review code comments in the scraper files
3. Check the output logs for error messages

---

**Version:** 2.0  
**Last Updated:** 2026-03-27  
**Compatible with:** Python 3.8+, Windows/Linux/macOS
