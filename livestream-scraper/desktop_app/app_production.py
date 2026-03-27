#!/usr/bin/env python3
"""
Production Desktop Application for Leisu.com
- Real-time extraction from live streams
- Multilingual support (EN/CN)
- Sustainable extraction with retry logic
- Proper data display
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional, Dict
import json
import os

from database import LocalDatabase
from extractor_fixed import LeisuExtractor, ExtractionResult
from scraper_live import LiveStreamScraper


class I18n:
    """Simple i18n manager."""
    
    TRANSLATIONS = {
        'en': {
            'title': 'Live Stream Phone Extractor',
            'url': 'Target URL',
            'start': '▶ Start Extraction',
            'stop': '⏹ Stop Extraction',
            'refresh': '🔄 Refresh',
            'export': '📁 Export CSV',
            'search': 'Search:',
            'col_id': 'ID',
            'col_phone': 'Phone Number',
            'col_username': 'Username',
            'col_context': 'Context',
            'col_time': 'Time',
            'lang': 'Language',
            'status_ready': 'Ready',
            'status_running': 'Running...',
            'status_found': 'Found {} new',
            'stats_total': 'Total: {}',
            'stats_today': 'Today: {}',
            'stats_phones': 'Phones: {}',
            'stats_users': 'Users: {}',
            'error': 'Error',
            'no_data': 'No data - click Start',
            'menu_copy': 'Copy',
            'menu_delete': 'Delete',
        },
        'zh': {
            'title': '直播手机号提取器',
            'url': '目标网址',
            'start': '▶ 开始提取',
            'stop': '⏹ 停止提取',
            'refresh': '🔄 刷新',
            'export': '📁 导出CSV',
            'search': '搜索:',
            'col_id': 'ID',
            'col_phone': '手机号码',
            'col_username': '用户名',
            'col_context': '内容',
            'col_time': '时间',
            'lang': '语言',
            'status_ready': '就绪',
            'status_running': '运行中...',
            'status_found': '发现 {} 个新号码',
            'stats_total': '总计: {}',
            'stats_today': '今日: {}',
            'stats_phones': '号码: {}',
            'stats_users': '用户: {}',
            'error': '错误',
            'no_data': '无数据 - 点击开始',
            'menu_copy': '复制',
            'menu_delete': '删除',
        }
    }
    
    def __init__(self, lang='zh'):
        self.lang = lang
    
    def set(self, lang):
        self.lang = lang
        # Save preference
        try:
            with open('lang_pref.json', 'w') as f:
                json.dump({'language': lang}, f)
        except:
            pass
    
    def get(self):
        # Load preference
        try:
            if os.path.exists('lang_pref.json'):
                with open('lang_pref.json', 'r') as f:
                    data = json.load(f)
                    self.lang = data.get('language', 'zh')
        except:
            pass
        return self.lang
    
    def _(self, key, *args):
        text = self.TRANSLATIONS.get(self.lang, {}).get(key, 
              self.TRANSLATIONS.get('en', {}).get(key, key))
        return text.format(*args) if args else text


class ProductionApp:
    """Production-ready desktop application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize i18n
        self.i18n = I18n()
        self.i18n.get()  # Load saved preference
        
        self.root.title(self.i18n._('title'))
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Components
        self.db = LocalDatabase()
        self.extractor = LeisuExtractor()
        self.scraper: Optional[LiveStreamScraper] = None
        
        # State
        self.is_running = False
        self.scrape_thread: Optional[threading.Thread] = None
        self.extracted_count = 0
        
        self._create_ui()
        self._refresh_data()
        
        # Auto-refresh every 5 seconds when running
        self._schedule_refresh()
    
    def _create_ui(self):
        """Create user interface with menu bar."""
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # Menu bar
        self._create_menu()
        
        # URL section
        self._create_url_section()
        
        # Control section
        self._create_control_section()
        
        # Data and log
        self._create_data_section()
        
        # Status bar
        self._create_status_bar()
    
    def _create_menu(self):
        """Create menu bar with language switch."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Language menu
        lang_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.i18n._('lang'), menu=lang_menu)
        
        self.lang_var = tk.StringVar(value=self.i18n.get())
        
        lang_menu.add_radiobutton(label='中文', variable=self.lang_var, 
                                   value='zh', command=lambda: self._switch_lang('zh'))
        lang_menu.add_radiobutton(label='English', variable=self.lang_var,
                                   value='en', command=lambda: self._switch_lang('en'))
    
    def _switch_lang(self, lang):
        """Switch language."""
        if lang != self.i18n.get():
            self.i18n.set(lang)
            if messagebox.askyesno(self.i18n._('title'), 
                                   "Restart to apply language change?\n重启以应用语言更改?"):
                self.root.destroy()
                import sys, os
                os.execl(sys.executable, sys.executable, *sys.argv)
    
    def _create_url_section(self):
        """Create URL input."""
        url_frame = ttk.LabelFrame(self.main_frame, text=self.i18n._('url'), padding="5")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        url_frame.columnconfigure(0, weight=1)
        
        self.url_var = tk.StringVar(value="https://live.leisu.com/detail-4244416")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # Preset buttons
        btn_frame = ttk.Frame(url_frame)
        btn_frame.grid(row=0, column=1)
        
        for i, url in enumerate([
            "https://live.leisu.com/detail-4244416",
            "https://live.leisu.com/detail-4244417"
        ], 1):
            ttk.Button(btn_frame, text=f"URL {i}", 
                      command=lambda u=url: self.url_var.set(u),
                      width=8).pack(side=tk.LEFT, padx=2)
    
    def _create_control_section(self):
        """Create controls."""
        ctrl_frame = ttk.Frame(self.main_frame)
        ctrl_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Main buttons
        self.btn_start = ttk.Button(ctrl_frame, text=self.i18n._('start'),
                                    command=self._toggle_extraction, width=18)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ctrl_frame, text=self.i18n._('refresh'),
                   command=self._refresh_data, width=12).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ctrl_frame, text=self.i18n._('export'),
                   command=self._export_csv, width=12).pack(side=tk.LEFT, padx=2)
        
        # Search
        search_frame = ttk.Frame(ctrl_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text=self.i18n._('search')).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text='🔍', command=self._search,
                   width=4).pack(side=tk.LEFT)
    
    def _create_data_section(self):
        """Create data table and log."""
        paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)
        
        # Data table
        data_frame = ttk.LabelFrame(paned, text=self.i18n._('title'), padding="3")
        paned.add(data_frame, weight=3)
        
        # Treeview
        cols = ('id', 'phone', 'username', 'context', 'time')
        self.tree = ttk.Treeview(data_frame, columns=cols, show='headings', height=25)
        
        self._update_headers()
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('phone', width=140, anchor='center')
        self.tree.column('username', width=150)
        self.tree.column('context', width=400)
        self.tree.column('time', width=130, anchor='center')
        
        # Scrollbars
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)
        
        # Log panel
        log_frame = ttk.LabelFrame(paned, text="Log", padding="3")
        paned.add(log_frame, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                   height=25, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state='disabled')
        
        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label=self.i18n._('menu_copy'),
                             command=self._copy_selection)
        self.menu.add_separator()
        self.menu.add_command(label=self.i18n._('menu_delete'),
                             command=self._delete_record)
        
        self.tree.bind('<Button-3>', self._show_menu)
    
    def _update_headers(self):
        """Update column headers."""
        self.tree.heading('id', text=self.i18n._('col_id'))
        self.tree.heading('phone', text=self.i18n._('col_phone'))
        self.tree.heading('username', text=self.i18n._('col_username'))
        self.tree.heading('context', text=self.i18n._('col_context'))
        self.tree.heading('time', text=self.i18n._('col_time'))
    
    def _create_status_bar(self):
        """Create status bar."""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.stats_label = ttk.Label(status_frame,
                                     text=self._get_stats_text(),
                                     font=('Arial', 10, 'bold'))
        self.stats_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value=self.i18n._('status_ready'))
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E))
        self.progress.grid_remove()
    
    def _get_stats_text(self) -> str:
        """Get statistics text."""
        return f"{self.i18n._('stats_total', 0)} | {self.i18n._('stats_today', 0)} | " \
               f"{self.i18n._('stats_phones', 0)} | {self.i18n._('stats_users', 0)}"
    
    def log(self, msg: str):
        """Add log message."""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.status_var.set(msg[:80])
    
    def _toggle_extraction(self):
        """Start or stop extraction."""
        if not self.is_running:
            self._start_extraction()
        else:
            self._stop_extraction()
    
    def _start_extraction(self):
        """Start extraction."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror(self.i18n._('error'), self.i18n._('url'))
            return
        
        self.is_running = True
        self.btn_start.config(text=self.i18n._('stop'))
        self.progress.grid()
        self.progress.start()
        self.url_entry.config(state='disabled')
        
        self.log(f"Starting extraction from {url}")
        
        # Create scraper with callbacks
        self.scraper = LiveStreamScraper(url, self._on_data, self.log)
        self.scrape_thread = threading.Thread(target=self.scraper.start)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def _stop_extraction(self):
        """Stop extraction."""
        self.is_running = False
        if self.scraper:
            self.scraper.stop()
        
        self.btn_start.config(text=self.i18n._('start'))
        self.progress.stop()
        self.progress.grid_remove()
        self.url_entry.config(state='normal')
        self.log("Extraction stopped")
    
    def _on_data(self, results):
        """Handle new data."""
        url = self.url_var.get()
        new_count = 0
        
        for r in results:
            is_new, msg = self.db.add_record(
                phone=r.phone,
                formatted=r.formatted_phone,
                username=r.username or 'Unknown',
                source_url=url,
                context=r.context
            )
            if is_new:
                new_count += 1
                self.extracted_count += 1
        
        if new_count > 0:
            self.log(self.i18n._('status_found', new_count))
            self._refresh_data()
    
    def _refresh_data(self):
        """Refresh data table."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load from database
        records = self.db.get_all_records(limit=1000)
        
        for rec in records:
            self.tree.insert('', tk.END, values=(
                rec.id,
                rec.formatted_phone or rec.phone_number,
                rec.username,
                rec.context[:50] + '...' if len(rec.context) > 50 else rec.context,
                rec.extracted_at[:19]  # Remove microseconds
            ))
        
        # Update stats
        stats = self.db.get_statistics()
        stats_text = (f"{self.i18n._('stats_total', stats['total_records'])} | "
                     f"{self.i18n._('stats_today', stats['today_records'])} | "
                     f"{self.i18n._('stats_phones', stats['unique_phones'])} | "
                     f"{self.i18n._('stats_users', stats['unique_usernames'])}")
        self.stats_label.config(text=stats_text)
    
    def _schedule_refresh(self):
        """Auto-refresh when running."""
        if self.is_running:
            self._refresh_data()
        self.root.after(5000, self._schedule_refresh)
    
    def _search(self):
        """Search records."""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._refresh_data()
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.search_records(keyword)
        for rec in records:
            self.tree.insert('', tk.END, values=(
                rec.id,
                rec.formatted_phone or rec.phone_number,
                rec.username,
                rec.context[:50] + '...' if len(rec.context) > 50 else rec.context,
                rec.extracted_at[:19]
            ))
    
    def _export_csv(self):
        """Export to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
            initialfile=f"phones_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        if filepath and self.db.export_to_csv(filepath):
            self.log(f"Exported: {filepath}")
            messagebox.showinfo(self.i18n._('title'), f"Saved:\n{filepath}")
    
    def _show_menu(self, event):
        """Show context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)
    
    def _copy_selection(self):
        """Copy selected cell."""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], 'values')
            if values:
                text = f"{values[1]} ({values[2]})"
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.status_var.set(f"Copied: {text[:40]}")
    
    def _delete_record(self):
        """Delete record."""
        selected = self.tree.selection()
        if selected:
            rid = self.tree.item(selected[0], 'values')[0]
            if self.db.delete_record(int(rid)):
                self.tree.delete(selected[0])
                self._refresh_data()
    
    def on_close(self):
        """Close handler."""
        if self.is_running:
            self._stop_extraction()
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ProductionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
