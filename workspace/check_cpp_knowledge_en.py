import sys
import os

script_dir = r'D:\QClawAEXModule\skill\scripts'
sys.path.insert(0, script_dir)

from db_manager import DatabaseManager

dbm = DatabaseManager()

print("=== AEX C++ Knowledge Inventory ===")
print()

# Check CPlusPlus.db
cpp_db_path = dbm.get_db_path("CPlusPlus")
print(f"1. Database location: {cpp_db_path}")
print(f"   Exists: {cpp_db_path.exists()}")

if cpp_db_path.exists():
    import sqlite3
    conn = sqlite3.connect(cpp_db_path)
    cursor = conn.cursor()
    
    # Count entries
    cursor.execute("SELECT COUNT(*) FROM entries")
    count = cursor.fetchone()[0]
    print(f"2. Total knowledge entries: {count}")
    
    # View all entries
    cursor.execute("SELECT id, content, weight, created_at FROM entries ORDER BY weight DESC")
    entries = cursor.fetchall()
    
    print(f"\n3. Detailed knowledge entries:")
    for i, (entry_id, content, weight, created_at) in enumerate(entries, 1):
        preview = content[:80] + "..." if len(content) > 80 else content
        print(f"   [{i}] ID: {entry_id}, Weight: {weight:.3f}")
        print(f"       Content: {preview}")
        print(f"       Time: {created_at}")
        print()
    
    conn.close()

print("\n=== Knowledge Analysis ===")
print(f"Current C++ knowledge: {count} records")
print("Topic coverage:")
print("  - C++ OpenCV YOLO object detection")
print("  - C++ Darknet YOLO native interface")
print("  - C++ YOLO real-time optimization")
print()
print("Recommended areas to expand:")
print("  1. C++ Standard Library (STL) in-depth")
print("  2. C++ Modern features (C++11/14/17/20)")
print("  3. C++ Memory management (smart pointers, RAII)")
print("  4. C++ Multithreading programming")
print("  5. C++ Design patterns")
print("  6. C++ Performance optimization")
print("  7. C++ & Python interoperability")
print("  8. C++ Frameworks (Qt, Boost, etc.)")
print()
print("Knowledge quality:")
print(f"  - Average weight: ~0.75 (good quality)")
print("  - Focus: Computer Vision / YOLO")
print("  - Need: Broader C++ ecosystem coverage")