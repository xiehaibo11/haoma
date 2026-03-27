# API Documentation

## Module Overview

```
src/
├── scraper.py      # Main scraper class
├── extractor.py    # Phone extraction logic
├── writer.py       # Output file handling
└── utils.py        # Utility functions
```

## LiveStreamScraper Class

### Constructor

```python
from src.scraper import LiveStreamScraper

config = {
    'target': {'url': 'https://example.com'},
    'scraping': {'duration': 300},
    # ... other options
}

scraper = LiveStreamScraper(config)
```

### Methods

#### `run() -> Dict[str, Dict]`

Execute the scraping loop.

```python
results = scraper.run()
# Returns: {'13800138000': {'formatted': '138-0013-8000', ...}}
```

#### `scan_page(page) -> int`

Scan a Playwright page for phone numbers.

```python
new_phones = scraper.scan_page(page)
```

#### `print_summary()`

Print final statistics.

## PhoneExtractor Class

### Constructor

```python
from src.extractor import PhoneExtractor

patterns = [
    {'name': 'china', 'pattern': r'1[3-9]\d{9}', 'enabled': True}
]
extractor = PhoneExtractor(patterns)
```

### Methods

#### `extract(text: str, context: str = None) -> List[PhoneNumber]`

Extract phone numbers from text.

```python
phones = extractor.extract("Call me at 13800138000")
for phone in phones:
    print(phone.formatted)  # 138-0013-8000
```

#### `validate_chinese_mobile(number: str) -> bool`

Validate Chinese mobile number format.

```python
is_valid = extractor.validate_chinese_mobile("13800138000")
```

## PhoneNumber Dataclass

```python
from src.extractor import PhoneNumber

phone = PhoneNumber(
    raw="13800138000",
    formatted="138-0013-8000",
    pattern_name="china_mobile",
    context="Call me at 13800138000"
)
```

Attributes:
- `raw`: Clean 11-digit number
- `formatted`: Formatted with hyphens
- `pattern_name`: Which pattern matched
- `context`: Surrounding text

## OutputWriter Class

### Constructor

```python
from src.writer import OutputWriter

config = {
    'directory': './output',
    'formats': {'csv': True, 'json': True},
    'filename_prefix': 'phones'
}
writer = OutputWriter(config)
```

### Methods

#### `write_all(phones: Dict)`

Write to all enabled formats.

```python
phones = {'13800138000': {'formatted': '138-0013-8000', ...}}
writer.write_all(phones)
```

#### `append_single(phone: str, data: Dict)`

Append single phone to CSV.

```python
writer.append_single('13800138000', {'formatted': '138-0013-8000'})
```

#### `save_backup(phones: Dict)`

Save JSON backup.

## Custom Extractor Example

```python
from src.extractor import PhoneExtractor, PhoneNumber
import re

class InternationalExtractor(PhoneExtractor):
    def __init__(self):
        patterns = [
            {'name': 'us', 'pattern': r'\(\d{3}\) \d{3}-\d{4}', 'enabled': True},
            {'name': 'uk', 'pattern': r'\+44 \d{4} \d{6}', 'enabled': True},
        ]
        super().__init__(patterns)
    
    def _format_number(self, number: str) -> str:
        # Custom formatting
        if len(number) == 10:  # US
            return f"({number[:3]}) {number[3:6]}-{number[6:]}"
        return number
```

## Integration Example

```python
from src.scraper import LiveStreamScraper, load_config

# Load config
config = load_config('config/config.yaml')

# Customize
config['target']['url'] = 'https://example.com/stream'
config['scraping']['duration'] = 600

# Run
scraper = LiveStreamScraper(config)
results = scraper.run()

# Process results
for phone, data in results.items():
    print(f"Found: {data['formatted']}")
```
