# 🚀 Quick Start Guide

## Easy Launch (Recommended)

### Windows Users

**Method 1: Double-click to run**
1. Navigate to the project folder
2. Double-click `START.bat`
3. Follow the menu prompts

**Method 2: Command line**
```batch
START.bat
```

### All Platforms (Command Line)

```bash
python start.py
```

## Menu Options

```
[1] 🚀 Quick Start (2 minutes)     - Fast extraction
[2] ⏱️  Standard Run (5 minutes)   - Balanced depth
[3] 🔥 Extended Run (15 minutes)   - Deep extraction
[4] 🎯 Custom Duration             - Set your own time
[5] 📊 View Previous Results       - Check past runs
[6] 🌐 Change Target URL           - Use different stream
[7] 📁 Open Output Folder          - View saved files
[0] ❌ Exit                        - Quit program
```

## First Time Setup

1. **Install dependencies** (if not already done):
```bash
pip install playwright
playwright install chromium
```

2. **Run the program**:
```bash
python start.py
```

3. **Select option [1] for Quick Start**

4. **Wait for extraction to complete**

5. **Results will be saved** in the `output/` folder

## Output Files

After each run, you'll find:

- `phones_YYYYMMDD_HHMMSS.json` - Full data with metadata
- `phones_YYYYMMDD_HHMMSS.csv` - Excel/import format  
- `phones_YYYYMMDD_HHMMSS.txt` - Simple text list

## Changing the Target URL

### Method 1: Using Menu
1. Select option `[6] 🌐 Change Target URL`
2. Enter the new URL
3. Save and run

### Method 2: Edit Config File
Edit `config.json`:
```json
{
  "url": "https://live.leisu.com/detail-YOUR_ID",
  "last_updated": "..."
}
```

## Advanced Usage

### Run Specific Scraper Directly

**Production Scraper** (most robust):
```bash
python production_scraper.py
```

**Optimized Scraper** (faster):
```bash
python optimized_scraper.py
```

**Continuous Scraper** (long-running):
```bash
python continuous_extractor.py
```

### Customize Duration

Edit the script and change:
```python
scraper.run(duration_per_url=600)  # 10 minutes
```

## Troubleshooting

### "Python is not installed"
- Install Python 3.8+ from https://python.org
- Make sure to check "Add Python to PATH" during installation

### "Module not found: playwright"
```bash
pip install playwright
playwright install chromium
```

### No phone numbers found
- Check if the URL is accessible in your browser
- Try a longer duration (options 2 or 3)
- Verify the stream is active

### Encoding issues on Windows
The startup program uses UTF-8 encoding. If you see garbled text:
1. Use `START.bat` which sets the correct encoding
2. Or run: `chcp 65001` before `python start.py`

## Keyboard Shortcuts

While running:
- `Ctrl+C` - Stop the scraper gracefully
- The scraper will save progress before exiting

## Tips

1. **Longer runs = More numbers** - Run for 15+ minutes for best results
2. **Multiple streams** - Add more URLs to scrape several streams
3. **Schedule runs** - Use Task Scheduler (Windows) or cron (Linux) for automated extraction
4. **Check output folder** - Results are saved automatically every 30 seconds

## Need Help?

Check the full documentation:
- `RESULTS_SUMMARY.md` - Detailed results info
- Code comments in `production_scraper.py`
