"""
Database models and operations for the scraper.
Uses SQLAlchemy for ORM support.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class PhoneRecord(Base):
    """Database model for extracted phone numbers."""
    __tablename__ = 'phone_records'
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False, index=True)
    formatted_number = Column(String(30))
    source_stream = Column(String(500), nullable=False, index=True)
    username = Column(String(200), index=True)
    context = Column(Text)
    pattern_type = Column(String(50))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_phone_stream', 'phone_number', 'source_stream'),
        Index('idx_first_seen', 'first_seen'),
    )


class StreamRecord(Base):
    """Database model for tracked streams."""
    __tablename__ = 'stream_records'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False, unique=True, index=True)
    platform = Column(String(50), index=True)
    status = Column(String(20), default='active')  # active, paused, error, completed
    last_check = Column(DateTime)
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    phones_found = Column(Integer, default=0)
    check_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(Integer, default=5)  # 1-10, lower = higher priority
    check_interval = Column(Integer, default=30)  # seconds


class ExtractionLog(Base):
    """Log of all extraction attempts."""
    __tablename__ = 'extraction_logs'
    
    id = Column(Integer, primary_key=True)
    stream_url = Column(String(500), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    new_phones_found = Column(Integer, default=0)
    total_phones_seen = Column(Integer, default=0)
    duration_seconds = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)


@dataclass
class DatabaseStats:
    """Statistics about the database."""
    total_phones: int
    total_streams: int
    active_streams: int
    today_phones: int
    top_streams: List[Dict]


class Database:
    """
    Database manager for the scraper.
    
    Handles all database operations including:
    - Phone number storage and deduplication
    - Stream tracking
    - Extraction logging
    - Statistics
    """
    
    def __init__(self, db_path: str = "./output/scraper.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine with connection pooling
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    @contextmanager
    def session(self) -> Session:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy session
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_phone(self, phone: str, formatted: str, stream_url: str, 
                  username: str = None, context: str = None, 
                  pattern_type: str = None) -> bool:
        """
        Add or update a phone number record.
        
        Args:
            phone: Raw phone number
            formatted: Formatted phone number
            stream_url: Source stream URL
            username: Username who posted the phone
            context: Surrounding text context
            pattern_type: Type of pattern that matched
            
        Returns:
            True if this is a new phone number, False if updated
        """
        with self.session() as s:
            # Check if phone already exists for this stream
            existing = s.query(PhoneRecord).filter_by(
                phone_number=phone,
                source_stream=stream_url
            ).first()
            
            if existing:
                # Update existing record
                existing.last_seen = datetime.utcnow()
                existing.occurrence_count += 1
                if context and not existing.context:
                    existing.context = context
                return False
            else:
                # Create new record
                record = PhoneRecord(
                    phone_number=phone,
                    formatted_number=formatted,
                    source_stream=stream_url,
                    username=username,
                    context=context,
                    pattern_type=pattern_type
                )
                s.add(record)
                
                # Update stream phone count
                stream = s.query(StreamRecord).filter_by(url=stream_url).first()
                if stream:
                    stream.phones_found += 1
                    stream.updated_at = datetime.utcnow()
                
                return True
    
    def add_stream(self, url: str, platform: str = None, 
                   priority: int = 5, check_interval: int = 30) -> bool:
        """
        Add a new stream to track.
        
        Args:
            url: Stream URL
            platform: Platform name (e.g., 'leisu', 'youtube')
            priority: Priority level (1-10, lower = higher)
            check_interval: Seconds between checks
            
        Returns:
            True if new stream added, False if already exists
        """
        with self.session() as s:
            existing = s.query(StreamRecord).filter_by(url=url).first()
            if existing:
                return False
            
            stream = StreamRecord(
                url=url,
                platform=platform,
                priority=priority,
                check_interval=check_interval
            )
            s.add(stream)
            return True
    
    def get_streams_to_check(self, limit: int = 10) -> List[StreamRecord]:
        """
        Get streams that are due for checking.
        
        Args:
            limit: Maximum number of streams to return
            
        Returns:
            List of StreamRecord objects
        """
        with self.session() as s:
            # Get active streams that haven't been checked recently
            streams = s.query(StreamRecord).filter(
                StreamRecord.status.in_(['active', 'error']),
                (StreamRecord.last_check == None) | 
                (StreamRecord.last_check < datetime.utcnow())
            ).order_by(
                StreamRecord.priority.asc(),
                StreamRecord.last_check.asc()
            ).limit(limit).all()
            
            # Detach from session so they can be used after session closes
            for stream in streams:
                s.expunge(stream)
            
            return streams
    
    def update_stream_status(self, url: str, status: str, 
                            error: str = None, phones_found: int = 0):
        """
        Update stream status after check.
        
        Args:
            url: Stream URL
            status: New status ('active', 'error', 'paused', 'completed')
            error: Error message if status is 'error'
            phones_found: Number of new phones found in this check
        """
        with self.session() as s:
            stream = s.query(StreamRecord).filter_by(url=url).first()
            if stream:
                stream.status = status
                stream.last_check = datetime.utcnow()
                stream.check_count += 1
                stream.phones_found += phones_found
                stream.updated_at = datetime.utcnow()
                
                if error:
                    stream.last_error = error
                    stream.error_count += 1
    
    def log_extraction(self, stream_url: str, new_phones: int, 
                      total_phones: int, duration: int, 
                      success: bool = True, error: str = None):
        """
        Log an extraction attempt.
        
        Args:
            stream_url: URL that was checked
            new_phones: Number of new phones found
            total_phones: Total phones seen
            duration: How long the check took
            success: Whether the check succeeded
            error: Error message if failed
        """
        with self.session() as s:
            log = ExtractionLog(
                stream_url=stream_url,
                new_phones_found=new_phones,
                total_phones_seen=total_phones,
                duration_seconds=duration,
                success=success,
                error_message=error
            )
            s.add(log)
    
    def get_stats(self) -> DatabaseStats:
        """
        Get database statistics.
        
        Returns:
            DatabaseStats object
        """
        with self.session() as s:
            total_phones = s.query(PhoneRecord).count()
            total_streams = s.query(StreamRecord).count()
            active_streams = s.query(StreamRecord).filter_by(status='active').count()
            
            # Today's phones
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_phones = s.query(PhoneRecord).filter(
                PhoneRecord.first_seen >= today
            ).count()
            
            # Top streams by phone count
            top_streams = s.query(StreamRecord).order_by(
                StreamRecord.phones_found.desc()
            ).limit(5).all()
            
            top_streams_data = [{
                'url': stream.url,
                'phones_found': stream.phones_found,
                'status': stream.status
            } for stream in top_streams]
            
            return DatabaseStats(
                total_phones=total_phones,
                total_streams=total_streams,
                active_streams=active_streams,
                today_phones=today_phones,
                top_streams=top_streams_data
            )
    
    def get_phones_by_stream(self, stream_url: str) -> List[Dict]:
        """
        Get all phones from a specific stream.
        
        Args:
            stream_url: Stream URL
            
        Returns:
            List of phone records as dictionaries
        """
        with self.session() as s:
            records = s.query(PhoneRecord).filter_by(
                source_stream=stream_url
            ).order_by(PhoneRecord.first_seen.desc()).all()
            
            return [{
                'phone': r.phone_number,
                'formatted': r.formatted_number,
                'username': r.username,
                'context': r.context,
                'first_seen': r.first_seen.isoformat(),
                'occurrence_count': r.occurrence_count
            } for r in records]
    
    def export_phones(self, filepath: str, format: str = 'csv'):
        """
        Export all phones to a file.
        
        Args:
            filepath: Output file path
            format: 'csv' or 'json'
        """
        import csv
        import json
        
        with self.session() as s:
            records = s.query(PhoneRecord).all()
            
            if format == 'csv':
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['phone', 'formatted', 'source', 'username', 
                                   'first_seen', 'occurrence_count'])
                    for r in records:
                        writer.writerow([
                            r.phone_number,
                            r.formatted_number,
                            r.source_stream,
                            r.username,
                            r.first_seen.isoformat(),
                            r.occurrence_count
                        ])
            
            elif format == 'json':
                data = [{
                    'phone': r.phone_number,
                    'formatted': r.formatted_number,
                    'source': r.source_stream,
                    'username': r.username,
                    'context': r.context,
                    'first_seen': r.first_seen.isoformat(),
                    'occurrence_count': r.occurrence_count
                } for r in records]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
    
    def cleanup_old_records(self, days: int = 30):
        """
        Remove old extraction logs to save space.
        
        Args:
            days: Remove logs older than this many days
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self.session() as s:
            s.query(ExtractionLog).filter(
                ExtractionLog.timestamp < cutoff
            ).delete()
