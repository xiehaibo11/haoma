# Installation Guide

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Internet connection

## Step-by-Step Installation

### 1. Install Python

Download and install Python from [python.org](https://www.python.org/downloads/).

Verify installation:
```bash
python --version
# or
python3 --version
```

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/livestream-scraper.git
cd livestream-scraper
```

### 3. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Playwright Browsers

```bash
playwright install chromium
```

This downloads the Chromium browser for Playwright automation.

## Verification

Test the installation:

```bash
python -m src.scraper --help
```

You should see the help message.

## Troubleshooting

### Playwright Installation Issues

If `playwright install` fails:

```bash
# Install system dependencies first
# Ubuntu/Debian:
sudo apt-get install libnss3 libatk-bridge2.0-0 libxcomposite1

# Then retry
playwright install chromium
```

### Permission Errors

On Linux/macOS, you may need:

```bash
chmod +x -R $(python -c "import playwright; print(playwright.__file__)")/../../../driver/
```

### Windows Defender/SmartScreen

If Windows blocks the browser:
1. Open Windows Security
2. Virus & threat protection → Virus & threat protection settings
3. Add exclusion for your project directory

## Next Steps

See [Configuration](CONFIGURATION.md) to set up your first extraction.
