#!/usr/bin/env python3
"""
Example: Custom Phone Extractor

This example shows how to create a custom extractor for international phone numbers.
"""

import re
from src.extractor import PhoneExtractor, PhoneNumber


class InternationalPhoneExtractor(PhoneExtractor):
    """
    Custom extractor for international phone numbers.
    Extends the base PhoneExtractor with additional patterns.
    """
    
    def __init__(self):
        # Define international patterns
        patterns = [
            # Chinese mobile (default)
            {'name': 'china_mobile', 'pattern': r'1[3-9]\d{9}', 'enabled': True},
            
            # US/Canada: (123) 456-7890 or 123-456-7890
            {'name': 'us_phone', 'pattern': r'\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}', 'enabled': True},
            
            # UK: +44 1234 567890 or 01234 567890
            {'name': 'uk_phone', 'pattern': r'(\+44\s?\d{4}|0\d{4})\s?\d{6}', 'enabled': True},
            
            # International format: +1 123 456 7890
            {'name': 'intl_format', 'pattern': r'\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}', 'enabled': True},
        ]
        super().__init__(patterns)
    
    def _format_number(self, number: str) -> str:
        """
        Custom formatting based on number type.
        """
        clean = self._clean_number(number)
        
        # Chinese mobile (11 digits starting with 1)
        if len(clean) == 11 and clean.startswith('1'):
            return f"{clean[:3]}-{clean[3:7]}-{clean[7:]}"
        
        # US phone (10 digits)
        if len(clean) == 10:
            return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
        
        # Return as-is for other formats
        return number
    
    def validate_international(self, number: str) -> dict:
        """
        Validate and identify international phone number type.
        
        Returns:
            Dict with validation result and identified country
        """
        clean = self._clean_number(number)
        
        result = {
            'valid': False,
            'type': 'unknown',
            'country': 'unknown'
        }
        
        # Chinese mobile
        if len(clean) == 11 and clean.startswith('1') and clean[1] in '3456789':
            result['valid'] = True
            result['type'] = 'mobile'
            result['country'] = 'CN'
        
        # US/Canada
        elif len(clean) == 10:
            result['valid'] = True
            result['type'] = 'landline_or_mobile'
            result['country'] = 'US/CA'
        
        # UK
        elif clean.startswith('44') and len(clean) >= 10:
            result['valid'] = True
            result['type'] = 'landline_or_mobile'
            result['country'] = 'UK'
        
        return result


def main():
    """Example usage."""
    extractor = InternationalPhoneExtractor()
    
    # Test text with multiple international numbers
    test_text = """
    Contact us:
    China: 138-0013-8000
    USA: (555) 123-4567
    UK: +44 1234 567890
    International: +1 234 567 8901
    """
    
    print("Testing International Phone Extractor")
    print("=" * 60)
    print(f"Input text:\n{test_text}\n")
    
    phones = extractor.extract(test_text)
    
    print(f"Found {len(phones)} phone number(s):\n")
    
    for phone in phones:
        validation = extractor.validate_international(phone.raw)
        print(f"Number: {phone.formatted}")
        print(f"  Raw: {phone.raw}")
        print(f"  Pattern: {phone.pattern_name}")
        print(f"  Country: {validation['country']}")
        print(f"  Type: {validation['type']}")
        print()


if __name__ == "__main__":
    main()
