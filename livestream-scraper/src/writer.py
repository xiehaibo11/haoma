"""
Output writing module.

Handles writing results to various formats (CSV, JSON, TXT).
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class OutputWriter:
    """
    Manages output to multiple file formats.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize output writer.
        
        Args:
            config: Output configuration dict
        """
        self.config = config
        self.output_dir = Path(config.get('directory', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = config.get('filename_prefix', 'phones')
        self.base_filename = f"{prefix}_{timestamp}"
        
        # Track if headers have been written
        self.csv_header_written = False
        
    def write_all(self, phones: Dict[str, Dict]):
        """
        Write results to all enabled formats.
        
        Args:
            phones: Dictionary of phone numbers with metadata
        """
        formats = self.config.get('formats', {})
        
        if formats.get('csv', True):
            self.write_csv(phones)
        
        if formats.get('json', True):
            self.write_json(phones)
        
        if formats.get('txt', True):
            self.write_txt(phones)
    
    def write_csv(self, phones: Dict[str, Dict], append: bool = False):
        """
        Write results to CSV file.
        
        Args:
            phones: Dictionary of phone numbers
            append: Whether to append or overwrite
        """
        filepath = self.output_dir / f"{self.base_filename}.csv"
        mode = 'a' if append else 'w'
        
        with open(filepath, mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not append or not self.csv_header_written:
                writer.writerow([
                    'timestamp', 'phone_raw', 'phone_formatted', 
                    'pattern', 'context', 'count'
                ])
                self.csv_header_written = True
            
            # Write data
            for phone, data in phones.items():
                writer.writerow([
                    data.get('first_seen', ''),
                    phone,
                    data.get('formatted', ''),
                    data.get('pattern_name', ''),
                    data.get('context', '')[:self.config.get('max_context_length', 100)],
                    data.get('count', 1)
                ])
    
    def write_json(self, phones: Dict[str, Dict]):
        """
        Write results to JSON file.
        
        Args:
            phones: Dictionary of phone numbers
        """
        filepath = self.output_dir / f"{self.base_filename}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(phones, f, ensure_ascii=False, indent=2)
    
    def write_txt(self, phones: Dict[str, Dict]):
        """
        Write simple list to TXT file.
        
        Args:
            phones: Dictionary of phone numbers
        """
        filepath = self.output_dir / f"{self.base_filename}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Extracted Phone Numbers\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Total: {len(phones)}\n\n")
            
            for phone, data in sorted(phones.items()):
                f.write(f"{data.get('formatted', phone)}\n")
    
    def append_single(self, phone: str, data: Dict):
        """
        Append a single phone number to CSV (for real-time logging).
        
        Args:
            phone: Phone number string
            data: Metadata dict
        """
        filepath = self.output_dir / f"{self.base_filename}.csv"
        
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not self.csv_header_written:
                writer.writerow([
                    'timestamp', 'phone_raw', 'phone_formatted',
                    'pattern', 'context', 'count'
                ])
                self.csv_header_written = True
            
            writer.writerow([
                data.get('first_seen', ''),
                phone,
                data.get('formatted', ''),
                data.get('pattern_name', ''),
                data.get('context', '')[:self.config.get('max_context_length', 100)],
                data.get('count', 1)
            ])
    
    def save_backup(self, phones: Dict[str, Dict]):
        """
        Save backup to temporary file.
        
        Args:
            phones: Dictionary of phone numbers
        """
        filepath = self.output_dir / "phones_backup.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(phones, f, ensure_ascii=False, indent=2)
    
    def get_output_paths(self) -> Dict[str, str]:
        """
        Get paths to all output files.
        
        Returns:
            Dictionary of format -> filepath
        """
        paths = {}
        formats = self.config.get('formats', {})
        
        if formats.get('csv', True):
            paths['csv'] = str(self.output_dir / f"{self.base_filename}.csv")
        if formats.get('json', True):
            paths['json'] = str(self.output_dir / f"{self.base_filename}.json")
        if formats.get('txt', True):
            paths['txt'] = str(self.output_dir / f"{self.base_filename}.txt")
        
        return paths
