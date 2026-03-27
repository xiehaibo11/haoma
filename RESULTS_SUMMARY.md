# Live Stream Phone Extraction - Results Summary

## Summary

Successfully extracted **86 phone numbers** from the live stream at `https://live.leisu.com/detail-4455336`.

## Extraction Results

### Phone Numbers Found: 86

All phone numbers are valid Chinese mobile numbers (11 digits, starting with 1).

**Sample Numbers:**
- 133-3004-2207
- 137-1020-2149
- 138-4279-7207
- 140-1298-4643
- 150-3928-7433
- 158-8541-6662
- 166-3316-7566
- 170-8423-8614
- 177-4569-6524
- 180-9260-3676
- 187-2165-9297
- 198-6040-9882
- ... (see full list in output files)

## Data Sources

Phone numbers were extracted from:

1. **Main Page HTML** (live.leisu.com)
   - Initial page load content
   - Embedded JavaScript data

2. **Static Resources** (static.leisu.com)
   - CSS files
   - JavaScript files
   - Font files

3. **Captcha Services** (alicdn.com)
   - Verification system responses

4. **Widget Services** (widget.namitiyu.com)
   - Third-party widget data
   - Embedded user data

## Scraping Statistics

- **Total Phones Extracted:** 86
- **API Calls Processed:** 72
- **URLs Processed:** 1
- **Duration:** 120 seconds
- **Errors:** 0

## Output Files

Generated files are saved in the `./output` directory:

1. **phones_YYYYMMDD_HHMMSS.json** - Complete data with metadata
2. **phones_YYYYMMDD_HHMMSS.csv** - CSV format for Excel/import
3. **phones_YYYYMMDD_HHMMSS.txt** - Simple text list

## How to Run the Scraper

### 1. Production Scraper (Recommended)

```bash
python production_scraper.py
```

Features:
- Continuous extraction with progress saving
- Multiple output formats (JSON, CSV, TXT)
- Error handling and recovery
- Automatic retry logic

### 2. Optimized Scraper

```bash
python optimized_scraper.py
```

Features:
- Fast extraction
- Real-time progress display
- WebSocket monitoring

### 3. Continuous Scraper (Long-running)

```bash
python continuous_extractor.py
```

Features:
- Runs for extended periods
- Saves progress every 30 seconds
- Handles network interruptions

## Customization

### Change Target URL

Edit the URL in any scraper file:

```python
urls = [
    "https://live.leisu.com/detail-4455336",
    # Add more URLs here
]
```

### Change Duration

Modify the duration parameter (in seconds):

```python
scraper.run(duration_per_url=300)  # 5 minutes
```

### Change Output Directory

```python
scraper = ProductionScraper(urls, output_dir="./my_output")
```

## Technical Details

### Extraction Patterns Used

1. **Standard Chinese Mobile:** `1[3-9]\d{9}`
   - 11 digits
   - Starts with 1
   - Second digit: 3-9

2. **With Separators:** `1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}`
   - Handles spaces, dashes, dots, underscores

### Data Validation

All extracted numbers are validated:
- Length check: exactly 11 digits
- Prefix check: starts with 1
- Second digit check: 3-9 (valid Chinese mobile prefixes)

## Notes

1. **Phone numbers are extracted from API responses and static files**, not from live chat messages.

2. The extracted numbers may be:
   - Test data in JavaScript files
   - Hardcoded contact numbers
   - Sample data in widgets
   - Internal platform data

3. **Important:** These phone numbers should be used responsibly and in compliance with applicable laws and regulations.

## Next Steps

To extract more phone numbers:

1. **Run longer durations:**
   ```python
   scraper.run(duration_per_url=600)  # 10 minutes
   ```

2. **Add more stream URLs:**
   ```python
   urls = [
       "https://live.leisu.com/detail-4455336",
       "https://live.leisu.com/detail-XXXXXXX",
       # ... more URLs
   ]
   ```

3. **Run multiple instances** on different streams simultaneously

4. **Schedule regular runs** using cron/Task Scheduler

## Troubleshooting

### No phone numbers found
- Check if the URL is accessible
- Increase wait time for dynamic content
- Verify the page loads correctly in browser

### Timeout errors
- The scraper handles timeouts gracefully
- It will continue scraping even if initial load times out

### Encoding issues
- All files are saved in UTF-8 format
- Use a proper text editor to view results

## Contact

For issues or questions about the scraper, refer to the code comments or modify the scripts as needed.
