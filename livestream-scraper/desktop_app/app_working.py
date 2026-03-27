#!/usr/bin/env python3
"""
Simplified working version - focuses on reliability over features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional
import re

from playwright.sync_api import sync_playwright

from database import LocalDatabase


class SimpleApp:
    """Simplified working app."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Live Stream Phone Extractor")
        self.root.geometry("1200x800")
        
        self.db = LocalDatabase()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self._create_ui()
        self._refresh()
    
    def _create_ui(self):
        """Create simple UI."""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # URL
        ttk.Label(frame, text="URL:").pack(anchor=tk.W)
        self.url_var = tk.StringVar(value="https://live.leisu.com/detail-4244416")
        ttk.Entry(frame, textvariable=self.url_var).pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_start = ttk.Button(btn_frame, text="Start", command=self._toggle)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Refresh", command=self._refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Export", command=self._export).pack(side=tk.LEFT, padx=2)
        
        # Data table
        cols = ('id', 'phone', 'username', 'time')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('phone', text='Phone Number')
        self.tree.heading('username', text='Username')
        self.tree.heading('time', text='Time')
        
        self.tree.column('id', width=50)
        self.tree.column('phone', width=150)
        self.tree.column('username', width=200)
        self.tree.column('time', width=150)
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log
        ttk.Label(frame, text="Log:").pack(anchor=tk.W, pady=(10,0))
        self.log_text = tk.Text(frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)
    
    def log(self, msg: str):
        """Add log message."""
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.status_var.set(msg)
        print(f"[{ts}] {msg}")
    
    def _toggle(self):
        if not self.running:
            self._start()
        else:
            self._stop()
    
    def _start(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Enter URL")
            return
        
        self.running = True
        self.btn_start.config(text="Stop")
        self.log("Starting...")
        
        self.thread = threading.Thread(target=self._run_scraper, args=(url,))
        self.thread.daemon = True
        self.thread.start()
    
    def _stop(self):
        self.running = False
        self.btn_start.config(text="Start")
        self.log("Stopping...")
    
    def _run_scraper(self, url: str):
        """Run scraper with simple approach."""
        try:
            with sync_playwright() as p:
                self.log("Launching browser...")
                browser = p.chromium.launch(headless=True)
                
                self.log("Opening page...")
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800}
                )
                page = context.new_page()
                
                self.log(f"Loading {url}...")
                try:
                    # Use shorter timeout, don't wait for full load
                    page.goto(url, timeout=30000)
                    self.log("Page loaded")
                except Exception as e:
                    self.log(f"Load warning: {e}")
                
                self.log("Waiting for content...")
                time.sleep(10)
                
                self.log("Starting extraction loop...")
                check_count = 0
                
                while self.running:
                    check_count += 1
                    self.log(f"Check #{check_count}")
                    
                    try:
                        # Get all page text
                        body = page.inner_text('body')
                        
                        # Find phone numbers
                        phones = re.findall(r'1[3-9]\d{9}', body)
                        
                        if phones:
                            self.log(f"Found {len(phones)} phone patterns")
                            
                            for phone in set(phones):
                                # Simple dedup check
                                formatted = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                                
                                # Find context (50 chars around phone)
                                idx = body.find(phone)
                                context = ""
                                if idx >= 0:
                                    start = max(0, idx - 50)
                                    end = min(len(body), idx + 50)
                                    context = body[start:end].replace('\n', ' ')
                                
                                # Add to database
                                is_new, _ = self.db.add_record(
                                    phone=phone,
                                    formatted=formatted,
                                    username="",  # Will extract from context
                                    source_url=url,
                                    context=context
                                )
                                
                                if is_new:
                                    self.log(f"NEW: {formatted}")
                        
                        # Scroll
                        if check_count % 3 == 0:
                            page.evaluate('window.scrollBy(0, 500)')
                            self.log("Scrolled")
                    
                    except Exception as e:
                        self.log(f"Check error: {e}")
                    
                    time.sleep(5)
                
                self.log("Closing browser...")
                browser.close()
        
        except Exception as e:
            self.log(f"FATAL ERROR: {e}")
        
        self.running = False
        self.btn_start.config(text="Start")
        self.log("Stopped")
    
    def _refresh(self):
        """Refresh data display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.get_all_records(limit=500)
        
        for rec in records:
            self.tree.insert('', tk.END, values=(
                rec.id,
                rec.formatted_phone or rec.phone_number,
                rec.username or "Unknown",
                rec.extracted_at[:19]
            ))
        
        stats = self.db.get_statistics()
        self.log(f"Stats: {stats['total_records']} records, {stats['unique_phones']} phones")
    
    def _export(self):
        """Export to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"phones_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        if filepath and self.db.export_to_csv(filepath):
            self.log(f"Exported to {filepath}")
            messagebox.showinfo("Success", f"Saved:\n{filepath}")


def main():
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
