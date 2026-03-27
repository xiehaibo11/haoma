"""
Username-based phone number extractor.

Extracts phone numbers from:
- Usernames/display names
- Comment text
- Profile information
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of phone extraction from a user/comment."""
    phone: str
    formatted: str
    source: str  # 'username', 'comment', 'profile'
    username: str
    context: str
    confidence: float  # 0.0 - 1.0


class UsernamePhoneExtractor:
    """
    Extracts phone numbers from usernames and content.
    
    Handles various formats:
    - Pure numbers in username: "13800138000"
    - Mixed format: "张三13800138000"
    - Separated: "张三-138-0013-8000"
    - Hidden format: "张三138****8000" (partial extraction)
    """
    
    def __init__(self):
        """Initialize with comprehensive patterns."""
        
        # Primary pattern: 11-digit Chinese mobile
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')
        
        # Pattern for mixed text (captures numbers embedded in text)
        self.mixed_pattern = re.compile(
            r'(?:^|[^\d])'  # Start or non-digit
            r'(1[3-9]\d{9})'  # Phone number
            r'(?:[^\d]|$)'  # End or non-digit
        )
        
        # Pattern with separators
        self.separated_pattern = re.compile(
            r'1[3-9]\d[\s\-\._]?\d{4}[\s\-\._]?\d{4}'
        )
        
        # Partial pattern (e.g., 138****8000)
        self.partial_pattern = re.compile(
            r'(1[3-9]\d)(\*{3,4})(\d{4})'
        )
        
        # Common separators in usernames
        self.separators = ['-', '_', '.', ' ', '~', '—', '–']
    
    def clean_username(self, username: str) -> str:
        """
        Clean username by normalizing separators.
        
        Args:
            username: Raw username
            
        Returns:
            Cleaned username
        """
        # Replace various separators with space for easier parsing
        cleaned = username
        for sep in self.separators:
            cleaned = cleaned.replace(sep, ' ')
        return cleaned
    
    def extract_from_username(self, username: str) -> List[ExtractionResult]:
        """
        Extract phone numbers from username.
        
        Args:
            username: Username/display name
            
        Returns:
            List of extraction results
        """
        results = []
        if not username:
            return results
        
        # Clean username
        cleaned = self.clean_username(username)
        
        # Try direct extraction
        phones = self.phone_pattern.findall(cleaned)
        
        for phone in phones:
            if self._validate_phone(phone):
                # Calculate confidence based on format
                confidence = self._calculate_confidence(
                    phone, username, source='username'
                )
                
                results.append(ExtractionResult(
                    phone=phone,
                    formatted=self._format_phone(phone),
                    source='username',
                    username=username,
                    context=username,
                    confidence=confidence
                ))
        
        # Try separated pattern
        if not results:
            separated = self.separated_pattern.findall(username)
            for match in separated:
                phone = re.sub(r'[^\d]', '', match)
                if self._validate_phone(phone):
                    results.append(ExtractionResult(
                        phone=phone,
                        formatted=self._format_phone(phone),
                        source='username',
                        username=username,
                        context=username,
                        confidence=0.9
                    ))
        
        return results
    
    def extract_from_comment(self, username: str, comment: str) -> List[ExtractionResult]:
        """
        Extract phone numbers from comment text.
        
        Args:
            username: Username who made the comment
            comment: Comment text
            
        Returns:
            List of extraction results
        """
        results = []
        if not comment:
            return results
        
        # Extract all phone numbers
        phones = self.phone_pattern.findall(comment)
        
        for phone in set(phones):  # Deduplicate
            if self._validate_phone(phone):
                confidence = self._calculate_confidence(
                    phone, comment, source='comment'
                )
                
                results.append(ExtractionResult(
                    phone=phone,
                    formatted=self._format_phone(phone),
                    source='comment',
                    username=username,
                    context=comment[:200],  # Limit context
                    confidence=confidence
                ))
        
        return results
    
    def extract_from_profile(self, username: str, profile_text: str) -> List[ExtractionResult]:
        """
        Extract phone numbers from profile information.
        
        Args:
            username: Username
            profile_text: Profile description/bio
            
        Returns:
            List of extraction results
        """
        results = []
        if not profile_text:
            return results
        
        phones = self.phone_pattern.findall(profile_text)
        
        for phone in set(phones):
            if self._validate_phone(phone):
                results.append(ExtractionResult(
                    phone=phone,
                    formatted=self._format_phone(phone),
                    source='profile',
                    username=username,
                    context=profile_text[:200],
                    confidence=0.85
                ))
        
        return results
    
    def extract_all(self, username: str, comment: str = None, 
                   profile: str = None) -> List[ExtractionResult]:
        """
        Extract phone numbers from all sources.
        
        Args:
            username: Username
            comment: Optional comment text
            profile: Optional profile text
            
        Returns:
            Combined list of extraction results
        """
        all_results = []
        
        # Extract from username
        all_results.extend(self.extract_from_username(username))
        
        # Extract from comment
        if comment:
            all_results.extend(self.extract_from_comment(username, comment))
        
        # Extract from profile
        if profile:
            all_results.extend(self.extract_from_profile(username, profile))
        
        # Deduplicate by phone number, keeping highest confidence
        seen = {}
        for result in all_results:
            if result.phone not in seen or seen[result.phone].confidence < result.confidence:
                seen[result.phone] = result
        
        return list(seen.values())
    
    def _validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format.
        
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
    
    def _calculate_confidence(self, phone: str, context: str, source: str) -> float:
        """
        Calculate confidence score for extraction.
        
        Args:
            phone: Extracted phone number
            context: Source text
            source: Type of source ('username', 'comment', 'profile')
            
        Returns:
            Confidence score 0.0 - 1.0
        """
        confidence = 0.5
        
        # Source-based confidence
        if source == 'username':
            confidence += 0.3  # Higher confidence for username
        elif source == 'profile':
            confidence += 0.2
        elif source == 'comment':
            confidence += 0.1
        
        # Check if context contains contact-related keywords
        contact_keywords = ['电话', '手机', '联系', 'tel', 'phone', 'mobile', 'call', '微信', 'wechat']
        context_lower = context.lower()
        
        for keyword in contact_keywords:
            if keyword in context_lower:
                confidence += 0.1
                break
        
        # Check if phone is standalone (not part of longer number)
        phone_idx = context.find(phone)
        if phone_idx >= 0:
            before = context[phone_idx-1:phone_idx] if phone_idx > 0 else ''
            after = context[phone_idx+11:phone_idx+12] if phone_idx + 11 < len(context) else ''
            
            if not before.isdigit() and not after.isdigit():
                confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)


class BatchExtractor:
    """
    Batch extraction processor for handling multiple users efficiently.
    """
    
    def __init__(self):
        """Initialize batch extractor."""
        self.extractor = UsernamePhoneExtractor()
    
    def process_users(self, users: List[Dict]) -> List[ExtractionResult]:
        """
        Process multiple users and extract all phone numbers.
        
        Args:
            users: List of user dictionaries with keys:
                   - username
                   - comment (optional)
                   - profile (optional)
                   
        Returns:
            List of all extraction results
        """
        all_results = []
        
        for user in users:
            username = user.get('username', '')
            comment = user.get('comment', '')
            profile = user.get('profile', '')
            
            results = self.extractor.extract_all(username, comment, profile)
            all_results.extend(results)
        
        return all_results
    
    def process_with_deduplication(self, users: List[Dict]) -> Dict[str, ExtractionResult]:
        """
        Process users with deduplication, keeping highest confidence.
        
        Args:
            users: List of user dictionaries
            
        Returns:
            Dictionary mapping phone numbers to best extraction result
        """
        all_results = self.process_users(users)
        
        # Deduplicate
        best_results = {}
        for result in all_results:
            phone = result.phone
            if phone not in best_results or best_results[phone].confidence < result.confidence:
                best_results[phone] = result
        
        return best_results


# Convenience function for quick extraction
def extract_phones_from_user(username: str, comment: str = None, 
                            profile: str = None) -> List[str]:
    """
    Quick extraction function - returns just the phone numbers.
    
    Args:
        username: Username
        comment: Optional comment
        profile: Optional profile
        
    Returns:
        List of formatted phone numbers
    """
    extractor = UsernamePhoneExtractor()
    results = extractor.extract_all(username, comment, profile)
    return [r.formatted for r in results]
