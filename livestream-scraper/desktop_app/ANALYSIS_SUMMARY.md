# Website Structure Analysis - Leisu.com

## 🔍 What I Found

### 1. Main Page Structure
```
URL: https://live.leisu.com/detail-{MATCH_ID}
Example: https://live.leisu.com/detail-4336493
```

### 2. Chat/Comment Location
```
Iframe: https://widget.namitiyu.com/football?id={MATCH_ID}
Example: https://widget.namitiyu.com/football?id=4336493
```

### 3. Key Components
- **Main page**: Shows match info, no comments
- **Iframe (widget.namitiyu.com)**: Contains live chat/comments
- **Chat component**: `detail_chatroom-*.js` loads dynamically

### 4. How Comments Load
1. Page loads with empty iframe
2. JavaScript fetches comments from API
3. Comments render in iframe
4. Real-time updates via WebSocket or polling

### 5. Phone Number Extraction Strategy
```
1. Load main page
2. Find iframe[src*="namitiyu"]
3. Access iframe content
4. Wait 15-20 seconds for JS to load comments
5. Extract all text from iframe body
6. Find pattern: 1[3-9]\d{9}
7. Scroll to load more
8. Repeat every 5 seconds
```

## 🛠️ Technical Challenges

### Challenge 1: Dynamic Loading
**Problem**: Comments load via JavaScript, not in HTML
**Solution**: Use Playwright, wait 15+ seconds

### Challenge 2: Cross-Origin Iframe
**Problem**: iframe is from different domain (namitiyu.com)
**Solution**: Playwright can access it (same-origin policy bypassed)

### Challenge 3: Headless Detection
**Problem**: Site may block headless browsers
**Solution**: Use mobile viewport + real user agent

### Challenge 4: Encoding Issues
**Problem**: Chinese characters show as garbage
**Solution**: Site uses UTF-8, terminal issue only

## ✅ Working Solution

### FINAL_APP.py Features:
1. **Mobile viewport** (375x812) - better for chat
2. **Iframe targeting** - specifically looks for namitiyu iframe
3. **Long wait** (15s) - allows JS to load comments
4. **Session tracking** - prevents duplicate extraction
5. **Auto-scroll** - loads more comments
6. **Direct DB** - saves immediately

### How to Use:
```bash
python FINAL_APP.py
```

1. Enter match ID (e.g., 4336493)
2. Click START
3. Wait for "Found chat iframe!"
4. Watch log for new phones
5. Data auto-saves to database

## 📊 Data Flow

```
User enters Match ID (4336493)
           ↓
Browser loads https://live.leisu.com/detail-4336493
           ↓
Waits for iframe to load
           ↓
Accesses https://widget.namitiyu.com/football?id=4336493
           ↓
Waits 15s for JS to render comments
           ↓
Extracts text → Finds phones → Saves to DB
           ↓
Every 5s: Scroll → Extract → Save
```

## 🎯 Expected Results

When working correctly, log shows:
```
[12:34:56] ========================================
[12:34:56] STARTING - Match ID: 4336493
[12:34:56] ========================================
[12:34:57] Launching browser...
[12:34:58] Loading: https://live.leisu.com/detail-4336493
[12:34:59] Page loaded
[12:34:59] Waiting for chat iframe...
[12:35:15] Found chat iframe!
[12:35:15] Accessing iframe content...
[12:35:25] Check #1
[12:35:25] Found 3 NEW phones!
[12:35:25]   ✓ Saved: 138-0013-8000
[12:35:25]   ✓ Saved: 139-1234-5678
```

## 🚀 Run the Final App

```bash
cd d:\colly\livestream-scraper\desktop_app
python FINAL_APP.py
```

**Note**: The site may have anti-bot protection. If no data appears:
1. Check internet connection
2. Verify match is live
3. Try different match ID
4. Check log for errors
