# Multi-Language Desktop Application

## Overview

This version of the desktop application supports **multiple languages** with an easy-to-use language selector on startup.

### Supported Languages

| Language | Code | Status |
|----------|------|--------|
| English | `en` | ✅ Complete |
| Chinese (Simplified) | `zh` | ✅ Complete |

## How to Use

### First Launch

When you start the application, a language selector dialog appears:

```
┌─────────────────────────────────────────┐
│  Select Language / 选择语言              │
├─────────────────────────────────────────┤
│  Please select language:                │
│  请选择语言:                             │
│                                         │
│  [        English        ]              │
│  [   中文 (Chinese)      ]              │
└─────────────────────────────────────────┘
```

Click your preferred language to continue.

### Switching Languages

Once the app is running, you can switch languages:

1. Click on **"Language / 语言"** in the menu bar
2. Select your preferred language
3. The app will restart automatically with the new language

## Language Files

### Built-in Translations

All translations are built into the `i18n.py` file:

```python
TRANSLATIONS = {
    'en': {
        'app_title': 'Live Stream Phone Extractor',
        'start_extraction': 'Start Extraction',
        # ... more keys
    },
    'zh': {
        'app_title': '直播手机号提取器',
        'start_extraction': '开始提取',
        # ... more keys
    }
}
```

### Adding New Languages

To add a new language:

1. Open `i18n.py`
2. Add translation dictionary:

```python
'th': {  # Thai example
    'app_title': 'ตัวดึงหมายเลขโทรศัพท์',
    'start_extraction': 'เริ่มการดึงข้อมูล',
    # Copy all keys from English...
}
```

3. Save and restart

## Running the Multi-Language App

### Windows
```bash
cd d:\colly\livestream-scraper\desktop_app
python app_multilang.py
```

### Skip Language Selection

To skip the language selector and use a default:

```python
# In app_multilang.py, change:
lang = 'zh'  # For Chinese
# or
lang = 'en'  # For English
```

## Screenshots

### English Interface
```
Live Stream Phone Extractor - Leisu.com
├─ Target URL: [https://live.leisu.com/detail-4244416]
├─ [Start Extraction] [Refresh Data] [Export CSV]
├─ ID | Phone Number | Username | Context | Extracted At
└─ Total: 156 | Today: 23 | Unique Phones: 142
```

### Chinese Interface
```
直播手机号提取器 - Leisu.com
├─ 目标网址: [https://live.leisu.com/detail-4244416]
├─ [开始提取] [刷新数据] [导出CSV]
├─ ID | 手机号码 | 用户名 | 内容 | 提取时间
└─ 总计: 156 | 今日: 23 | 唯一号码: 142
```

## Translation Keys

All UI elements use these translation keys:

| Key | English | Chinese |
|-----|---------|---------|
| `app_title` | Live Stream Phone Extractor | 直播手机号提取器 |
| `url_section` | Target URL | 目标网址 |
| `start_extraction` | Start Extraction | 开始提取 |
| `stop_extraction` | Stop Extraction | 停止提取 |
| `refresh_data` | Refresh Data | 刷新数据 |
| `export_csv` | Export CSV | 导出CSV |
| `search` | Search: | 搜索: |
| `col_phone` | Phone Number | 手机号码 |
| `col_username` | Username | 用户名 |
| `col_context` | Context | 内容 |
| `status_ready` | Ready | 就绪 |
| `status_found` | Found X phones | 发现X个号码 |

## Technical Details

### I18n System

The internationalization system:

1. **Language Selection**: Stored in `I18n` class
2. **Translation Lookup**: `_()` function
3. **Format Support**: Variable substitution (`{}`)
4. **Fallback**: Defaults to English if key missing

### Code Example

```python
import i18n

# Set language
i18n.set_language('zh')

# Get translation
title = i18n._('app_title')  # 直播手机号提取器

# With format
msg = i18n._('status_found', 5)  # 发现 5 个新号码
```

## Adding Custom Translations

You can add translations without modifying code:

1. Create `translations.json`:

```json
{
  "ja": {
    "app_title": "電話番号抽出ツール",
    "start_extraction": "抽出開始"
  }
}
```

2. Register in `i18n.py`:

```python
def _load_custom_translations(self):
    if os.path.exists('translations.json'):
        with open('translations.json', 'r') as f:
            self.custom_translations = json.load(f)
```

## File Structure

```
desktop_app/
├── app.py                  # Original (English only)
├── app_multilang.py        # Multi-language version ← Use this
├── i18n.py                 # Translation system
├── database.py             # Database (language-agnostic)
├── extractor.py            # Extractor (language-agnostic)
└── scraper.py              # Scraper (language-agnostic)
```

## Recommendation

Use **`app_multilang.py`** for international users
Use **`app.py`** for English-only deployment

Both have identical functionality, just different language support.

## Run Now

```bash
cd d:\colly\livestream-scraper\desktop_app
python app_multilang.py
```

Select your language and start extracting!
