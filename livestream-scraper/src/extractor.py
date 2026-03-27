"""
Phone number extraction module.

Handles pattern matching and cleaning of phone numbers from text.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PhoneNumber:
    """Represents an extracted phone number."""
    raw: str
    formatted: str
    pattern_name: str
    context: Optional[str] = None
    
    def __hash__(self):
        return hash(self.raw)
    
    def __eq__(self, other):
        if isinstance(other, PhoneNumber):
            return self.raw == other.raw
        return False


class PhoneExtractor:
    """
    Extracts phone numbers from text using configured patterns.
    """
    
    def __init__(self, patterns: List[Dict] = None):
        """
        Initialize extractor with patterns.
        
        Args:
            patterns: List of pattern configs with 'name', 'pattern', 'enabled' keys
        """
        self.patterns = []
        self.compiled_patterns = {}
        
        if patterns:
            self.load_patterns(patterns)
    
    def load_patterns(self, patterns: List[Dict]):
        """Load and compile regex patterns."""
        for p in patterns:
            if p.get('enabled', True):
                try:
                    name = p['name']
                    pattern = p['pattern']
                    self.compiled_patterns[name] = re.compile(pattern)
                    self.patterns.append({'name': name, 'pattern': pattern})
                except (KeyError, re.error) as e:
                    print(f"Warning: Failed to load pattern {p}: {e}")
    
    def extract(self, text: str, context: str = None) -> List[PhoneNumber]:
        """
        Extract phone numbers from text.
        
        Args:
            text: Text to search
            context: Optional context for the phone number
            
        Returns:
            List of PhoneNumber objects
        """
        found = []
        seen = set()
        
        if not text:
            return found
        
        for name, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            
            for match in matches:
                # Handle tuple returns from groups
                if isinstance(match, tuple):
                    match = ''.join(m for m in match if m)
                
                # Clean the number
                clean = self._clean_number(match)
                
                if clean and len(clean) == 11 and clean not in seen:
                    seen.add(clean)
                    formatted = self._format_number(clean)
                    phone = PhoneNumber(
                        raw=clean,
                        formatted=formatted,
                        pattern_name=name,
                        context=context
                    )
                    found.append(phone)
        
        return found
    
    def _clean_number(self, number: str) -> str:
        """
        Clean phone number by removing separators and country codes.
        
        Args:
            number: Raw phone number string
            
        Returns:
            Cleaned 11-digit number
        """
        # Remove common separators
        clean = number.replace(' ', '').replace('-', '')
        clean = clean.replace('(', '').replace(')', '')
        clean = clean.replace('+', '')
        
        # Remove country code
        if clean.startswith('86') and len(clean) > 11:
            clean = clean[2:]
        
        return clean
    
    def _format_number(self, number: str) -> str:
        """
        Format phone number for display.
        
        Args:
            number: Clean 11-digit number
            
        Returns:
            Formatted number (e.g., 138-0013-8000)
        """
        if len(number) == 11:
            return f"{number[:3]}-{number[3:7]}-{number[7:]}"
        return number
    
    def validate_chinese_mobile(self, number: str) -> bool:
        """
        Validate if number is a valid Chinese mobile number.
        
        Args:
            number: Phone number to validate
            
        Returns:
            True if valid Chinese mobile number
        """
        if len(number) != 11:
            return False
        
        if not number.startswith('1'):
            return False
        
        # Valid second digits for Chinese mobile
        valid_seconds = '3456789'
        if number[1] not in valid_seconds:
            return False
        
        return True
