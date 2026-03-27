# START HERE - Desktop App Quick Guide

## 🚀 Run the Application (30 seconds)

### Step 1: Open Command Prompt
```bash
# Navigate to desktop app folder
cd d:\colly\livestream-scraper\desktop_app
```

### Step 2: Run the App
```bash
python app.py
```

### Step 3: Use the App
1. The URL is already filled in: `https://live.leisu.com/detail-4244416`
2. Click **"Start Extraction"**
3. Wait 30-60 seconds for data to appear
4. Click **"Export CSV"** to save results

---

## 📋 What You See

### Main Window
```
┌─────────────────────────────────────────────────────────────┐
│  URL: [https://live.leisu.com/detail-4244416          ]     │
│                                                           │
│  [▶ Start Extraction] [🔄 Refresh] [📁 Export]             │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ID │ Phone         │ Username │ Context    │ Time   │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ 1  │ 138-0013-8000 │ 张三...  │ Contact... │ 10:30  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  Total: 0 | Today: 0 | Unique: 0 | Users: 0              │
│  Status: Ready                                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Automatically Appears Here
- **Phone Number**: Extracted phone (e.g., 138-0013-8000)
- **Username**: Who posted it (e.g., 张三13800138000)
- **Context**: Surrounding text
- **Time**: When it was found

---

## 🎯 Common Tasks

### Task 1: Extract Phone Numbers
```
1. Click "Start Extraction"
2. Wait for data to appear (30-60 seconds)
3. New numbers appear automatically
4. Click "Stop" when done
```

### Task 2: Export to Excel
```
1. Click "Export CSV"
2. Choose where to save
3. Open in Excel
4. Columns: ID, Phone, Username, Context, Time
```

### Task 3: Search Data
```
1. Type in Search box (top right)
2. Click "Search" or press Enter
3. Results filter automatically
4. Click "Refresh" to see all again
```

### Task 4: Copy a Phone Number
```
1. Right-click on any row
2. Click "Copy Phone"
3. Paste anywhere (Ctrl+V)
```

---

## 💾 Where Data Is Stored

**Database File**: `extracted_data.db` (in same folder)
- All extracted numbers saved here
- Automatically deduplicated
- Persists between sessions

**CSV Exports**: You choose location
- Click "Export CSV"
- Choose filename and folder
- Open in Excel or other tools

---

## ⚠️ Important Notes

### 1. First Run
- May take 30-60 seconds to start seeing data
- Browser opens invisibly (headless)
- App checks the page every 5 seconds

### 2. While Running
- Don't close the window
- Data appears automatically
- Numbers are deduplicated automatically
- You can minimize the window

### 3. Stopping
- Click "Stop Extraction" to pause
- Data is saved automatically
- Can resume anytime

### 4. Deduplication
- Same phone won't be added twice
- But timestamp updates
- Check "Today" count for new finds

---

## 🔧 If Something Goes Wrong

### App Won't Open
```bash
# Check Python
python --version

# Install missing packages
pip install playwright
playwright install chromium
```

### No Data Appears
1. Check internet connection
2. Verify the live stream is active
3. Wait at least 1 minute
4. Try clicking "Refresh"

### Database Error
```bash
# Close app
# Delete database file
del extracted_data.db
# Restart app
python app.py
```

---

## 📊 Understanding Statistics

**Total**: All records ever extracted
**Today**: Records from today only
**Unique Phones**: Different phone numbers
**Unique Users**: Different usernames

---

## 🎓 Tips for Best Results

1. **Run for 5-10 minutes** to collect good data
2. **Export regularly** to avoid losing data
3. **Use Search** to find specific numbers
4. **Check Today count** to see new finds
5. **Right-click** for copy/delete options

---

## 📞 Need Help?

See full documentation: `DESKTOP_APP_COMPLETE.md`

Or run tests:
```bash
python -c "from database import LocalDatabase; print('OK')"
python -c "from extractor import LeisuExtractor; print('OK')"
```

---

## ✅ Checklist

- [ ] App opens: `python app.py`
- [ ] Start button works
- [ ] Data appears in table
- [ ] Export CSV works
- [ ] Search works

---

**Ready? Run this now:**
```bash
cd d:\colly\livestream-scraper\desktop_app
python app.py
```
