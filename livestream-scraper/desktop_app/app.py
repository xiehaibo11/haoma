#!/usr/bin/env python3
"""
Desktop Application for Leisu.com Phone Number Extraction

A simple, focused GUI application that extracts phone numbers and usernames
from live stream comments and stores them locally with deduplication.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional

from database import LocalDatabase
from extractor import LeisuExtractor
from scraper import LeisuScraper


class DesktopApp:
    """
    Main desktop application class.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the desktop application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Live Stream Phone Extractor - Leisu.com")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Initialize components
        self.db = LocalDatabase()
        self.extractor = LeisuExtractor()
        self.scraper: Optional[LeisuScraper] = None
        
        # State
        self.is_running = False
        self.scrape_thread: Optional[threading.Thread] = None
        self.update_interval = 2000  # Update UI every 2 seconds
        
        # Build UI
        self._create_ui()
        
        # Initial data load
        self._refresh_data()
        
        # Start auto-update
        self._schedule_update()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)  # Data section expands
        
        # === URL Section ===
        self._create_url_section()
        
        # === Control Section ===
        self._create_control_section()
        
        # === Data Display Section ===
        self._create_data_section()
        
        # === Status Bar ===
        self._create_status_bar()
    
    def _create_url_section(self):
        """Create URL input section."""
        url_frame = ttk.LabelFrame(self.main_frame, text="Target URL", padding="10")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        # URL Entry
        self.url_var = tk.StringVar(
            value="https://live.leisu.com/detail-4244416"
        )
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # URL Preset Buttons
        preset_frame = ttk.Frame(url_frame)
        preset_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(
            preset_frame, 
            text="Preset 1",
            command=lambda: self.url_var.set("https://live.leisu.com/detail-4244416")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            preset_frame,
            text="Preset 2", 
            command=lambda: self.url_var.set("https://live.leisu.com/detail-4244417")
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_control_section(self):
        """Create control buttons section."""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop Button
        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Extraction",
            command=self._toggle_scraping,
            width=20
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh Button
        ttk.Button(
            control_frame,
            text="🔄 Refresh Data",
            command=self._refresh_data,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Export Button
        ttk.Button(
            control_frame,
            text="📁 Export CSV",
            command=self._export_csv,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Search Frame
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            search_frame,
            text="Search",
            command=self._search_data,
            width=8
        ).pack(side=tk.LEFT)
        
        # Bind enter key to search
        search_entry.bind('<Return>', lambda e: self._search_data())
    
    def _create_data_section(self):
        """Create data display section with treeview."""
        data_frame = ttk.LabelFrame(self.main_frame, text="Extracted Data", padding="10")
        data_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)
        
        # Create Treeview
        columns = ('id', 'phone', 'username', 'context', 'time')
        self.tree = ttk.Treeview(
            data_frame,
            columns=columns,
            show='headings',
            height=20
        )
        
        # Define column headings
        self.tree.heading('id', text='ID')
        self.tree.heading('phone', text='Phone Number')
        self.tree.heading('username', text='Username')
        self.tree.heading('context', text='Context')
        self.tree.heading('time', text='Extracted At')
        
        # Define column widths
        self.tree.column('id', width=50, anchor=tk.CENTER)
        self.tree.column('phone', width=150, anchor=tk.CENTER)
        self.tree.column('username', width=200)
        self.tree.column('context', width=500)
        self.tree.column('time', width=150, anchor=tk.CENTER)
        
        # Scrollbars
        vsb = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(data_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Phone", command=self._copy_phone)
        self.context_menu.add_command(label="Copy Username", command=self._copy_username)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Record", command=self._delete_record)
        
        self.tree.bind('<Button-3>', self._show_context_menu)  # Right-click
        self.tree.bind('<Double-1>', self._on_double_click)    # Double-click
        
        # Statistics Frame
        stats_frame = ttk.Frame(data_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="Total: 0 | Today: 0 | Unique Phones: 0 | Unique Users: 0",
            font=('Arial', 10, 'bold')
        )
        self.stats_label.pack(side=tk.LEFT)
        
        ttk.Button(
            stats_frame,
            text="Clear All Data",
            command=self._clear_all_data
        ).pack(side=tk.RIGHT)
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.main_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.progress.grid_remove()  # Hidden by default
    
    def _toggle_scraping(self):
        """Start or stop the scraping process."""
        if not self.is_running:
            self._start_scraping()
        else:
            self._stop_scraping()
    
    def _start_scraping(self):
        """Start the scraping thread."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.is_running = True
        self.start_btn.config(text="⏹ Stop Extraction")
        self.status_var.set(f"Scraping: {url}")
        self.progress.grid()
        self.progress.start()
        
        # Disable URL editing while running
        self.url_entry.config(state='disabled')
        
        # Start scraper in background thread
        self.scraper = LeisuScraper(url, self._on_new_data)
        self.scrape_thread = threading.Thread(target=self.scraper.start)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def _stop_scraping(self):
        """Stop the scraping process."""
        self.is_running = False
        
        if self.scraper:
            self.scraper.stop()
        
        self.start_btn.config(text="▶ Start Extraction")
        self.status_var.set("Stopped")
        self.progress.stop()
        self.progress.grid_remove()
        
        # Re-enable URL editing
        self.url_entry.config(state='normal')
        
        # Refresh data display
        self._refresh_data()
    
    def _on_new_data(self, results: list):
        """
        Callback for new data from scraper.
        
        Args:
            results: List of ExtractionResult objects
        """
        url = self.url_var.get()
        new_count = 0
        
        for result in results:
            is_new, _ = self.db.add_record(
                phone=result.phone,
                formatted=result.formatted_phone,
                username=result.username,
                source_url=url,
                context=result.context
            )
            if is_new:
                new_count += 1
        
        if new_count > 0:
            self.status_var.set(f"Found {new_count} new phone number(s)")
    
    def _refresh_data(self):
        """Refresh the data display."""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load data from database
        records = self.db.get_all_records(limit=1000)
        
        # Insert into tree
        for record in records:
            self.tree.insert('', tk.END, values=(
                record.id,
                record.formatted_phone or record.phone_number,
                record.username,
                record.context[:80] + '...' if len(record.context) > 80 else record.context,
                record.extracted_at
            ))
        
        # Update statistics
        self._update_stats()
        
        self.status_var.set(f"Data refreshed - {len(records)} records loaded")
    
    def _search_data(self):
        """Search data by keyword."""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._refresh_data()
            return
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Search
        records = self.db.search_records(keyword)
        
        # Insert results
        for record in records:
            self.tree.insert('', tk.END, values=(
                record.id,
                record.formatted_phone or record.phone_number,
                record.username,
                record.context[:80] + '...' if len(record.context) > 80 else record.context,
                record.extracted_at
            ))
        
        self.status_var.set(f"Search found {len(records)} record(s)")
    
    def _update_stats(self):
        """Update statistics display."""
        stats = self.db.get_statistics()
        self.stats_label.config(
            text=f"Total: {stats['total_records']} | "
                 f"Today: {stats['today_records']} | "
                 f"Unique Phones: {stats['unique_phones']} | "
                 f"Unique Users: {stats['unique_usernames']}"
        )
    
    def _export_csv(self):
        """Export data to CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"extracted_phones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filepath:
            if self.db.export_to_csv(filepath):
                messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
                self.status_var.set(f"Exported to {filepath}")
            else:
                messagebox.showerror("Error", "Failed to export data")
    
    def _clear_all_data(self):
        """Clear all data from database."""
        if messagebox.askyesno(
            "Confirm",
            "Are you sure you want to delete ALL data?\nThis cannot be undone!",
            icon='warning'
        ):
            if self.db.clear_all():
                self._refresh_data()
                messagebox.showinfo("Success", "All data has been cleared")
            else:
                messagebox.showerror("Error", "Failed to clear data")
    
    def _show_context_menu(self, event):
        """Show right-click context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        """Handle double-click on row."""
        item = self.tree.selection()[0]
        values = self.tree.item(item, 'values')
        if values:
            # Show detail dialog
            self._show_detail_dialog(values)
    
    def _show_detail_dialog(self, values):
        """Show detail dialog for a record."""
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
        
        ttk.Label(dialog, text=f"Extracted: {values[4]}", font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _copy_phone(self):
        """Copy phone number to clipboard."""
        selected = self.tree.selection()
        if selected:
            phone = self.tree.item(selected[0], 'values')[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(phone)
            self.status_var.set(f"Copied: {phone}")
    
    def _copy_username(self):
        """Copy username to clipboard."""
        selected = self.tree.selection()
        if selected:
            username = self.tree.item(selected[0], 'values')[2]
            self.root.clipboard_clear()
            self.root.clipboard_append(username)
            self.status_var.set(f"Copied: {username}")
    
    def _delete_record(self):
        """Delete selected record."""
        selected = self.tree.selection()
        if selected:
            record_id = self.tree.item(selected[0], 'values')[0]
            if messagebox.askyesno("Confirm", "Delete this record?"):
                if self.db.delete_record(int(record_id)):
                    self.tree.delete(selected[0])
                    self._update_stats()
                    self.status_var.set("Record deleted")
    
    def _schedule_update(self):
        """Schedule periodic UI updates."""
        self._update_stats()
        if self.is_running:
            self._refresh_data()
        self.root.after(self.update_interval, self._schedule_update)
    
    def on_closing(self):
        """Handle window close event."""
        if self.is_running:
            self._stop_scraping()
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = DesktopApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
