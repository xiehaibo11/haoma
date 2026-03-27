"""
Phone and username extractor specifically for leisu.com live streams.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of extraction."""
    phone: str
    formatted_phone: str
    username: str
    context: str
    source: str  # 'username', 'comment', 'page'
    confidence: float


class LeisuExtractor:
    """
    Specialized extractor for leisu.com live stream comments.
    Extracts phone numbers from usernames and comments.
    """
    
    def __init__(self):
        """Initialize with patterns optimized for leisu.com."""
        # Chinese mobile phone pattern
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        
        # Pattern with separators (dash, space, dot)
        self.separated_pattern = re.compile(
            r'1[3-9]\d[\s\-\.]?\d{4}[\s\-\.]?\d{4}'
        )
        
        # Pattern for hidden/masked numbers (e.g., 138****8000)
        self.masked_pattern = re.compile(
            r'(1[3-9]\d)(\*+)(\d{4})'
        )
        
        # Keywords that indicate contact info
        self.contact_keywords = [
            '电话', '手机', '联系', '微信', 'vx', 'qq', 
            'tel', 'phone', 'mobile', 'contact', 'call',
            '加我', '联系我', '咨询'
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace."""
        if not text:
            return ""
        return ' '.join(text.split())
    
    def extract_from_username(self, username: str) -> List[ExtractionResult]:
        """
        Extract phone from username.
        
        Args:
            username: Username string
            
        Returns:
            List of extraction results
        """
        results = []
        if not username:
            return results
        
        # Direct extraction
        phones = self.phone_pattern.findall(username)
        
        for phone in phones:
            if self._validate_phone(phone):
                results.append(ExtractionResult(
                    phone=phone,
                    formatted_phone=self._format_phone(phone),
                    username=username,
                    context=username,
                    source='username',
                    confidence=0.95
                ))
        
        # Try separated pattern
        if not results:
            matches = self.separated_pattern.findall(username)
            for match in matches:
                # Remove separators
                phone = re.sub(r'[^\d]', '', match)
                if self._validate_phone(phone):
                    results.append(ExtractionResult(
                        phone=phone,
                        formatted_phone=self._format_phone(phone),
                        username=username,
                        context=username,
                        source='username',
                        confidence=0.90
                    ))
        
        return results
    
    def extract_from_comment(self, username: str, comment: str) -> List[ExtractionResult]:
        """
        Extract phone from comment text.
        
        Args:
            username: Username who posted
            comment: Comment text
            
        Returns:
            List of extraction results
        """
        results = []
        if not comment:
            return results
        
        # Clean comment
        comment = self.clean_text(comment)
        
        # Find all phone numbers
        phones = self.phone_pattern.findall(comment)
        
        for phone in set(phones):  # Deduplicate
            if self._validate_phone(phone):
                # Calculate confidence based on context
                confidence = self._calculate_confidence(phone, comment)
                
                results.append(ExtractionResult(
                    phone=phone,
                    formatted_phone=self._format_phone(phone),
                    username=username,
                    context=comment[:200],  # Limit context
                    source='comment',
                    confidence=confidence
                ))

        # Fallback: numbers with separators like 177-4557-6176
        if not results:
            separated = self.separated_pattern.findall(comment)
            for match in set(separated):
                phone = re.sub(r'[^\d]', '', match)
                if self._validate_phone(phone):
                    results.append(ExtractionResult(
                        phone=phone,
                        formatted_phone=self._format_phone(phone),
                        username=username,
                        context=comment[:200],
                        source='comment',
                        confidence=0.80
                    ))
        
        return results
    
    def extract_from_page_content(self, content: str) -> List[ExtractionResult]:
        """
        Extract from entire page content as fallback.
        
        Args:
            content: Page HTML/text content
            
        Returns:
            List of extraction results
        """
        results = []
        if not content:
            return results
        
        # Extract all phone patterns
        phones = self.phone_pattern.findall(content)
        
        # Deduplicate and validate
        seen = set()
        for phone in phones:
            if phone not in seen and self._validate_phone(phone):
                seen.add(phone)
                results.append(ExtractionResult(
                    phone=phone,
                    formatted_phone=self._format_phone(phone),
                    username="",  # Unknown username from page scan
                    context=content[:200],
                    source='page',
                    confidence=0.60
                ))

        # Fallback: separated numbers on page text
        if not results:
            separated = self.separated_pattern.findall(content)
            for match in set(separated):
                phone = re.sub(r'[^\d]', '', match)
                if phone not in seen and self._validate_phone(phone):
                    seen.add(phone)
                    results.append(ExtractionResult(
                        phone=phone,
                        formatted_phone=self._format_phone(phone),
                        username="",
                        context=content[:200],
                        source='page',
                        confidence=0.60
                    ))
        
        return results
    
    def extract_all(self, username: str = "", comment: str = "", 
                   page_content: str = "") -> List[ExtractionResult]:
        """
        Extract from all available sources.
        
        Args:
            username: Username
            comment: Comment text
            page_content: Full page content
            
        Returns:
            Combined list of unique results
        """
        all_results = []
        
        # Extract from username (highest priority)
        if username:
            all_results.extend(self.extract_from_username(username))
        
        # Extract from comment
        if comment:
            all_results.extend(self.extract_from_comment(username, comment))
        
        # Extract from page content (fallback)
        if page_content and not all_results:
            all_results.extend(self.extract_from_page_content(page_content))
        
        # Deduplicate by phone number, keeping highest confidence
        unique_results = {}
        for result in all_results:
            if result.phone not in unique_results:
                unique_results[result.phone] = result
            elif unique_results[result.phone].confidence < result.confidence:
                unique_results[result.phone] = result
        
        return list(unique_results.values())
    
    def _validate_phone(self, phone: str) -> bool:
        """
        Validate Chinese mobile phone number.
        
        Args:
            phone: Phone number string
            
        Returns:
            True if valid
        """
        if len(phone) != 11:
            return False
        
        if not phone.startswith('1'):
            return False
        
        # Valid second digit
        if phone[1] not in '3456789':
            return False
        
        return True
    
    def _format_phone(self, phone: str) -> str:
        """
        Format phone number with separators.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted number (e.g., 138-0013-8000)
        """
        if len(phone) == 11:
            return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return phone
    
    def _calculate_confidence(self, phone: str, context: str) -> float:
        """
        Calculate confidence score based on context.
        
        Args:
            phone: Phone number
            context: Surrounding text
            
        Returns:
            Confidence score 0.0-1.0
        """
        confidence = 0.70  # Base confidence
        context_lower = context.lower()
        
        # Boost if contact keywords present
        for keyword in self.contact_keywords:
            if keyword in context_lower:
                confidence += 0.10
                break
        
        # Boost if standalone (not part of longer number)
        idx = context.find(phone)
        if idx >= 0:
            before = context[idx-1:idx] if idx > 0 else ' '
            after = context[idx+11:idx+12] if idx + 11 < len(context) else ' '
            
            if not before.isdigit() and not after.isdigit():
                confidence += 0.10
        
        return min(confidence, 1.0)


def quick_extract(text: str) -> List[Tuple[str, str]]:
    """
    Quick extraction function - returns list of (phone, formatted) tuples.
    
    Args:
        text: Text to search
        
    Returns:
        List of (raw_phone, formatted_phone) tuples
    """
    extractor = LeisuExtractor()
    results = extractor.extract_all(page_content=text)
    return [(r.phone, r.formatted_phone) for r in results]
