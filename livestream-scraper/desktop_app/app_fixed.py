#!/usr/bin/env python3
"""
Fixed Desktop Application with improved scraper and debug logging.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional

from database import LocalDatabase
from extractor_fixed import LeisuExtractor
from scraper_improved import LeisuScraper


class DesktopApp:
    """Fixed desktop application with debug panel."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Live Stream Phone Extractor - Leisu.com")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Components
        self.db = LocalDatabase()
        self.extractor = LeisuExtractor()
        self.scraper: Optional[LeisuScraper] = None
        
        # State
        self.is_running = False
        self.scrape_thread: Optional[threading.Thread] = None
        
        # Build UI
        self._create_ui()
        
        # Initial data load
        self._refresh_data()
    
    def _create_ui(self):
        """Create user interface with debug panel."""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
        
        # === URL Section ===
        url_frame = ttk.LabelFrame(self.main_frame, text="Target URL", padding="10")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_var = tk.StringVar(value="https://live.leisu.com/detail-4244416")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        preset_frame = ttk.Frame(url_frame)
        preset_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(preset_frame, text="Preset 1",
                  command=lambda: self.url_var.set("https://live.leisu.com/detail-4244416")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Preset 2",
                  command=lambda: self.url_var.set("https://live.leisu.com/detail-4244417")).pack(side=tk.LEFT, padx=2)
        
        # === Control Section ===
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="▶ Start Extraction",
                                   command=self._toggle_scraping, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Refresh Data",
                  command=self._refresh_data, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="📁 Export CSV",
                  command=self._export_csv, width=15).pack(side=tk.LEFT, padx=5)
        
        # Test extraction button
        ttk.Button(control_frame, text="🧪 Test Extraction",
                  command=self._test_extraction, width=15).pack(side=tk.LEFT, padx=5)
        
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Search", command=self._search_data, width=8).pack(side=tk.LEFT)
        
        # === Main Content (Data + Debug) ===
        content_frame = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        content_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Data Table
        data_frame = ttk.LabelFrame(content_frame, text="Extracted Data", padding="5")
        content_frame.add(data_frame, weight=2)
        
        columns = ('id', 'phone', 'username', 'context', 'time')
        self.tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('phone', text='Phone Number')
        self.tree.heading('username', text='Username')
        self.tree.heading('context', text='Context')
        self.tree.heading('time', text='Extracted At')
        
        self.tree.column('id', width=50, anchor=tk.CENTER)
        self.tree.column('phone', width=150, anchor=tk.CENTER)
        self.tree.column('username', width=180)
        self.tree.column('context', width=400)
        self.tree.column('time', width=150, anchor=tk.CENTER)
        
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)
        
        # Debug/Log Panel
        debug_frame = ttk.LabelFrame(content_frame, text="Debug Log", padding="5")
        content_frame.add(debug_frame, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(debug_frame, wrap=tk.WORD, height=15,
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state='disabled')
        
        # Statistics
        stats_frame = ttk.Frame(data_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Total: 0 | Today: 0 | Unique Phones: 0 | Unique Users: 0",
                                    font=('Arial', 10, 'bold'))
        self.stats_label.pack(side=tk.LEFT)
        
        ttk.Button(stats_frame, text="Clear All Data", command=self._clear_all_data).pack(side=tk.RIGHT)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready - Click 'Start Extraction' to begin")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate', length=200)
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.progress.grid_remove()
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Phone", command=self._copy_phone)
        self.context_menu.add_command(label="Copy Username", command=self._copy_username)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Record", command=self._delete_record)
        
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def log(self, message: str):
        """Add message to debug log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.status_var.set(message)
    
    def _toggle_scraping(self):
        if not self.is_running:
            self._start_scraping()
        else:
            self._stop_scraping()
    
    def _start_scraping(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.is_running = True
        self.start_btn.config(text="⏹ Stop Extraction")
        self.progress.grid()
        self.progress.start()
        self.url_entry.config(state='disabled')
        
        self.log("Starting extraction...")
        
        self.scraper = LeisuScraper(url, self._on_new_data, self.log)
        self.scrape_thread = threading.Thread(target=self.scraper.start)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def _stop_scraping(self):
        self.is_running = False
        if self.scraper:
            self.scraper.stop()
        
        self.start_btn.config(text="▶ Start Extraction")
        self.progress.stop()
        self.progress.grid_remove()
        self.url_entry.config(state='normal')
        self.log("Extraction stopped")
        self._refresh_data()
    
    def _test_extraction(self):
        """Test extraction without browser."""
        test_texts = [
            "张三13800138000",
            "Contact me at 139-1234-5678",
            "User: 李四15056789012",
            "Call 15123456789 for info"
        ]
        
        self.log("=== TEST MODE ===")
        
        found_count = 0
        for text in test_texts:
            results = self.extractor.extract_all(comment=text)
            if results:
                found_count += len(results)
                for r in results:
                    self.log(f"Test found: {r.formatted_phone} in '{text[:30]}...'")
                    # Add to database
                    self.db.add_record(
                        phone=r.phone,
                        formatted=r.formatted_phone,
                        username="TestUser",
                        source_url="test://test",
                        context=text
                    )
        
        self.log(f"=== Test complete: {found_count} phone(s) found ===")
        self._refresh_data()
        messagebox.showinfo("Test Complete", f"Found {found_count} phone number(s) in test data.")
    
    def _on_new_data(self, results: list):
        url = self.url_var.get()
        new_count = 0
        
        for result in results:
            is_new, msg = self.db.add_record(
                phone=result.phone,
                formatted=result.formatted_phone,
                username=result.username,
                source_url=url,
                context=result.context
            )
            if is_new:
                new_count += 1
        
        if new_count > 0:
            self.log(f"✓ Added {new_count} new phone number(s) to database")
            self._refresh_data()
    
    def _refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.get_all_records(limit=1000)
        
        for record in records:
            self.tree.insert('', tk.END, values=(
                record.id,
                record.formatted_phone or record.phone_number,
                record.username,
                record.context[:60] + '...' if len(record.context) > 60 else record.context,
                record.extracted_at
            ))
        
        self._update_stats()
    
    def _search_data(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            self._refresh_data()
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.search_records(keyword)
        
        for record in records:
            self.tree.insert('', tk.END, values=(
                record.id,
                record.formatted_phone or record.phone_number,
                record.username,
                record.context[:60] + '...' if len(record.context) > 60 else record.context,
                record.extracted_at
            ))
        
        self.log(f"Search found {len(records)} record(s)")
    
    def _update_stats(self):
        stats = self.db.get_statistics()
        self.stats_label.config(
            text=f"Total: {stats['total_records']} | "
                 f"Today: {stats['today_records']} | "
                 f"Unique Phones: {stats['unique_phones']} | "
                 f"Unique Users: {stats['unique_usernames']}"
        )
    
    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"extracted_phones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filepath:
            if self.db.export_to_csv(filepath):
                self.log(f"Exported to: {filepath}")
                messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
            else:
                messagebox.showerror("Error", "Failed to export")
    
    def _clear_all_data(self):
        if messagebox.askyesno("Confirm", "Delete ALL data? This cannot be undone!", icon='warning'):
            if self.db.clear_all():
                self._refresh_data()
                self.log("All data cleared")
                messagebox.showinfo("Success", "All data has been cleared")
    
    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        item = self.tree.selection()[0]
        values = self.tree.item(item, 'values')
        if values:
            self._show_detail_dialog(values)
    
    def _show_detail_dialog(self, values):
        dialog = tk.Toplevel(self.root)
        dialog.title("Record Details")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text=f"ID: {values[0]}", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text=f"Phone: {values[1]}", font=('Arial', 11)).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text=f"Username: {values[2]}", font=('Arial', 11)).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text="Context:", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        context_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=10)
        context_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        context_text.insert(tk.END, values[3])
        context_text.config(state='disabled')
        
        ttk.Label(dialog, text=f"Time: {values[4]}", font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _copy_phone(self):
        selected = self.tree.selection()
        if selected:
            phone = self.tree.item(selected[0], 'values')[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(phone)
            self.status_var.set(f"Copied: {phone}")
    
    def _copy_username(self):
        selected = self.tree.selection()
        if selected:
            username = self.tree.item(selected[0], 'values')[2]
            self.root.clipboard_clear()
            self.root.clipboard_append(username)
            self.status_var.set(f"Copied: {username}")
    
    def _delete_record(self):
        selected = self.tree.selection()
        if selected:
            record_id = self.tree.item(selected[0], 'values')[0]
            if messagebox.askyesno("Confirm", "Delete this record?"):
                if self.db.delete_record(int(record_id)):
                    self.tree.delete(selected[0])
                    self._update_stats()
                    self.log("Record deleted")
    
    def on_closing(self):
        if self.is_running:
            self._stop_scraping()
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = DesktopApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
