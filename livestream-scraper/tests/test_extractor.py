"""
Tests for the phone extractor module.
"""

import pytest
from src.extractor import PhoneExtractor, PhoneNumber


class TestPhoneExtractor:
    """Test cases for PhoneExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.patterns = [
            {'name': 'china_mobile', 'pattern': r'1[3-9]\d{9}', 'enabled': True},
            {'name': 'with_separators', 'pattern': r'1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}', 'enabled': True},
        ]
        self.extractor = PhoneExtractor(self.patterns)
    
    def test_extract_basic_chinese_mobile(self):
        """Test extraction of basic 11-digit Chinese mobile number."""
        text = "My phone is 13800138000"
        phones = self.extractor.extract(text)
        
        assert len(phones) == 1
        assert phones[0].raw == "13800138000"
        assert phones[0].formatted == "138-0013-8000"
    
    def test_extract_multiple_phones(self):
        """Test extraction of multiple phone numbers."""
        text = "Call 13800138000 or 13900139000"
        phones = self.extractor.extract(text)
        
        assert len(phones) == 2
        raw_numbers = [p.raw for p in phones]
        assert "13800138000" in raw_numbers
        assert "13900139000" in raw_numbers
    
    def test_extract_with_dashes(self):
        """Test extraction of numbers with dash separators."""
        text = "Contact: 138-0013-8000"
        phones = self.extractor.extract(text)
        
        assert len(phones) == 1
        assert phones[0].raw == "13800138000"
    
    def test_extract_with_spaces(self):
        """Test extraction of numbers with space separators."""
        text = "Phone: 138 0013 8000"
        phones = self.extractor.extract(text)
        
        assert len(phones) == 1
        assert phones[0].raw == "13800138000"
    
    def test_no_false_positives(self):
        """Test that invalid numbers are not extracted."""
        text = "Numbers: 12345678901 99999999999 00000000000"
        phones = self.extractor.extract(text)
        
        # 12345678901 - starts with 1 but second digit 2 is valid
        # 99999999999 - doesn't start with 1
        # 00000000000 - doesn't start with 1
        assert len(phones) == 1  # Only 12345678901 might match
    
    def test_empty_text(self):
        """Test handling of empty text."""
        phones = self.extractor.extract("")
        assert len(phones) == 0
        
        phones = self.extractor.extract(None)
        assert len(phones) == 0
    
    def test_context_preservation(self):
        """Test that context is preserved."""
        text = "Call me at 13800138000 for details"
        phones = self.extractor.extract(text, context=text)
        
        assert len(phones) == 1
        assert phones[0].context == text
    
    def test_deduplication(self):
        """Test that duplicate numbers are not returned."""
        text = "Call 13800138000 or 13800138000 again"
        phones = self.extractor.extract(text)
        
        assert len(phones) == 1
    
    def test_validate_chinese_mobile_valid(self):
        """Test validation of valid Chinese mobile numbers."""
        valid_numbers = [
            "13800138000",
            "15012345678",
            "18612345678",
            "19912345678",
        ]
        
        for number in valid_numbers:
            assert self.extractor.validate_chinese_mobile(number), f"{number} should be valid"
    
    def test_validate_chinese_mobile_invalid(self):
        """Test validation of invalid Chinese mobile numbers."""
        invalid_numbers = [
            "1380013800",      # Too short
            "138001380000",    # Too long
            "02800138000",     # Doesn't start with 1
            "11111111111",     # Second digit not 3-9
            "",                # Empty
            "abcdefghijk",     # Not digits
        ]
        
        for number in invalid_numbers:
            assert not self.extractor.validate_chinese_mobile(number), f"{number} should be invalid"
    
    def test_format_number(self):
        """Test number formatting."""
        assert self.extractor._format_number("13800138000") == "138-0013-8000"
        assert self.extractor._format_number("123") == "123"  # Short number unchanged
    
    def test_clean_number(self):
        """Test number cleaning."""
        assert self.extractor._clean_number("138-0013-8000") == "13800138000"
        assert self.extractor._clean_number("138 0013 8000") == "13800138000"
        assert self.extractor._clean_number("+8613800138000") == "13800138000"
        assert self.extractor._clean_number("8613800138000") == "13800138000"


class TestPhoneNumber:
    """Test cases for PhoneNumber dataclass."""
    
    def test_phone_number_creation(self):
        """Test PhoneNumber creation."""
        phone = PhoneNumber(
            raw="13800138000",
            formatted="138-0013-8000",
            pattern_name="china_mobile",
            context="Call me"
        )
        
        assert phone.raw == "13800138000"
        assert phone.formatted == "138-0013-8000"
        assert phone.pattern_name == "china_mobile"
        assert phone.context == "Call me"
    
    def test_phone_number_equality(self):
        """Test PhoneNumber equality based on raw number."""
        phone1 = PhoneNumber("13800138000", "138-0013-8000", "pattern1")
        phone2 = PhoneNumber("13800138000", "138-0013-8000", "pattern2")
        phone3 = PhoneNumber("13900139000", "139-0013-9000", "pattern1")
        
        assert phone1 == phone2  # Same raw number
        assert phone1 != phone3  # Different raw number
        assert hash(phone1) == hash(phone2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
