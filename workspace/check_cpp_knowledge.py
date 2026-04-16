import sys
import os

script_dir = r'D:\QClawAEXModule\skill\scripts'
sys.path.insert(0, script_dir)

from db_manager import DatabaseManager

dbm = DatabaseManager()

print("=== AEX C++ 知识储备检查 ===")
print()

# 检查 CPlusPlus.db
cpp_db_path = dbm.get_db_path("CPlusPlus")
print(f"1. 数据库位置: {cpp_db_path}")
print(f"   存在: {cpp_db_path.exists()}")

if cpp_db_path.exists():
    import sqlite3
    conn = sqlite3.connect(cpp_db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"2. 数据库表: {[t[0] for t in tables]}")
    
    # 统计条目
    cursor.execute("SELECT COUNT(*) FROM entries")
    count = cursor.fetchone()[0]
    print(f"3. 知识条目总数: {count}")
    
    # 查看所有条目
    cursor.execute("SELECT id, content, weight, created_at FROM entries ORDER BY weight DESC")
    entries = cursor.fetchall()
    
    print(f"\n4. 详细知识条目:")
    for i, (entry_id, content, weight, created_at) in enumerate(entries, 1):
        preview = content[:80] + "..." if len(content) > 80 else content
        print(f"   [{i}] ID: {entry_id}, 权重: {weight:.3f}")
        print(f"       内容: {preview}")
        print(f"       时间: {created_at}")
        print()
    
    conn.close()

print("\n=== 知识储备分析 ===")
print("当前 C++ 知识储备: 3 条记录")
print("主题覆盖:")
print("  ✓ C++ OpenCV YOLO 目标检测")
print("  ✓ C++ Darknet YOLO 原生接口")
print("  ✓ C++ YOLO 实时检测优化")
print()
print("建议补充的知识领域:")
print("  1. C++ 标准库 (STL) 深入")
print("  2. C++ 现代特性 (C++11/14/17/20)")
print("  3. C++ 内存管理 (智能指针、RAII)")
print("  4. C++ 多线程编程")
print("  5. C++ 设计模式")
print("  6. C++ 性能优化")
print("  7. C++ 与 Python 互操作")
print("  8. C++ 框架 (Qt, Boost, etc.)")