#!/usr/bin/env python3
"""
Simple script to run the multi-stream scraper.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from multi_stream_scraper import main

if __name__ == '__main__':
    main()
