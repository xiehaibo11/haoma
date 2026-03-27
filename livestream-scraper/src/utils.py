"""
Utility functions for the scraper.
"""

import os
from datetime import datetime
from typing import Dict, Any


def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary of environment overrides
    """
    config = {}
    
    # Target URL
    if url := os.getenv('SCRAPER_URL'):
        config['target'] = {'url': url}
    
    # Duration
    if duration := os.getenv('SCRAPER_DURATION'):
        config['scraping'] = {'duration': int(duration)}
    
    # Output directory
    if output := os.getenv('SCRAPER_OUTPUT'):
        config['output'] = {'directory': output}
    
    # Headless mode
    if headless := os.getenv('SCRAPER_HEADLESS'):
        config['browser'] = {'headless': headless.lower() == 'true'}
    
    return config


def merge_configs(base: Dict, override: Dict) -> Dict:
    """
    Recursively merge two configuration dictionaries.
    
    Args:
        base: Base configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def format_duration(seconds: int) -> str:
    """
    Format seconds into human-readable duration.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "5m 30s")
    """
    minutes = seconds // 60
    hours = minutes // 60
    
    if hours > 0:
        return f"{hours}h {minutes % 60}m {seconds % 60}s"
    elif minutes > 0:
        return f"{minutes}m {seconds % 60}s"
    else:
        return f"{seconds}s"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename.strip()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Original text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_phone_number(phone: str) -> Dict[str, Any]:
    """
    Parse a phone number and extract components.
    
    Args:
        phone: Phone number string
        
    Returns:
        Dictionary with parsed components
    """
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    result = {
        'raw': phone,
        'digits': digits,
        'length': len(digits),
        'is_chinese_mobile': False,
        'carrier': 'unknown'
    }
    
    # Check if Chinese mobile
    if len(digits) == 11 and digits.startswith('1'):
        result['is_chinese_mobile'] = True
        
        # Identify carrier
        prefix = digits[:3]
        carriers = {
            '134': 'China Mobile', '135': 'China Mobile', '136': 'China Mobile',
            '137': 'China Mobile', '138': 'China Mobile', '139': 'China Mobile',
            '147': 'China Mobile', '150': 'China Mobile', '151': 'China Mobile',
            '152': 'China Mobile', '157': 'China Mobile', '158': 'China Mobile',
            '159': 'China Mobile', '178': 'China Mobile', '182': 'China Mobile',
            '183': 'China Mobile', '184': 'China Mobile', '187': 'China Mobile',
            '188': 'China Mobile', '198': 'China Mobile',
            '130': 'China Unicom', '131': 'China Unicom', '132': 'China Unicom',
            '145': 'China Unicom', '155': 'China Unicom', '156': 'China Unicom',
            '166': 'China Unicom', '175': 'China Unicom', '176': 'China Unicom',
            '185': 'China Unicom', '186': 'China Unicom',
            '133': 'China Telecom', '149': 'China Telecom', '153': 'China Telecom',
            '173': 'China Telecom', '177': 'China Telecom', '180': 'China Telecom',
            '181': 'China Telecom', '189': 'China Telecom', '199': 'China Telecom',
        }
        result['carrier'] = carriers.get(prefix, 'Unknown')
    
    return result


def generate_report(phones: Dict[str, Dict], duration: int) -> str:
    """
    Generate a text report of extraction results.
    
    Args:
        phones: Dictionary of extracted phones
        duration: Extraction duration in seconds
        
    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("EXTRACTION REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Duration: {format_duration(duration)}")
    lines.append(f"Total Phones Found: {len(phones)}")
    lines.append("")
    
    if phones:
        lines.append("PHONE NUMBERS:")
        lines.append("-" * 70)
        
        for i, (phone, data) in enumerate(sorted(phones.items()), 1):
            lines.append(f"{i}. {data['formatted']}")
            lines.append(f"   First seen: {data.get('first_seen', 'unknown')}")
            lines.append(f"   Occurrences: {data.get('count', 1)}")
            if data.get('context'):
                lines.append(f"   Context: {data['context'][:60]}...")
            lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)
