#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized version with Chinese UI and fixed layout
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import re
import sqlite3
import sys
from datetime import datetime

# Language strings
LANG = {
    'zh': {
        'title': '雷速直播手机号提取器',
        'subtitle': '基于网站结构分析：widget.namitiyu.com  iframe',
        'match_id': '比赛ID：',
        'start': '▶ 开始提取',
        'stop': '⏹ 停止提取',
        'refresh': '🔄 刷新数据',
        'export': '📁 导出CSV',
        'log': '运行日志',
        'data': '提取数据',
        'col_id': '序号',
        'col_phone': '手机号码',
        'col_username': '用户名',
        'col_context': '内容上下文',
        'col_time': '提取时间',
        'stats': '记录：{} | 本次：{} | 唯一：{}',
        'ready': '就绪',
        'starting': '开始提取比赛ID：{}',
        'found_iframe': '发现聊天iframe',
        'found_phones': '发现 {} 个新号码',
        'saved': '已保存：{}',
        'stopped': '已停止',
        'export_success': '导出成功：{}',
    },
    'en': {
        'title': 'Leisu Live Phone Extractor',
        'subtitle': 'Based on: widget.namitiyu.com iframe',
        'match_id': 'Match ID:',
        'start': '▶ START',
        'stop': '⏹ STOP',
        'refresh': '🔄 Refresh',
        'export': '📁 Export CSV',
        'log': 'Activity Log',
        'data': 'Extracted Data',
        'col_id': 'ID',
        'col_phone': 'Phone Number',
        'col_username': 'Username',
        'col_context': 'Context',
        'col_time': 'Time',
        'stats': 'Records: {} | Session: {} | Unique: {}',
        'ready': 'Ready',
        'starting': 'Starting match ID: {}',
        'found_iframe': 'Found chat iframe',
        'found_phones': 'Found {} new phones',
        'saved': 'Saved: {}',
        'stopped': 'Stopped',
        'export_success': 'Exported: {}',
    }
}

NOISE_KEYWORDS = (
    '日志id',
    'logid',
    '访问验证',
    '请按住滑块',
    '为保证您的正常访问',
    '动画直播',
    '热议',
    '赛况',
    '阵容',
)


def init_db():
    conn = sqlite3.connect('phones.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS phones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        formatted TEXT,
        username TEXT,
        context TEXT,
        url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


class OptimizedApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = 'zh'  # Default Chinese
        self.L = LANG[self.lang]
        
        self.root.title(self.L['title'])
        self.root.geometry("1400x900")
        
        init_db()
        self.running = False
        self.found_phones = set()
        
        self._create_ui()
        self._load_data()
    
    def _create_ui(self):
        # Main frame
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main, text=self.L['title'], 
                 font=('Microsoft YaHei', 20, 'bold')).pack(anchor=tk.W)
        ttk.Label(main, text=self.L['subtitle'], 
                 font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # Control bar
        ctrl = ttk.Frame(main)
        ctrl.pack(fill=tk.X, pady=10)
        
        ttk.Label(ctrl, text=self.L['match_id'], 
                 font=('Microsoft YaHei', 12)).pack(side=tk.LEFT)
        
        self.id_var = tk.StringVar(value="4336493")
        ttk.Entry(ctrl, textvariable=self.id_var, width=15,
                 font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        
        self.btn_start = ttk.Button(ctrl, text=self.L['start'], 
                                   command=self._toggle, width=15)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(ctrl, text=self.L['refresh'],
                  command=self._load_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(ctrl, text=self.L['export'],
                  command=self._export).pack(side=tk.LEFT, padx=5)
        
        # Language toggle
        ttk.Button(ctrl, text='English/中文',
                  command=self._toggle_lang).pack(side=tk.RIGHT)
        
        # Progress
        self.progress = ttk.Progressbar(main, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.pack_forget()
        
        # Paned window for log and table
        paned = ttk.PanedWindow(main, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log section (top)
        log_frame = ttk.LabelFrame(paned, text=self.L['log'], padding="5")
        paned.add(log_frame, weight=1)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD,
                               font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Data table section (bottom)
        table_frame = ttk.LabelFrame(paned, text=self.L['data'], padding="5")
        paned.add(table_frame, weight=3)
        
        # Treeview with proper columns
        cols = ('id', 'phone', 'username', 'context', 'time')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings')
        
        # Configure columns with proper widths
        self.tree.heading('id', text=self.L['col_id'])
        self.tree.heading('phone', text=self.L['col_phone'])
        self.tree.heading('username', text=self.L['col_username'])
        self.tree.heading('context', text=self.L['col_context'])
        self.tree.heading('time', text=self.L['col_time'])
        
        self.tree.column('id', width=60, anchor='center')
        self.tree.column('phone', width=150, anchor='center')
        self.tree.column('username', width=200, anchor='w')
        self.tree.column('context', width=500, anchor='w')
        self.tree.column('time', width=150, anchor='center')
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value=self.L['stats'].format(0, 0, 0))
        ttk.Label(main, textvariable=self.status_var,
                 font=('Microsoft YaHei', 11, 'bold'),
                 relief=tk.SUNKEN).pack(fill=tk.X, pady=(5, 0))
    
    def log(self, msg: str):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f"[{ts}] {msg}\n"
        if threading.current_thread() is threading.main_thread():
            self._append_log_line(line)
        else:
            self.root.after(0, lambda l=line: self._append_log_line(l))

        # 控制台输出做编码保护，避免 gbk 环境下因特殊字符中断线程
        try:
            print(line.strip())
        except UnicodeEncodeError:
            try:
                sys.stdout.buffer.write(line.encode('utf-8', errors='replace'))
                sys.stdout.flush()
            except Exception:
                pass

    def _append_log_line(self, line: str):
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
    
    def _toggle_lang(self):
        self.lang = 'en' if self.lang == 'zh' else 'zh'
        self.L = LANG[self.lang]
        self.root.destroy()
        import sys, os
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def _toggle(self):
        if not self.running:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        match_id = self.id_var.get().strip()
        if not match_id:
            return
        
        self.running = True
        self.btn_start.config(text=self.L['stop'])
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        
        self.log("=" * 50)
        self.log(self.L['starting'].format(match_id))
        self.log("=" * 50)
        
        threading.Thread(target=self._scrape, 
                        args=(match_id,), daemon=True).start()
    
    def _stop(self):
        self.running = False
        self.btn_start.config(text=self.L['start'])
        self.progress.stop()
        self.progress.pack_forget()
        self.log(self.L['stopped'])
    
    def _scrape(self, match_id: str):
        from playwright.sync_api import sync_playwright
        
        url = f"https://live.leisu.com/detail-{match_id}"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 375, 'height': 812},
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)'
                )
                page = context.new_page()
                
                self.log(f"Loading: {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                self.log("Page loaded")
                
                self.log("Waiting for chat iframe...")
                time.sleep(12)
                
                # Try to get iframe
                iframe = page.query_selector('iframe[src*=\"namitiyu\"]')
                target_page = iframe.content_frame() if iframe else page
                
                if iframe:
                    self.log(self.L['found_iframe'])

                self.log("进入持续提取模式（仅手动停止才结束）")
                check_count = 0
                while self.running:
                    check_count += 1
                    
                    try:
                        records = self._collect_chat_records(target_page)
                        if check_count % 5 == 1:
                            self.log(f"第 {check_count} 轮扫描，聊天行数: {len(records)}")

                        new_count = 0
                        for username, message in records:
                            username = self._sanitize_username(username)
                            message = self._sanitize_context(message)
                            if not message:
                                continue
                            candidate_text = f"{username} {message}".strip()
                            for phone in self._extract_phones(candidate_text):
                                if phone in self.found_phones:
                                    continue
                                self.found_phones.add(phone)
                                new_count += 1
                                self._save(
                                    phone=phone,
                                    formatted=phone,  # 统一11位纯数字输出
                                    username=username or "未知用户",
                                    context=message,
                                    url=url,
                                )
                                self.log(f"  + {phone} | {username or '未知用户'}")

                        if new_count > 0:
                            self.log(self.L['found_phones'].format(new_count))
                            self.root.after(0, self._load_data)
                        elif check_count % 8 == 0:
                            self.log("本轮无新增号码，继续监控...")

                        self._scroll_chat_only(target_page)
                        
                    except Exception as e:
                        self.log(f"Error: {e}")
                    
                    time.sleep(3)
                
                browser.close()
        
        except Exception as e:
            self.log(f"Fatal: {e}")
        
        self.root.after(0, self._stop)

    def _collect_chat_records(self, target_page):
        """从聊天列表结构提取 (用户名, 消息正文)。"""
        selectors = [
            '#msg-list ul > li',
            '.msg-list ul > li',
            '.discussionArea .discussion .msg-list ul > li',
        ]
        name_selectors = [
            '.name',
            '.username',
            '.user-name',
            '.nickname',
            'a.name',
            'a[class*="name"]',
            '[class*="name"] a',
        ]
        msg_selectors = [
            '.content-txt',
            '.msg-content',
            '.content',
            '.message',
            '.text',
            '.comment',
            '.msg-txt',
        ]

        records = []
        seen = set()
        for selector in selectors:
            try:
                items = target_page.query_selector_all(selector)
            except Exception:
                continue
            if not items:
                continue
            for li in items[:400]:
                row_text = self._compact_text(self._pick_text(li, [], fallback=True))
                parsed_username, parsed_message = self._split_chat_row(row_text)

                username = self._sanitize_username(self._pick_text(li, name_selectors))
                message = self._sanitize_context(self._pick_text(li, msg_selectors))

                if (not username or self._is_noise_username(username)) and parsed_username:
                    username = self._sanitize_username(parsed_username)
                if (not message or self._is_noise_context(message)) and parsed_message:
                    message = self._sanitize_context(parsed_message)
                if not message and row_text:
                    message = self._sanitize_context(row_text)

                if self._is_noise_context(message):
                    continue
                if not username and not message:
                    continue
                key = (username, message)
                if key in seen:
                    continue
                seen.add(key)
                records.append((username, message))
            if records:
                return records
        return records

    def _extract_phones(self, text: str):
        """提取并归一化手机号为11位数字。"""
        phones = set()
        if not text:
            return []
        pattern = (
            r'(?<![0-9A-Za-z])1[3-9]\d{9}(?![0-9A-Za-z])'
            r'|(?<![0-9A-Za-z])1[3-9]\d[\s\-\.]?\d{4}[\s\-\.]?\d{4}(?![0-9A-Za-z])'
        )
        for m in re.findall(pattern, text):
            digits = re.sub(r'[^\d]', '', m)
            if re.fullmatch(r'1[3-9]\d{9}', digits):
                phones.add(digits)
        return sorted(phones)

    def _compact_text(self, text: str) -> str:
        if not text:
            return ''
        return re.sub(r'\s+', ' ', str(text)).strip()

    def _split_chat_row(self, row_text: str):
        """
        尝试把一行聊天拆成 (用户名, 消息)，兼容:
        "Lv10 用户abc: 内容"
        """
        text = self._compact_text(row_text)
        if not text:
            return '', ''

        text = re.sub(r'^(?:Lv|LV)\d+\s*', '', text)
        parts = re.split(r'[：:]', text, maxsplit=1)
        if len(parts) != 2:
            return '', text

        left = self._compact_text(parts[0])
        left = re.sub(r'^(?:Lv|LV)\d+\s*', '', left)
        left = left.strip('[]【】()（）|- ')
        left = re.sub(r'^[^A-Za-z0-9\u4e00-\u9fff]+', '', left)
        right = self._compact_text(parts[1])
        return left, right

    def _is_noise_username(self, username: str) -> bool:
        name = self._compact_text(username)
        if not name:
            return True
        if len(name) < 2 or len(name) > 36:
            return True
        if re.fullmatch(r'\d+', name):
            return True
        lowered = name.lower()
        return any(k in lowered for k in NOISE_KEYWORDS)

    def _is_noise_context(self, context: str) -> bool:
        msg = self._compact_text(context)
        if not msg:
            return True
        lowered = msg.lower()
        if any(k in lowered for k in NOISE_KEYWORDS):
            return True
        if re.fullmatch(r'[\d\.\%\s]+', msg):
            # 纯数字文本里若包含手机号，则视为有效
            digits = re.sub(r'[^\d]', '', msg)
            if not re.fullmatch(r'1[3-9]\d{9}', digits):
                return True
        return False

    def _sanitize_username(self, username: str) -> str:
        name = self._compact_text(username)
        if not name:
            return ''
        name = re.sub(r'^(?:Lv|LV)\d+\s*', '', name)
        name = re.sub(r'[：:]\s*$', '', name).strip()
        name = name.strip('[]【】()（）|- ')
        if self._is_noise_username(name):
            return ''
        return name

    def _sanitize_context(self, context: str) -> str:
        msg = self._compact_text(context)
        if not msg:
            return ''
        msg = msg.replace('\r', ' ').replace('\n', ' ')
        msg = re.sub(r'\s+', ' ', msg).strip()
        if len(msg) > 180:
            msg = msg[:180]
        if self._is_noise_context(msg):
            return ''
        return msg

    def _pick_text(self, elem, selectors, fallback=False):
        for selector in selectors:
            try:
                n = elem.query_selector(selector)
                if not n:
                    continue
                t = ' '.join((n.inner_text() or '').split()).strip()
                if t:
                    return t
            except Exception:
                continue
        if fallback:
            try:
                return ' '.join((elem.inner_text() or '').split()).strip()
            except Exception:
                return ''
        return ''

    def _scroll_chat_only(self, target_page):
        """仅滚动聊天容器，不滚动整页。"""
        try:
            target_page.evaluate(
                """
                () => {
                    const nano = document.querySelector('#msg-list .nano-content, .msg-list .nano-content');
                    if (nano) {
                        nano.scrollTop = nano.scrollHeight;
                        return;
                    }
                    const list = document.querySelector('#msg-list ul, .msg-list ul');
                    if (list && list.parentElement) {
                        list.parentElement.scrollTop = list.parentElement.scrollHeight;
                    }
                }
                """
            )
        except Exception:
            pass
    
    def _save(self, phone, formatted, username, context, url):
        username = self._sanitize_username(username) or "未知用户"
        context = self._sanitize_context(context)
        if self._is_noise_context(context) and self._is_noise_username(username):
            return

        conn = sqlite3.connect('phones.db')
        c = conn.cursor()
        c.execute('SELECT 1 FROM phones WHERE phone=? LIMIT 1', (phone,))
        if c.fetchone():
            conn.close()
            return
        c.execute('''INSERT OR IGNORE INTO phones 
                     (phone, formatted, username, context, url)
                     VALUES (?, ?, ?, ?, ?)''',
                  (phone, formatted, username, context, url))
        conn.commit()
        conn.close()
    
    def _load_data(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load from DB
        conn = sqlite3.connect('phones.db')
        c = conn.cursor()
        c.execute('''
            SELECT * FROM (
                SELECT * FROM phones ORDER BY id DESC LIMIT 500
            ) t
            ORDER BY id ASC
        ''')
        rows = c.fetchall()
        
        # Get unique count
        c.execute('SELECT COUNT(DISTINCT phone) FROM phones')
        unique = c.fetchone()[0]
        conn.close()
        
        # Insert with proper data
        visible_count = 0
        for row in rows:
            username = self._sanitize_username(row[3] or "")
            context = self._sanitize_context(row[4] or "")

            # 历史脏数据隐藏（避免“日志ID/访问验证”污染表格）
            if not username and not context:
                continue
            if not username:
                username = "未知用户"

            self.tree.insert('', tk.END, values=(
                row[0],  # ID
                row[2] or row[1],  # Formatted or phone
                username,
                context[:60] + "..." if len(context) > 60 else context,
                row[6][:19] if row[6] else ""  # Time (not URL!)
            ))
            visible_count += 1
        
        self.status_var.set(self.L['stats'].format(
            visible_count, len(self.found_phones), unique))
    
    def _export(self):
        import csv
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"phones_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        
        if not filepath:
            return
        
        conn = sqlite3.connect('phones.db')
        c = conn.cursor()
        c.execute('SELECT * FROM phones')
        rows = c.fetchall()
        conn.close()
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Phone', 'Formatted', 'Username', 
                           'Context', 'URL', 'Time'])
            writer.writerows(rows)
        
        self.log(self.L['export_success'].format(filepath))
        messagebox.showinfo("Success", self.L['export_success'].format(filepath))


def main():
    root = tk.Tk()
    app = OptimizedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
