# Production Desktop Application

## Features

### ✅ Implemented
- **Multilingual UI**: English + Chinese (menu selectable)
- **Real-time extraction**: 3-second check interval
- **Retry logic**: Auto-retry on timeout (max 3 attempts)
- **Dynamic content**: Handles live updating comments
- **Deduplication**: Tracks seen texts, not just phones
- **Data display**: Shows ID, Phone, Username, Context, Time
- **Export**: CSV export with UTF-8 encoding
- **Search**: Search by phone/username/context
- **Logging**: Real-time log panel
- **No test data**: Only extracts from real website

### 🚀 Production Improvements
1. **60-second timeout** (vs 30s before)
2. **3 retry attempts** with exponential backoff
3. **Desktop viewport** (1280x800) for better rendering
4. **Dynamic comment detection** - multiple strategies
5. **Text-based deduplication** - tracks full comment text
6. **Menu bar language switch** - persistent preference

---

## Usage

### Run Production Version

```bash
cd d:\colly\livestream-scraper\desktop_app
python app_production.py
```

Or use launcher:
```bash
run_production.bat
```

### Language Selection

1. **Menu bar** → Language / 语言
2. Select English or 中文
3. App restarts with selected language

Preference is saved to `lang_pref.json`

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Live Stream Phone Extractor / 直播手机号提取器              [Language]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Target URL / 目标网址: [https://live.leisu.com/detail-4244416]  [URL 1] [URL 2]│
├─────────────────────────────────────────────────────────────────────────────┤
│ [▶ Start] [Refresh] [Export]                    Search: [      ] [🔍]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Extracted Data / 提取的数据                    │  Log                        │
│ ┌────┬─────────────┬──────────┬──────────┬─────┤  [12:34:56] Starting...     │
│ │ ID │ Phone       │ Username │ Context  │ Time│  [12:34:59] Found 3 new     │
│ ├────┼─────────────┼──────────┼──────────┼─────┤  [12:35:02] Found 1 new     │
│ │ 1  │ 138-0013... │ 张三138  │ Contact  │ ... │                             │
│ │ 2  │ 139-1234... │ 李四     │ Call me  │ ... │                             │
│ └────┴─────────────┴──────────┴──────────┴─────┤                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total: 156 | Today: 23 | Phones: 142 | Users: 89                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Status: Found 3 new comment(s) with phone numbers                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Display

### Table Columns

| Column | Description | Example |
|--------|-------------|---------|
| ID | Record ID | 1, 2, 3... |
| Phone Number / 手机号码 | Formatted phone | 138-0013-8000 |
| Username / 用户名 | Comment author | 张三13800138000 |
| Context / 内容 | Comment text | Contact me... |
| Time / 时间 | Extraction timestamp | 2024-03-27 12:34:56 |

### Statistics

- **Total / 总计**: All records in database
- **Today / 今日**: Records from today only
- **Phones / 号码**: Unique phone numbers
- **Users / 用户**: Unique usernames

---

## Extraction Behavior

### Real-Time Processing

1. **Page loads** (60s timeout, 3 retries)
2. **Every 3 seconds**: Scan for new comments
3. **Text deduplication**: Tracks `{username}:{comment}` to avoid duplicates
4. **Phone extraction**: Extracts from username AND comment text
5. **Database storage**: Saves immediately with deduplication
6. **UI update**: Auto-refreshes every 5 seconds

### What Gets Extracted

| Source | Example | Extracted |
|--------|---------|-----------|
| Username | 张三13800138000 | 138-0013-8000 |
| Comment | Call me 139-1234-5678 | 139-1234-5678 |
| Both | 李四: My phone 15056789012 | 150-5678-9012 |

---

## Troubleshooting

### Page Timeout

**Symptom**: "Timeout 30000ms exceeded" in log

**Solution**:
- App auto-retries (up to 3 times)
- Check internet connection
- Verify URL is accessible
- Wait longer (60s timeout)

### No Data Appearing

**Check**:
1. Is live stream active? (check in browser)
2. Are comments visible on page?
3. Wait at least 30 seconds after starting
4. Check log for errors

### Language Not Changing

**Solution**:
- Select language from menu
- Click "Yes" to restart
- Preference saved automatically

---

## Files

| File | Purpose |
|------|---------|
| `app_production.py` | Main application |
| `scraper_live.py` | Live stream scraper with retry |
| `extractor_fixed.py` | Phone number extractor |
| `database.py` | SQLite database |
| `run_production.bat` | Windows launcher |
| `lang_pref.json` | Saved language preference |

---

## Run Now

```bash
cd d:\colly\livestream-scraper\desktop_app
python app_production.py
```

**Select language from menu, then click "Start Extraction"**
