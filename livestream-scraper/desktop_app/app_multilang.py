#!/usr/bin/env python3
"""
Multi-language Desktop Application for Leisu.com Phone Number Extraction

Supports English and Chinese (Simplified) with easy extensibility for more languages.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime
from typing import Optional, Dict

import i18n
from database import LocalDatabase
from extractor import LeisuExtractor
from scraper import LeisuScraper


class LanguageSelector:
    """Language selector dialog."""
    
    @staticmethod
    def show(parent) -> Optional[str]:
        """
        Show language selection dialog.
        
        Returns:
            Selected language code or None
        """
        dialog = tk.Toplevel(parent)
        dialog.title("Select Language / 选择语言")
        dialog.geometry("300x200")
        dialog.transient(parent)
        dialog.grab_set()
        
        selected_lang = None
        
        def select(lang):
            nonlocal selected_lang
            selected_lang = lang
            dialog.destroy()
        
        ttk.Label(dialog, text="Please select language:", 
                 font=('Arial', 12)).pack(pady=10)
        ttk.Label(dialog, text="请选择语言:", 
                 font=('SimSun', 12)).pack(pady=5)
        
        ttk.Button(dialog, text="English", 
                  command=lambda: select('en')).pack(fill='x', padx=20, pady=5)
        
        ttk.Button(dialog, text="中文 (Chinese)", 
                  command=lambda: select('zh')).pack(fill='x', padx=20, pady=5)
        
        parent.wait_window(dialog)
        return selected_lang


class DesktopApp:
    """
    Main desktop application class with multi-language support.
    """
    
    def __init__(self, root: tk.Tk, language: str = 'zh'):
        """
        Initialize the desktop application.
        
        Args:
            root: Tkinter root window
            language: Language code ('en' or 'zh')
        """
        self.root = root
        
        # Set language
        i18n.set_language(language)
        
        # Initialize components
        self.db = LocalDatabase()
        self.extractor = LeisuExtractor()
        self.scraper: Optional[LeisuScraper] = None
        
        # State
        self.is_running = False
        self.scrape_thread: Optional[threading.Thread] = None
        self.update_interval = 2000
        self.current_language = language
        
        # UI elements storage for language switching
        self.ui_elements: Dict[str, any] = {}
        self.column_headers = {}
        
        # Build UI
        self._create_ui()
        
        # Initial data load
        self._refresh_data()
        
        # Start auto-update
        self._schedule_update()
    
    def _create_ui(self):
        """Create the user interface."""
        self.root.title(i18n._('app_title'))
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # Create menu bar
        self._create_menu()
        
        # Create sections
        self._create_url_section()
        self._create_control_section()
        self._create_data_section()
        self._create_status_bar()
    
    def _create_menu(self):
        """Create menu bar with language option."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Language menu
        lang_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=i18n._('language'), menu=lang_menu)
        
        lang_menu.add_command(label=i18n._('lang_english'), 
                             command=lambda: self._switch_language('en'))
        lang_menu.add_command(label=i18n._('lang_chinese'), 
                             command=lambda: self._switch_language('zh'))
        
        self.ui_elements['lang_menu'] = lang_menu
    
    def _switch_language(self, lang: str):
        """Switch application language."""
        if lang != self.current_language:
            i18n.set_language(lang)
            self.current_language = lang
            
            # Show confirmation and restart
            if messagebox.askyesno(
                "Restart Required / 需要重启",
                "Language changed. Restart application to apply changes?\n"
                "语言已更改。重启应用以应用更改？"
            ):
                self.root.destroy()
                # Restart with new language
                import sys
                import os
                os.execl(sys.executable, sys.executable, *sys.argv)
    
    def _create_url_section(self):
        """Create URL input section."""
        url_frame = ttk.LabelFrame(self.main_frame, text=i18n._('url_section'), padding="10")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        # URL Entry
        self.url_var = tk.StringVar(value="https://live.leisu.com/detail-4244416")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Preset buttons
        preset_frame = ttk.Frame(url_frame)
        preset_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.ui_elements['preset1_btn'] = ttk.Button(
            preset_frame, 
            text=i18n._('preset1'),
            command=lambda: self.url_var.set("https://live.leisu.com/detail-4244416")
        )
        self.ui_elements['preset1_btn'].pack(side=tk.LEFT, padx=2)
        
        self.ui_elements['preset2_btn'] = ttk.Button(
            preset_frame,
            text=i18n._('preset2'), 
            command=lambda: self.url_var.set("https://live.leisu.com/detail-4244417")
        )
        self.ui_elements['preset2_btn'].pack(side=tk.LEFT, padx=2)
    
    def _create_control_section(self):
        """Create control buttons section."""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop Button
        self.ui_elements['start_btn'] = ttk.Button(
            control_frame,
            text=i18n._('start_extraction'),
            command=self._toggle_scraping,
            width=20
        )
        self.ui_elements['start_btn'].pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh Button
        self.ui_elements['refresh_btn'] = ttk.Button(
            control_frame,
            text=i18n._('refresh_data'),
            command=self._refresh_data,
            width=15
        )
        self.ui_elements['refresh_btn'].pack(side=tk.LEFT, padx=5)
        
        # Export Button
        self.ui_elements['export_btn'] = ttk.Button(
            control_frame,
            text=i18n._('export_csv'),
            command=self._export_csv,
            width=15
        )
        self.ui_elements['export_btn'].pack(side=tk.LEFT, padx=5)
        
        # Search Frame
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text=i18n._('search')).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        self.ui_elements['search_btn'] = ttk.Button(
            search_frame,
            text=i18n._('search_btn'),
            command=self._search_data,
            width=8
        )
        self.ui_elements['search_btn'].pack(side=tk.LEFT)
        
        search_entry.bind('<Return>', lambda e: self._search_data())
    
    def _create_data_section(self):
        """Create data display section with treeview."""
        data_frame = ttk.LabelFrame(self.main_frame, text=i18n._('data_section'), padding="10")
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
        
        # Store column references for language switching
        self.column_headers = {
            'id': 'col_id',
            'phone': 'col_phone',
            'username': 'col_username',
            'context': 'col_context',
            'time': 'col_time'
        }
        
        self._update_column_headers()
        
        # Column widths
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
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label=i18n._('menu_copy_phone'), 
            command=self._copy_phone
        )
        self.context_menu.add_command(
            label=i18n._('menu_copy_username'), 
            command=self._copy_username
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label=i18n._('menu_delete'), 
            command=self._delete_record
        )
        
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Double-1>', self._on_double_click)
        
        # Statistics Frame
        stats_frame = ttk.Frame(data_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(
            stats_frame,
            text=self._get_stats_text(),
            font=('Arial', 10, 'bold')
        )
        self.stats_label.pack(side=tk.LEFT)
        
        self.ui_elements['clear_btn'] = ttk.Button(
            stats_frame,
            text=i18n._('clear_all'),
            command=self._clear_all_data
        )
        self.ui_elements['clear_btn'].pack(side=tk.RIGHT)
    
    def _update_column_headers(self):
        """Update treeview column headers with current language."""
        for col, key in self.column_headers.items():
            self.tree.heading(col, text=i18n._(key))
    
    def _get_stats_text(self) -> str:
        """Get statistics text in current language."""
        return (f"{i18n._('stats_total', 0)} | "
                f"{i18n._('stats_today', 0)} | "
                f"{i18n._('stats_unique_phones', 0)} | "
                f"{i18n._('stats_unique_users', 0)}")
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_var = tk.StringVar(value=i18n._('status_ready'))
        status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.progress = ttk.Progressbar(
            self.main_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.progress.grid_remove()
    
    def _toggle_scraping(self):
        """Start or stop scraping."""
        if not self.is_running:
            self._start_scraping()
        else:
            self._stop_scraping()
    
    def _start_scraping(self):
        """Start scraping."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error / 错误", i18n._('error_url'))
            return
        
        self.is_running = True
        self.ui_elements['start_btn'].config(text=i18n._('stop_extraction'))
        self.status_var.set(i18n._('status_running'))
        self.progress.grid()
        self.progress.start()
        
        self.url_entry.config(state='disabled')
        
        self.scraper = LeisuScraper(url, self._on_new_data)
        self.scrape_thread = threading.Thread(target=self.scraper.start)
        self.scrape_thread.daemon = True
        self.scrape_thread.start()
    
    def _stop_scraping(self):
        """Stop scraping."""
        self.is_running = False
        
        if self.scraper:
            self.scraper.stop()
        
        self.ui_elements['start_btn'].config(text=i18n._('start_extraction'))
        self.status_var.set(i18n._('status_stopped'))
        self.progress.stop()
        self.progress.grid_remove()
        
        self.url_entry.config(state='normal')
        self._refresh_data()
    
    def _on_new_data(self, results: list):
        """Handle new data from scraper."""
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
            self.status_var.set(i18n._('status_found', new_count))
    
    def _refresh_data(self):
        """Refresh data display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        records = self.db.get_all_records(limit=1000)
        
        for record in records:
            self.tree.insert('', tk.END, values=(
                record.id,
                record.formatted_phone or record.phone_number,
                record.username,
                record.context[:80] + '...' if len(record.context) > 80 else record.context,
                record.extracted_at
            ))
        
        self._update_stats()
        self.status_var.set(f"{i18n._('status_ready')} - {len(records)} records")
    
    def _search_data(self):
        """Search data."""
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
                record.context[:80] + '...' if len(record.context) > 80 else record.context,
                record.extracted_at
            ))
        
        self.status_var.set(f"Search found {len(records)} records")
    
    def _update_stats(self):
        """Update statistics."""
        stats = self.db.get_statistics()
        stats_text = (f"{i18n._('stats_total', stats['total_records'])} | "
                     f"{i18n._('stats_today', stats['today_records'])} | "
                     f"{i18n._('stats_unique_phones', stats['unique_phones'])} | "
                     f"{i18n._('stats_unique_users', stats['unique_usernames'])}")
        self.stats_label.config(text=stats_text)
    
    def _export_csv(self):
        """Export to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"extracted_phones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filepath:
            if self.db.export_to_csv(filepath):
                messagebox.showinfo("Success / 成功", i18n._('export_success', filepath))
                self.status_var.set(f"Exported to {filepath}")
            else:
                messagebox.showerror("Error / 错误", i18n._('export_error'))
    
    def _clear_all_data(self):
        """Clear all data."""
        if messagebox.askyesno(
            "Confirm / 确认",
            i18n._('confirm_clear'),
            icon='warning'
        ):
            if self.db.clear_all():
                self._refresh_data()
                messagebox.showinfo("Success / 成功", i18n._('all_data_cleared'))
            else:
                messagebox.showerror("Error / 错误", "Failed to clear")
    
    def _show_context_menu(self, event):
        """Show context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Update menu labels with current language
            self.context_menu.entryconfig(0, label=i18n._('menu_copy_phone'))
            self.context_menu.entryconfig(1, label=i18n._('menu_copy_username'))
            self.context_menu.entryconfig(3, label=i18n._('menu_delete'))
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        """Handle double click."""
        item = self.tree.selection()[0]
        values = self.tree.item(item, 'values')
        if values:
            self._show_detail_dialog(values)
    
    def _show_detail_dialog(self, values):
        """Show detail dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(i18n._('dialog_details'))
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text=f"ID: {values[0]}", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text=f"{i18n._('col_phone')}: {values[1]}", font=('Arial', 11)).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text=f"{i18n._('col_username')}: {values[2]}", font=('Arial', 11)).pack(anchor=tk.W, pady=5)
        ttk.Label(dialog, text=f"{i18n._('col_context')}:", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        context_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=10)
        context_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        context_text.insert(tk.END, values[3])
        context_text.config(state='disabled')
        
        ttk.Label(dialog, text=f"{i18n._('col_time')}: {values[4]}", font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        
        ttk.Button(dialog, text=i18n._('dialog_close'), command=dialog.destroy).pack(pady=10)
    
    def _copy_phone(self):
        """Copy phone."""
        selected = self.tree.selection()
        if selected:
            phone = self.tree.item(selected[0], 'values')[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(phone)
            self.status_var.set(i18n._('copied', phone))
    
    def _copy_username(self):
        """Copy username."""
        selected = self.tree.selection()
        if selected:
            username = self.tree.item(selected[0], 'values')[2]
            self.root.clipboard_clear()
            self.root.clipboard_append(username)
            self.status_var.set(i18n._('copied', username))
    
    def _delete_record(self):
        """Delete record."""
        selected = self.tree.selection()
        if selected:
            record_id = self.tree.item(selected[0], 'values')[0]
            if messagebox.askyesno("Confirm / 确认", i18n._('confirm_delete')):
                if self.db.delete_record(int(record_id)):
                    self.tree.delete(selected[0])
                    self._update_stats()
                    self.status_var.set(i18n._('record_deleted'))
    
    def _schedule_update(self):
        """Schedule update."""
        self._update_stats()
        if self.is_running:
            self._refresh_data()
        self.root.after(self.update_interval, self._schedule_update)
    
    def on_closing(self):
        """Handle closing."""
        if self.is_running:
            self._stop_scraping()
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    
    # Show language selector on first run
    # Comment out next 4 lines to skip language selection
    lang = LanguageSelector.show(root)
    if lang is None:
        lang = 'zh'  # Default to Chinese
    
    # Or set language directly:
    # lang = 'zh'  # Chinese
    # lang = 'en'  # English
    
    app = DesktopApp(root, language=lang)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
