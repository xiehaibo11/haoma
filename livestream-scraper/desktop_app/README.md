# Desktop App - Live Stream Phone Extractor

A simple, focused desktop application for extracting phone numbers and usernames from leisu.com live streams.

## Features

- **Simple GUI**: Easy-to-use desktop interface
- **Local Storage**: SQLite database for persistent storage
- **Deduplication**: Automatic duplicate detection
- **Real-time**: Live extraction with auto-refresh
- **Export**: CSV export functionality
- **Search**: Search through extracted data

## Quick Start

### 1. Installation

```bash
cd livestream-scraper/desktop_app

# Install Playwright (if not already installed)
pip install playwright
playwright install chromium
```

### 2. Run Application

**Windows:**
```bash
run_desktop.bat
```

**Linux/Mac:**
```bash
chmod +x run_desktop.sh
./run_desktop.sh
```

**Direct:**
```bash
python app.py
```

### 3. Usage

1. **Enter URL**: The default URL is preset, or enter your own
2. **Click Start**: Press "Start Extraction" button
3. **Wait**: The app will start extracting data
4. **View Results**: New data appears automatically in the table
5. **Export**: Click "Export CSV" to save results

## Interface Guide

### URL Section
- Enter the live stream URL
- Use preset buttons for quick selection

### Control Buttons
- **Start/Stop Extraction**: Begin or stop the scraping process
- **Refresh Data**: Manually refresh the data display
- **Export CSV**: Save all data to a CSV file
- **Search**: Search through extracted records

### Data Table
Columns:
- **ID**: Record ID
- **Phone Number**: Extracted phone number
- **Username**: Username who posted
- **Context**: Surrounding text
- **Extracted At**: Timestamp

### Right-Click Menu
Right-click on any row to:
- Copy Phone Number
- Copy Username
- Delete Record

Double-click to view full details.

### Statistics
Shows at bottom:
- Total records
- Today's records
- Unique phones
- Unique usernames

## Data Storage

All data is stored locally in `extracted_data.db` (SQLite database).

### Database Schema

```sql
extracted_phones:
  - id (primary key)
  - phone_number
  - formatted_phone
  - username
  - source_url
  - context
  - extracted_at (timestamp)
  - is_valid
```

## Configuration

Edit these variables in `scraper.py` to adjust behavior:

```python
self.check_interval = 5    # Seconds between page checks
self.scroll_interval = 3   # Scroll every N checks
```

## File Structure

```
desktop_app/
├── app.py              # Main GUI application
├── scraper.py          # Background scraper
├── extractor.py        # Phone extraction logic
├── database.py         # Local SQLite database
├── requirements.txt    # Dependencies
├── run_desktop.bat     # Windows launcher
├── run_desktop.sh      # Linux/Mac launcher
└── README.md           # This file
```

## Requirements

- Python 3.8+
- Playwright
- Tkinter (built-in)

## Troubleshooting

### App won't start
```bash
# Check Python version
python --version

# Install dependencies
pip install playwright
playwright install chromium

# Run with console to see errors
python app.py
```

### No data extracted
1. Check if URL is correct
2. Verify the live stream is active
3. Wait at least 30 seconds
4. Check internet connection

### Database locked
- Close any other instances of the app
- Restart the application

## Export Format

CSV columns:
- ID
- Phone Number
- Formatted Phone
- Username
- Source URL
- Context
- Extracted At
- Is Valid

## Updates

### v2.1.0
- Desktop GUI application
- Local SQLite database
- Real-time extraction
- CSV export
- Search functionality

## License

MIT License - See main project LICENSE
