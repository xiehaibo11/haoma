#!/usr/bin/env python3
"""
Test script to verify extraction is working.
"""

import sys
from extractor_fixed import LeisuExtractor


def test_extraction():
    """Test the extraction logic."""
    extractor = LeisuExtractor()
    
    test_cases = [
        # (input_text, expected_phones_count, description)
        ("张三13800138000", 1, "Username with phone"),
        ("Contact me at 139-1234-5678", 1, "Comment with dashed phone"),
        ("Call 13800138000 or 13912345678", 2, "Multiple phones"),
        ("User: 李四15056789012", 1, "User prefix with phone"),
        ("No phone here", 0, "No phone number"),
        ("手机: 18612345678", 1, "Chinese label with phone"),
        ("微信 138-0013-8000 联系", 1, "Mixed text with phone"),
    ]
    
    print("=" * 70)
    print("PHONE EXTRACTION TEST")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for text, expected_count, description in test_cases:
        results = extractor.extract_all(comment=text)
        actual_count = len(results)
        
        status = "[PASS]" if actual_count == expected_count else "[FAIL]"
        
        print(f"{status} - {description}")
        print(f"  Input: {text[:50]}...")
        print(f"  Expected: {expected_count}, Found: {actual_count}")
        
        if results:
            for r in results:
                print(f"    → {r.formatted_phone} (confidence: {r.confidence:.2f})")
        print()
        
        if actual_count == expected_count:
            passed += 1
        else:
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    # Test username extraction
    print("\n" + "=" * 70)
    print("USERNAME EXTRACTION TEST")
    print("=" * 70)
    print()
    
    username_tests = [
        ("张三13800138000", "138-0013-8000"),
        ("李四13912345678", "139-1234-5678"),
        ("王五-150-5678-9012", "150-5678-9012"),
    ]
    
    for username, expected_phone in username_tests:
        results = extractor.extract_from_username(username)
        
        if results and results[0].formatted_phone == expected_phone:
            print(f"[PASS] - {username}")
            print(f"  → Found: {results[0].formatted_phone}")
        else:
            print(f"[FAIL] - {username}")
            found = results[0].formatted_phone if results else "None"
            print(f"  Expected: {expected_phone}, Found: {found}")
    
    print()
    return failed == 0


if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)
