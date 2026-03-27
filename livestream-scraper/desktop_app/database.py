"""
Local database for desktop app - stores extracted phone numbers and usernames.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedRecord:
    """Represents an extracted phone record."""
    id: int
    phone_number: str
    formatted_phone: str
    username: str
    source_url: str
    context: str
    extracted_at: str
    is_valid: bool


class LocalDatabase:
    """
    SQLite database for local storage of extracted data.
    Handles deduplication and data persistence.
    """
    
    def __init__(self, db_path: str = "extracted_data.db"):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection and tables."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                formatted_phone TEXT,
                username TEXT,
                source_url TEXT NOT NULL,
                context TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN DEFAULT 1,
                UNIQUE(phone_number, source_url)
            )
        ''')
        
        # Create indexes for fast lookup
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_phone ON extracted_phones(phone_number)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username ON extracted_phones(username)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_extracted_at ON extracted_phones(extracted_at)
        ''')
        
        self.conn.commit()
    
    def add_record(self, phone: str, formatted: str, username: str, 
                   source_url: str, context: str = "") -> Tuple[bool, str]:
        """
        Add a new record with deduplication.
        
        Args:
            phone: Raw phone number
            formatted: Formatted phone number
            username: Username who posted
            source_url: Source URL
            context: Context text
            
        Returns:
            Tuple of (is_new, message)
        """
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO extracted_phones 
                (phone_number, formatted_phone, username, source_url, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (phone, formatted, username, source_url, context))
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                return True, "New record added"
            else:
                # Update occurrence count indirectly via last_seen
                self.cursor.execute('''
                    UPDATE extracted_phones 
                    SET extracted_at = CURRENT_TIMESTAMP
                    WHERE phone_number = ? AND source_url = ?
                ''', (phone, source_url))
                self.conn.commit()
                return False, "Duplicate - updated timestamp"
                
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
    
    def get_all_records(self, limit: int = 1000, 
                        order_by: str = "extracted_at DESC") -> List[ExtractedRecord]:
        """
        Get all extracted records.
        
        Args:
            limit: Maximum records to return
            order_by: Sort order
            
        Returns:
            List of ExtractedRecord objects
        """
        self.cursor.execute(f'''
            SELECT id, phone_number, formatted_phone, username, 
                   source_url, context, extracted_at, is_valid
            FROM extracted_phones
            ORDER BY {order_by}
            LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return [ExtractedRecord(*row) for row in rows]
    
    def get_records_by_date(self, date_str: str) -> List[ExtractedRecord]:
        """
        Get records from specific date (YYYY-MM-DD).
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of records
        """
        self.cursor.execute('''
            SELECT id, phone_number, formatted_phone, username,
                   source_url, context, extracted_at, is_valid
            FROM extracted_phones
            WHERE date(extracted_at) = ?
            ORDER BY extracted_at DESC
        ''', (date_str,))
        
        rows = self.cursor.fetchall()
        return [ExtractedRecord(*row) for row in rows]
    
    def search_records(self, keyword: str) -> List[ExtractedRecord]:
        """
        Search records by keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching records
        """
        pattern = f"%{keyword}%"
        self.cursor.execute('''
            SELECT id, phone_number, formatted_phone, username,
                   source_url, context, extracted_at, is_valid
            FROM extracted_phones
            WHERE phone_number LIKE ? 
               OR username LIKE ?
               OR context LIKE ?
            ORDER BY extracted_at DESC
        ''', (pattern, pattern, pattern))
        
        rows = self.cursor.fetchall()
        return [ExtractedRecord(*row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # Total records
        self.cursor.execute('SELECT COUNT(*) FROM extracted_phones')
        stats['total_records'] = self.cursor.fetchone()[0]
        
        # Today's records
        self.cursor.execute('''
            SELECT COUNT(*) FROM extracted_phones 
            WHERE date(extracted_at) = date('now')
        ''')
        stats['today_records'] = self.cursor.fetchone()[0]
        
        # Unique phones
        self.cursor.execute('SELECT COUNT(DISTINCT phone_number) FROM extracted_phones')
        stats['unique_phones'] = self.cursor.fetchone()[0]
        
        # Unique usernames
        self.cursor.execute('SELECT COUNT(DISTINCT username) FROM extracted_phones WHERE username != ""')
        stats['unique_usernames'] = self.cursor.fetchone()[0]
        
        # Latest record
        self.cursor.execute('''
            SELECT extracted_at FROM extracted_phones 
            ORDER BY extracted_at DESC LIMIT 1
        ''')
        result = self.cursor.fetchone()
        stats['latest_record'] = result[0] if result else None
        
        return stats
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Export all records to CSV.
        
        Args:
            filepath: Output file path
            
        Returns:
            True if successful
        """
        import csv
        
        try:
            records = self.get_all_records(limit=100000)
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Phone Number', 'Formatted', 'Username', 
                               'Source URL', 'Context', 'Extracted At', 'Valid'])
                
                for record in records:
                    writer.writerow([
                        record.id,
                        record.phone_number,
                        record.formatted_phone,
                        record.username,
                        record.source_url,
                        record.context,
                        record.extracted_at,
                        record.is_valid
                    ])
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def delete_record(self, record_id: int) -> bool:
        """
        Delete a specific record.
        
        Args:
            record_id: Record ID to delete
            
        Returns:
            True if deleted
        """
        try:
            self.cursor.execute('DELETE FROM extracted_phones WHERE id = ?', (record_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def clear_all(self) -> bool:
        """Clear all records (use with caution)."""
        try:
            self.cursor.execute('DELETE FROM extracted_phones')
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
