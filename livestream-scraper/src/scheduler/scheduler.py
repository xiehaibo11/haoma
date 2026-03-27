"""
Stream scheduler for managing multiple live streams.

Handles:
- Queue management for multiple streams
- Rate limiting across all streams
- Priority-based scheduling
- Worker pool management
"""

import time
import threading
from queue import PriorityQueue, Empty
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


@dataclass(order=True)
class ScrapingTask:
    """
    A task for scraping a stream.
    
    Implements ordering for priority queue.
    """
    priority: int
    created_at: datetime = field(compare=False)
    stream_url: str = field(compare=False)
    platform: str = field(compare=False, default=None)
    check_interval: int = field(compare=False, default=30)
    retry_count: int = field(compare=False, default=0)
    last_check: Optional[datetime] = field(compare=False, default=None)
    
    def __post_init__(self):
        """Validate task data."""
        if not self.stream_url:
            raise ValueError("Stream URL is required")


class RateLimiter:
    """
    Rate limiter to prevent overwhelming target sites.
    
    Implements token bucket algorithm.
    """
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
    
    def acquire(self, blocking: bool = True) -> bool:
        """
        Try to acquire permission to make a request.
        
        Args:
            blocking: Whether to block until available
            
        Returns:
            True if permission granted, False otherwise
        """
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.time_window)
            
            # Remove old requests
            self.requests = [r for r in self.requests if r > cutoff]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            if not blocking:
                return False
            
            # Calculate wait time
            wait_time = (self.requests[0] - cutoff).total_seconds()
            wait_time = max(0.1, wait_time)
        
        # Wait outside the lock
        time.sleep(wait_time)
        return self.acquire(blocking=True)
    
    def get_stats(self) -> Dict:
        """Get current rate limiter statistics."""
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.time_window)
            active_requests = len([r for r in self.requests if r > cutoff])
            
            return {
                'active_requests': active_requests,
                'max_requests': self.max_requests,
                'utilization': active_requests / self.max_requests * 100
            }


class StreamScheduler:
    """
    Scheduler for managing multiple stream scraping tasks.
    
    Features:
    - Priority-based task queue
    - Rate limiting across all streams
    - Concurrent worker threads
    - Automatic retry with backoff
    - Health monitoring
    """
    
    def __init__(self, db, max_workers: int = 5, 
                 global_rate_limit: int = 60,
                 default_check_interval: int = 30):
        """
        Initialize scheduler.
        
        Args:
            db: Database instance
            max_workers: Maximum concurrent scraping threads
            global_rate_limit: Global requests per minute
            default_check_interval: Default seconds between checks
        """
        self.db = db
        self.max_workers = max_workers
        self.default_check_interval = default_check_interval
        
        # Task queue (priority-based)
        self.task_queue = PriorityQueue()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=global_rate_limit,
            time_window=60
        )
        
        # Worker management
        self.executor = None
        self.running = False
        self.worker_threads = []
        
        # Statistics
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'phones_found': 0,
            'start_time': None
        }
        
        # Callback for task results
        self.on_task_complete: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
    
    def add_stream(self, url: str, platform: str = None, 
                   priority: int = 5, check_interval: int = None) -> bool:
        """
        Add a stream to the scheduler.
        
        Args:
            url: Stream URL
            platform: Platform identifier
            priority: Priority level (1-10, lower = higher)
            check_interval: Seconds between checks
            
        Returns:
            True if added successfully
        """
        # Add to database
        added = self.db.add_stream(url, platform, priority, 
                                   check_interval or self.default_check_interval)
        
        if added:
            self.logger.info(f"Added stream: {url} (priority: {priority})")
        
        return added
    
    def add_streams_bulk(self, urls: List[str], platform: str = None,
                         priority: int = 5) -> int:
        """
        Add multiple streams at once.
        
        Args:
            urls: List of stream URLs
            platform: Platform for all streams
            priority: Priority for all streams
            
        Returns:
            Number of streams added
        """
        count = 0
        for url in urls:
            if self.add_stream(url, platform, priority):
                count += 1
        
        self.logger.info(f"Bulk added {count}/{len(urls)} streams")
        return count
    
    def load_streams_from_db(self, limit: int = 100):
        """
        Load active streams from database into queue.
        
        Args:
            limit: Maximum streams to load
        """
        streams = self.db.get_streams_to_check(limit)
        
        for stream in streams:
            # Check if enough time has passed since last check
            if stream.last_check:
                next_check = stream.last_check + timedelta(seconds=stream.check_interval)
                if datetime.utcnow() < next_check:
                    continue
            
            task = ScrapingTask(
                priority=stream.priority,
                created_at=datetime.utcnow(),
                stream_url=stream.url,
                platform=stream.platform,
                check_interval=stream.check_interval,
                last_check=stream.last_check
            )
            
            self.task_queue.put(task)
        
        self.logger.info(f"Loaded {len(streams)} streams into queue")
    
    def _execute_task(self, task: ScrapingTask) -> Dict:
        """
        Execute a single scraping task.
        
        Args:
            task: ScrapingTask to execute
            
        Returns:
            Task result dictionary
        """
        start_time = time.time()
        result = {
            'url': task.stream_url,
            'success': False,
            'new_phones': 0,
            'total_phones': 0,
            'duration': 0,
            'error': None
        }
        
        try:
            # Acquire rate limit
            self.rate_limiter.acquire()
            
            # Call the actual scraping function
            if self.on_task_complete:
                scrape_result = self.on_task_complete(task)
                result.update(scrape_result)
            else:
                result['error'] = "No scraping handler registered"
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Task failed for {task.stream_url}: {e}")
        
        finally:
            result['duration'] = int(time.time() - start_time)
            
            # Update database
            status = 'active' if result['success'] else 'error'
            self.db.update_stream_status(
                task.stream_url,
                status,
                result['error'],
                result['new_phones']
            )
            
            # Log extraction
            self.db.log_extraction(
                task.stream_url,
                result['new_phones'],
                result['total_phones'],
                result['duration'],
                result['success'],
                result['error']
            )
        
        return result
    
    def _worker_loop(self):
        """Worker thread main loop."""
        while self.running:
            try:
                # Get task from queue (blocking with timeout)
                task = self.task_queue.get(timeout=5)
                
                # Execute task
                result = self._execute_task(task)
                
                # Update stats
                if result['success']:
                    self.stats['tasks_completed'] += 1
                    self.stats['phones_found'] += result['new_phones']
                else:
                    self.stats['tasks_failed'] += 1
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Re-queue stream for next check if successful
                if result['success'] and task.retry_count < 3:
                    next_task = ScrapingTask(
                        priority=task.priority,
                        created_at=datetime.utcnow(),
                        stream_url=task.stream_url,
                        platform=task.platform,
                        check_interval=task.check_interval,
                        retry_count=0  # Reset retry count on success
                    )
                    # Delay re-queue by check_interval
                    time.sleep(task.check_interval)
                    if self.running:
                        self.task_queue.put(next_task)
                
            except Empty:
                # No tasks available, reload from DB
                self.load_streams_from_db()
                time.sleep(1)
            
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        
        # Load initial streams
        self.load_streams_from_db()
        
        # Start worker threads
        self.worker_threads = []
        for i in range(self.max_workers):
            thread = threading.Thread(target=self._worker_loop, name=f"Worker-{i}")
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
        
        self.logger.info(f"Scheduler started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the scheduler gracefully."""
        self.running = False
        
        # Wait for workers to finish
        for thread in self.worker_threads:
            thread.join(timeout=10)
        
        self.logger.info("Scheduler stopped")
    
    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'uptime_seconds': int(uptime),
            'queue_size': self.task_queue.qsize(),
            'rate_limiter': self.rate_limiter.get_stats()
        }
    
    def pause_stream(self, url: str):
        """Pause a specific stream."""
        self.db.update_stream_status(url, 'paused')
        self.logger.info(f"Paused stream: {url}")
    
    def resume_stream(self, url: str):
        """Resume a paused stream."""
        self.db.update_stream_status(url, 'active')
        # Add back to queue
        self.load_streams_from_db()
        self.logger.info(f"Resumed stream: {url}")
