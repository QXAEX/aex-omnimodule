#!/usr/bin/env python3
"""
修复 AEX 数据库表结构不一致问题 - 版本2
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def fix_database_schema(db_path):
    """修复数据库表结构"""
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(entries)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"\n检查数据库: {os.path.basename(db_path)}")
    print(f"当前字段: {column_names}")
    
    changes_made = False
    
    # 标准字段定义（简化，避免 SQLite 限制）
    standard_columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "content": "TEXT NOT NULL",
        "source": "TEXT",
        "credibility_score": "REAL DEFAULT 0.5",
        "weight": "INTEGER DEFAULT 1",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "metadata": "TEXT"
    }
    
    # 1. 首先重命名字段
    if "credibility" in column_names and "credibility_score" not in column_names:
        print(f"  重命名字段: credibility -> credibility_score")
        try:
            # SQLite 3.25+ 支持 RENAME COLUMN
            cursor.execute("ALTER TABLE entries RENAME COLUMN credibility TO credibility_score")
            changes_made = True
        except Exception as e:
            print(f"  重命名失败: {e}")
            # 回退方案：创建新表并复制数据
            print(f"  使用回退方案：创建新表...")
            return recreate_table_with_correct_schema(db_path)
    
    # 2. 修复 weight 字段类型
    for col in columns:
        if col[1] == "weight" and col[2] == "REAL":
            print(f"  修复 weight 字段类型: REAL -> INTEGER")
            # 需要创建新表
            return recreate_table_with_correct_schema(db_path)
    
    # 3. 添加缺失的字段（不带默认值）
    for col_name, col_type in standard_columns.items():
        if col_name not in column_names:
            print(f"  添加字段: {col_name}")
            
            # 简化类型定义
            simple_type = col_type.split()[0]  # 只取第一个词，如 "INTEGER", "TEXT", "REAL", "TIMESTAMP"
            
            try:
                cursor.execute(f"ALTER TABLE entries ADD COLUMN {col_name} {simple_type}")
                changes_made = True
            except Exception as e:
                print(f"  添加字段失败: {e}")
                # 可能需要创建新表
                return recreate_table_with_correct_schema(db_path)
    
    # 4. 创建 tags 表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            tag TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
        )
    """)
    
    if changes_made:
        conn.commit()
        print(f"  数据库已修复")
    else:
        print(f"  数据库结构正常")
    
    # 显示修复后的数据
    cursor.execute("SELECT COUNT(*) FROM entries")
    count = cursor.fetchone()[0]
    print(f"  记录数: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, content, source FROM entries LIMIT 3")
        entries = cursor.fetchall()
        print(f"  示例记录:")
        for entry in entries:
            print(f"    ID:{entry[0]}, 来源:{entry[2]}")
            print(f"    内容: {entry[1][:100]}...")
    
    conn.close()
    return changes_made

def recreate_table_with_correct_schema(db_path):
    """创建新表并复制数据（当 ALTER 失败时使用）"""
    print(f"  创建新表并迁移数据...")
    
    # 备份原文件
    backup_path = db_path.with_suffix('.db.backup')
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"  已创建备份: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 创建临时表保存原数据
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries_old AS 
        SELECT * FROM entries
    """)
    
    # 2. 删除原表
    cursor.execute("DROP TABLE IF EXISTS entries")
    
    # 3. 创建新表（正确结构）
    cursor.execute("""
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT,
            credibility_score REAL DEFAULT 0.5,
            weight INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    # 4. 从旧表复制数据（处理字段映射）
    cursor.execute("PRAGMA table_info(entries_old)")
    old_columns = [col[1] for col in cursor.fetchall()]
    
    # 构建字段映射
    column_map = {}
    if "content" in old_columns:
        column_map["content"] = "content"
    if "source" in old_columns:
        column_map["source"] = "source"
    if "credibility" in old_columns:
        column_map["credibility_score"] = "credibility"
    elif "credibility_score" in old_columns:
        column_map["credibility_score"] = "credibility_score"
    if "weight" in old_columns:
        column_map["weight"] = "CAST(weight AS INTEGER)"
    if "created_at" in old_columns:
        column_map["created_at"] = "created_at"
    if "metadata" in old_columns:
        column_map["metadata"] = "metadata"
    
    if column_map:
        source_cols = ", ".join(column_map.values())
        target_cols = ", ".join(column_map.keys())
        
        insert_sql = f"""
            INSERT INTO entries ({target_cols})
            SELECT {source_cols} FROM entries_old
        """
        
        cursor.execute(insert_sql)
        print(f"  迁移了 {cursor.rowcount} 条记录")
    
    # 5. 删除临时表
    cursor.execute("DROP TABLE entries_old")
    
    # 6. 创建索引
    indexes = [
        "CREATE INDEX idx_entries_created ON entries(created_at)",
        "CREATE INDEX idx_entries_weight ON entries(weight DESC)",
        "CREATE INDEX idx_entries_credibility ON entries(credibility_score DESC)",
        "CREATE INDEX idx_entries_source ON entries(source)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    # 7. 创建 tags 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            tag TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_entry ON tags(entry_id)")
    
    conn.commit()
    conn.close()
    
    print(f"  表结构已重建")
    return True

def main():
    """修复所有数据库"""
    db_dir = Path(r"D:\QClawAEXModule\db")
    
    print("开始修复 AEX 数据库表结构...")
    print("=" * 60)
    
    # 修复主题数据库
    theme_dbs = ["Python.db", "CPlusPlus.db", "AI.db", "Flutter.db", "Rust.db", "Web.db"]
    
    for db_file in theme_dbs:
        db_path = db_dir / db_file
        if os.path.exists(db_path):
            fix_database_schema(db_path)
        else:
            print(f"\n数据库不存在: {db_file}")
    
    # 修复系统数据库
    system_dir = db_dir / "2026_2027"
    if system_dir.exists():
        system_dbs = ["general.db", "conversations.db"]
        
        for db_file in system_dbs:
            db_path = system_dir / db_file
            if os.path.exists(db_path):
                fix_database_schema(db_path)
    
    print("\n" + "=" * 60)
    print("数据库修复完成！")
    print("\n下一步：")
    print("1. 重启 OpenClaw 网关")
    print("2. 测试 AEX 知识检索功能")
    print("3. 添加更多知识到数据库")

if __name__ == "__main__":
    main()