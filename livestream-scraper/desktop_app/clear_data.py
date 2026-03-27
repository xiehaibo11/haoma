#!/usr/bin/env python3
"""
Clear all test data from database.
"""

import os
from database import LocalDatabase

db = LocalDatabase()

print("Current statistics:")
stats = db.get_statistics()
print(f"  Total records: {stats['total_records']}")
print(f"  Unique phones: {stats['unique_phones']}")

print("\nClearing all data...")
if db.clear_all():
    print("✓ Database cleared successfully")
else:
    print("✗ Failed to clear database")

print("\nNew statistics:")
stats = db.get_statistics()
print(f"  Total records: {stats['total_records']}")
print(f"  Unique phones: {stats['unique_phones']}")

# Also remove old db files
for f in ['test_app.db', 'extracted_data.db.bak']:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"✓ Removed {f}")
        except:
            pass

input("\nPress Enter to exit...")
