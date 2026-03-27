"""
Phone and username extractor specifically for leisu.com live streams.
Fixed version with better dash-separated number handling.
"""

import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of extraction."""
    phone: str
    formatted_phone: str
    username: str
    context: str
    source: str
    confidence: float


class LeisuExtractor:
    """
    Specialized extractor for leisu.com live stream comments.
    """
    
    def __init__(self):
        """Initialize with patterns optimized for leisu.com."""
        # Direct 11-digit pattern
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        
        # Pattern with various separators
        # Matches: 138-0013-8000, 138 0013 8000, 138.0013.8000, etc.
        self.separated_pattern = re.compile(
            r'1[3-9]\d[\s\-\._]\d{4}[\s\-\._]\d{4}'
        )
        
        # Contact keywords
        self.contact_keywords = [
            '电话', '手机', '联系', '微信', 'vx', 'qq', 
            'tel', 'phone', 'mobile', 'contact', 'call',
            '加我', '联系我', '咨询', '微信'
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean text."""
        if not text:
            return ""
        return ' '.join(text.split())
    
    def extract_from_username(self, username: str) -> List[ExtractionResult]:
        """Extract phone from username."""
        results = []
        if not username:
            return results
        
        # Try direct extraction first
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
                # Remove all non-digits
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
        """Extract phone from comment."""
        results = []
        if not comment:
            return results
        
        comment = self.clean_text(comment)
        
        # Strategy 1: Find all 11-digit numbers
        phones = self.phone_pattern.findall(comment)
        for phone in set(phones):
            if self._validate_phone(phone):
                confidence = self._calculate_confidence(phone, comment)
                results.append(ExtractionResult(
                    phone=phone,
                    formatted_phone=self._format_phone(phone),
                    username=username,
                    context=comment[:200],
                    source='comment',
                    confidence=confidence
                ))
        
        # Strategy 2: Find dash/space separated
        if not results:
            matches = self.separated_pattern.findall(comment)
            for match in matches:
                phone = re.sub(r'[^\d]', '', match)
                if self._validate_phone(phone) and phone not in [r.phone for r in results]:
                    results.append(ExtractionResult(
                        phone=phone,
                        formatted_phone=self._format_phone(phone),
                        username=username,
                        context=comment[:200],
                        source='comment',
                        confidence=0.85
                    ))
        
        return results
    
    def extract_all(self, username: str = "", comment: str = "", 
                   page_content: str = "") -> List[ExtractionResult]:
        """Extract from all sources."""
        all_results = []
        
        if username:
            all_results.extend(self.extract_from_username(username))
        
        if comment:
            all_results.extend(self.extract_from_comment(username, comment))
        
        if page_content and not all_results:
            # Scan page content
            phones = self.phone_pattern.findall(page_content)
            for phone in set(phones):
                if self._validate_phone(phone):
                    all_results.append(ExtractionResult(
                        phone=phone,
                        formatted_phone=self._format_phone(phone),
                        username="",
                        context=page_content[:200],
                        source='page',
                        confidence=0.60
                    ))
        
        # Deduplicate
        seen = {}
        for result in all_results:
            if result.phone not in seen or seen[result.phone].confidence < result.confidence:
                seen[result.phone] = result
        
        return list(seen.values())
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number."""
        if len(phone) != 11:
            return False
        if not phone.startswith('1'):
            return False
        if phone[1] not in '3456789':
            return False
        return True
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number."""
        if len(phone) == 11:
            return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return phone
    
    def _calculate_confidence(self, phone: str, context: str) -> float:
        """Calculate confidence."""
        confidence = 0.70
        context_lower = context.lower()
        
        for keyword in self.contact_keywords:
            if keyword in context_lower:
                confidence += 0.15
                break
        
        # Check standalone
        idx = context.find(phone)
        if idx >= 0:
            before = context[idx-1:idx] if idx > 0 else ' '
            after = context[idx+11:idx+12] if idx + 11 < len(context) else ' '
            if not before.isdigit() and not after.isdigit():
                confidence += 0.10
        
        return min(confidence, 1.0)


# Quick extract function
def quick_extract(text: str) -> List[tuple]:
    """Quick extraction."""
    extractor = LeisuExtractor()
    results = extractor.extract_all(page_content=text)
    return [(r.phone, r.formatted_phone) for r in results]
