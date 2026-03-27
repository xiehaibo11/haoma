#!/usr/bin/env python3
"""
Final working version with proper error handling and real-time updates.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional
import re
import os

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from database import LocalDatabase


class FinalApp:
    """Final production app."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Live Stream Phone Extractor - v3.0")
        self.root.geometry("1300x850")
        
        self.db = LocalDatabase()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.found_phones = set()  # Track found phones in session
        
        self._create_ui()
        self._load_data()
    
    def _create_ui(self):
        """Create UI."""
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main, text="Live Stream Phone Extractor", 
                 font=('Arial', 16, 'bold')).pack(anchor=tk.W)
        ttk.Label(main, text="Extracts phone numbers from leisu.com live streams",
                 font=('Arial', 10)).pack(anchor=tk.W, pady=(0,10))
        
        # URL
        url_frame = ttk.LabelFrame(main, text="Target URL", padding="5")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_var = tk.StringVar(value="https://live.leisu.com/detail-4244416")
        ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11)).pack(fill=tk.X)
        
        # Controls
        ctrl = ttk.Frame(main)
        ctrl.pack(fill=tk.X, pady=5)
        
        self.btn_start = ttk.Button(ctrl, text="▶ START EXTRACTION", 
                                   command=self._toggle, width=20)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ctrl, text="🔄 Refresh Data", 
                  command=self._load_data, width=15).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ctrl, text="📁 Export CSV", 
                  command=self._export, width=15).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ctrl, text="🗑 Clear Database", 
                  command=self._clear_db, width=15).pack(side=tk.LEFT, padx=2)
        
        # Progress
        self.progress = ttk.Progressbar(main, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.pack_forget()
        
        # Data table
        table_frame = ttk.LabelFrame(main, text="Extracted Phone Numbers", padding="5")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        cols = ('id', 'phone', 'username', 'context', 'time')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('phone', text='Phone Number')
        self.tree.heading('username', text='Username/Source')
        self.tree.heading('context', text='Context')
        self.tree.heading('time', text='Extracted At')
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('phone', width=140, anchor='center')
        self.tree.column('username', width=180)
        self.tree.column('context', width=500)
        self.tree.column('time', width=140, anchor='center')
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log
        log_frame = ttk.LabelFrame(main, text="Activity Log", padding="5")
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, 
                               font=('Consolas', 9))
        self.log_text.pack(fill=tk.X)
        
        # Status
        self.status_var = tk.StringVar(value="Ready - Click START to begin")
        ttk.Label(main, textvariable=self.status_var, 
                 relief=tk.SUNKEN, font=('Arial', 10)).pack(fill=tk.X)
        
        # Stats
        self.stats_var = tk.StringVar(value="Records: 0 | Phones: 0 | This Session: 0")
        ttk.Label(main, textvariable=self.stats_var, 
                 font=('Arial', 10, 'bold')).pack(fill=tk.X, pady=(5,0))
    
    def log(self, msg: str):
        """Log message."""
        ts = datetime.now().strftime('%H:%M:%S')
        line = f"[{ts}] {msg}\n"
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.status_var.set(msg)
        print(line.strip())
    
    def _toggle(self):
        if not self.running:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.running = True
        self.btn_start.config(text="⏹ STOP")
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.found_phones.clear()
        
        self.log("=" * 50)
        self.log("STARTING EXTRACTION")
        self.log(f"URL: {url}")
        self.log("=" * 50)
        
        self.thread = threading.Thread(target=self._scrape, args=(url,))
        self.thread.daemon = True
        self.thread.start()
    
    def _stop(self):
        self.running = False
        self.btn_start.config(text="▶ START EXTRACTION")
        self.progress.stop()
        self.progress.pack_forget()
        self.log("STOPPING...")
    
    def _scrape(self, url: str):
        """Scrape with detailed logging."""
        try:
            with sync_playwright() as p:
                self.log("Launching browser...")
                browser = p.chromium.launch(headless=True)
                
                self.log("Creating browser context...")
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                
                self.log(f"Navigating to: {url}")
                try:
                    # 45 second timeout
                    page.goto(url, wait_until='domcontentloaded', timeout=45000)
                    self.log("Page loaded successfully")
                except PlaywrightTimeout:
                    self.log("WARNING: Page load timeout, but continuing...")
                except Exception as e:
                    self.log(f"Navigation error: {e}")
                    return
                
                self.log("Waiting 15 seconds for page to settle...")
                time.sleep(15)
                
                self.log("Starting extraction loop (checking every 5 seconds)...")
                check_num = 0
                
                while self.running:
                    check_num += 1
                    self.log(f"--- Check #{check_num} ---")
                    
                    try:
                        # Get page content
                        self.log("Reading page content...")
                        body_text = page.inner_text('body')
                        self.log(f"Page text length: {len(body_text)} chars")
                        
                        # Find phone numbers
                        phones = re.findall(r'1[3-9]\d{9}', body_text)
                        self.log(f"Found {len(phones)} phone number patterns")
                        
                        new_found = 0
                        for phone in set(phones):
                            if phone not in self.found_phones:
                                self.found_phones.add(phone)
                                
                                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                                
                                # Find context
                                idx = body_text.find(phone)
                                context = ""
                                if idx >= 0:
                                    start = max(0, idx - 60)
                                    end = min(len(body_text), idx + 60)
                                    context = body_text[start:end].strip()
                                
                                # Extract username from context (simple heuristic)
                                username = "Unknown"
                                if ':' in context:
                                    parts = context.split(':')
                                    if len(parts) > 1:
                                        username = parts[0].strip()[-20:]  # Last 20 chars
                                
                                # Add to database
                                is_new, _ = self.db.add_record(
                                    phone=phone,
                                    formatted=formatted,
                                    username=username,
                                    source_url=url,
                                    context=context
                                )
                                
                                if is_new:
                                    new_found += 1
                                    self.log(f"✓ NEW PHONE: {formatted}")
                                    self._update_ui()
                        
                        if new_found == 0:
                            self.log("No new phones this check")
                        
                        # Scroll periodically
                        if check_num % 3 == 0:
                            self.log("Scrolling page...")
                            page.evaluate('window.scrollBy(0, 600)')
                        
                    except Exception as e:
                        self.log(f"Error during check: {e}")
                    
                    self.log("Waiting 5 seconds...")
                    time.sleep(5)
                
                self.log("Closing browser...")
                browser.close()
        
        except Exception as e:
            self.log(f"FATAL ERROR: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        self.running = False
        self.btn_start.config(text="▶ START EXTRACTION")
        self.progress.stop()
        self.progress.pack_forget()
        self.log("EXTRACTION STOPPED")
        self._load_data()
    
    def _update_ui(self):
        """Update UI from main thread."""
        self.root.after(100, self._load_data)
    
    def _load_data(self):
        """Load data into table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.get_all_records(limit=1000)
        
        for rec in records:
            self.tree.insert('', tk.END, values=(
                rec.id,
                rec.formatted_phone or rec.phone_number,
                rec.username or "Unknown",
                (rec.context or "")[:60] + "..." if len(rec.context or "") > 60 else (rec.context or ""),
                rec.extracted_at[:19]
            ))
        
        stats = self.db.get_statistics()
        self.stats_var.set(
            f"Records: {stats['total_records']} | "
            f"Unique Phones: {stats['unique_phones']} | "
            f"This Session: {len(self.found_phones)}"
        )
    
    def _export(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"phones_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        if filepath and self.db.export_to_csv(filepath):
            self.log(f"Exported: {filepath}")
            messagebox.showinfo("Success", f"Exported to:\n{filepath}")
    
    def _clear_db(self):
        if messagebox.askyesno("Confirm", "Delete ALL data?", icon='warning'):
            if self.db.clear_all():
                self.found_phones.clear()
                self._load_data()
                self.log("Database cleared")


def main():
    root = tk.Tk()
    app = FinalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
