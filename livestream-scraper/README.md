# LiveStream Phone Extractor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https://img.shields.io/badge/playwright-automation-green.svg)](https://playwright.dev/)

> **Automated phone number extraction from live stream comments**

A powerful, extensible tool for monitoring live streams and extracting mobile phone numbers from real-time comments. Built with Playwright for browser automation and designed for continuous operation.

## Features

- **Real-time Monitoring**: Continuously scans live stream comments
- **Multi-pattern Recognition**: Detects various phone number formats (Chinese mobile numbers)
- **Persistent Storage**: Saves findings to CSV, JSON, and TXT formats
- **Smart Deduplication**: Tracks unique numbers with occurrence counts
- **Configurable**: YAML-based configuration for easy customization
- **Headless Operation**: Runs in background without GUI
- **Extensible**: Plugin architecture for custom extractors and notifiers

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/livestream-scraper.git
cd livestream-scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Basic Usage

```bash
# Run with default configuration
python -m src.scraper

# Run with custom URL
python -m src.scraper --url "https://live.example.com/stream/12345"

# Run for specific duration
python -m src.scraper --duration 300  # 5 minutes
```

### Configuration

Edit `config/config.yaml` to customize:

```yaml
target:
  url: "https://live.leisu.com/detail-4244416"
  
scraping:
  duration: 300  # seconds (0 = infinite)
  check_interval: 2  # seconds between checks
  scroll_interval: 5  # scroll every N iterations
  
phone_patterns:
  - "1[3-9]\\d{9}"  # Chinese mobile numbers
  
output:
  csv: true
  json: true
  txt: true
  directory: "./output"
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [API Documentation](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Legal & Ethics](docs/LEGAL.md)

## Project Structure

```
livestream-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Main scraper engine
│   ├── extractor.py        # Phone number extraction
│   ├── notifier.py         # Notifications/alerts
│   └── utils.py            # Utility functions
├── config/
│   └── config.yaml         # Configuration file
├── docs/
│   ├── INSTALLATION.md
│   ├── CONFIGURATION.md
│   ├── API.md
│   ├── DEVELOPMENT.md
│   └── LEGAL.md
├── tests/
│   └── test_extractor.py
├── examples/
│   └── custom_extractor.py
├── output/                 # Generated results
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

## Sample Output

```
============================================================
LIVE STREAM PHONE EXTRACTOR v1.0
============================================================
Target: https://live.leisu.com/detail-4244416
Duration: 300 seconds

[03:05:43] NEW PHONE: 177-4551-9344 (Total: 1)
[03:06:12] NEW PHONE: 138-0013-8000 (Total: 2)
[03:07:45] NEW PHONE: 139-1234-5678 (Total: 3)

============================================================
FINAL RESULTS
============================================================
Total unique phone numbers found: 3

1. 177-4551-9344
2. 138-0013-8000
3. 139-1234-5678

Files saved:
  - output/phones_20240327_030543.csv
  - output/phones_20240327_030543.json
  - output/phones_20240327_030543.txt
```

## Legal & Ethical Use

**IMPORTANT**: This tool is for educational and research purposes only.

- Respect website Terms of Service
- Comply with local privacy laws (GDPR, CCPA, PIPL)
- Do not use for spam, harassment, or unauthorized marketing
- Only extract data you have permission to access

See [Legal & Ethics](docs/LEGAL.md) for detailed guidelines.

## Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for:

- Setting up development environment
- Code style guidelines
- Testing requirements
- Pull request process

## Roadmap

- [ ] Support for more live stream platforms
- [ ] Machine learning-based phone format detection
- [ ] Real-time webhook notifications
- [ ] Docker containerization
- [ ] GUI interface
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] Multi-threading support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

The authors are not responsible for any misuse of this tool. Users are solely responsible for ensuring their use complies with all applicable laws and regulations.

---

**Made with ❤️ for the open-source community**
