#!/usr/bin/env python3
"""
AEX全知模块 - 数据库管理器
负责数据库的创建、查询、压缩、归档等操作
"""

import sqlite3
import os
import json
import lzma
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# 动态检测根目录：优先读配置中的 data_dir，否则用预设路径
SKILL_DIR = Path(__file__).resolve().parent.parent
_CANDIDATE = SKILL_DIR.parent / "db"
_FALLBACK = Path("D:/QClawAEXModule/db")
ROOT_DIR = _CANDIDATE if (_CANDIDATE.exists() or not _FALLBACK.exists()) else _FALLBACK
MAX_DB_SIZE = 1.5 * 1024 * 1024 * 1024  # 1.5GB

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else ROOT_DIR
        self.master_db = self.root_dir / "master.db"
        self.config_file = self.root_dir / "config.json"
        self._ensure_structure()
    
    def _ensure_structure(self):
        """确保目录结构存在"""
        period = self.get_current_period()
        # 创建周期目录（用于通用数据库）
        (self.root_dir / period).mkdir(parents=True, exist_ok=True)
        # 创建归档目录
        (self.root_dir / "archive" / period).mkdir(parents=True, exist_ok=True)
    
    def get_current_period(self) -> str:
        """获取当前周期（每2年一个周期，如 2026_2027, 2028_2029）"""
        current_year = datetime.now().year
        cycle_start = (current_year // 2) * 2
        cycle_end = cycle_start + 1
        return f"{cycle_start}_{cycle_end}"
    
    def get_db_path(self, db_type: str, year: int = None, month: int = None) -> Path:
        """获取数据库路径（新架构：主题库在根目录，通用库在周期目录）"""
        # 系统数据库类型（放在周期目录下）
        system_dbs = {
            "emotion": "core_memory",
            "knowledge": "general",  # 原 core_knowledge 重命名为 general
            "core_knowledge": "general",  # 兼容旧调用
            "conversation": "conversations",
            "conversations": "conversations"  # 兼容 search_learn.py 的调用
        }
        
        # 是否为系统数据库
        is_system = db_type in system_dbs
        
        if is_system:
            # 系统数据库放在当前周期目录下
            period = self.get_current_period()
            base_name = system_dbs[db_type]
            
            # 对话数据库按月分库，其他系统数据库不按月分
            if db_type in ["conversation", "conversations"]:
                if year is None:
                    year = datetime.now().year
                if month is None:
                    month = datetime.now().month
                db_name = f"{base_name}_{year}_{month:02d}.db"
            else:
                db_name = f"{base_name}.db"
            
            return self.root_dir / period / db_name
        else:
            # 主题数据库放在根目录（如 Flutter.db, Python.db）
            # 忽略 year/month 参数
            return self.root_dir / f"{db_type}.db"
    
    def create_database(self, db_type: str, year: int = None, month: int = None) -> Path:
        """创建新数据库"""
        db_path = self.get_db_path(db_type, year, month)
        
        if db_path.exists():
            return db_path
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 通用表结构
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                tag TEXT,
                FOREIGN KEY (entry_id) REFERENCES entries(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_created ON entries(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_weight ON entries(weight DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_credibility ON entries(credibility_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_entry ON tags(entry_id)")
        
        conn.commit()
        conn.close()
        
        self._register_database(db_type, db_path)
        return db_path
    
    def _register_database(self, db_type: str, db_path: Path):
        """在 master.db 中注册数据库"""
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_type TEXT UNIQUE,
                db_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO databases (db_type, db_path, last_accessed)
            VALUES (?, ?, ?)
        """, (db_type, str(db_path), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_db_size(self, db_path: Path) -> int:
        """获取数据库大小（字节）"""
        return db_path.stat().st_size if db_path.exists() else 0
    
    def is_db_full(self, db_path: Path) -> bool:
        """检查数据库是否达到上限"""
        return self.get_db_size(db_path) >= MAX_DB_SIZE
    
    def compress_database(self, db_path: Path) -> Path:
        """压缩数据库为 .pack 格式"""
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        pack_path = db_path.with_suffix('.pack')
        
        # 使用 lzma 压缩
        with open(db_path, 'rb') as f_in:
            with lzma.open(pack_path, 'wb', preset=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return pack_path
    
    def decompress_database(self, pack_path: Path) -> Path:
        """解压 .pack 文件"""
        if not pack_path.exists():
            raise FileNotFoundError(f"Pack file not found: {pack_path}")
        
        db_path = pack_path.with_suffix('.db')
        
        with lzma.open(pack_path, 'rb') as f_in:
            with open(db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return db_path
    
    def archive_month(self, db_type: str, year: int, month: int):
        """归档指定月份的数据库（与 aex_admin.py 周期归档保持一致）"""
        db_path = self.get_db_path(db_type, year, month)
        
        if not db_path.exists():
            return None
        
        # 压缩
        pack_path = self.compress_database(db_path)
        
        # 移动到周期归档目录
        cycle = self._get_cycle_for_date(year, month)
        archive_dir = self.root_dir / "archive" / cycle
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / pack_path.name
        
        shutil.move(str(pack_path), str(archive_path))
        
        # 删除原数据库
        db_path.unlink()
        
        return archive_path
    
    def _get_cycle_for_date(self, year: int, month: int) -> str:
        """获取日期所属的周期（每2年一个周期）"""
        cycle_start = (year // 2) * 2
        cycle_end = cycle_start + 1
        return f"{cycle_start}_{cycle_end}"
    
    def query_entries(self, db_type: str, keyword: str = None, limit: int = 10) -> List[Dict]:
        """查询条目"""
        db_path = self.get_db_path(db_type)
        
        if not db_path.exists():
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if keyword:
            # 简化搜索：直接使用 LIKE 匹配
            cursor.execute("""
                SELECT * FROM entries 
                WHERE content LIKE ? 
                ORDER BY weight DESC, created_at DESC 
                LIMIT ?
            """, (f"%{keyword}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM entries 
                ORDER BY weight DESC, created_at DESC 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_entry(self, db_type: str, content: str, source: str = None, 
                  credibility: float = 0.5, metadata: Dict = None) -> int:
        """添加条目"""
        db_path = self.get_db_path(db_type)
        
        if not db_path.exists():
            self.create_database(db_type)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO entries (content, source, credibility_score, metadata)
            VALUES (?, ?, ?, ?)
        """, (content, source, credibility, json.dumps(metadata) if metadata else None))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return entry_id


if __name__ == "__main__":
    # 测试
    dbm = DatabaseManager()
    print(f"Root dir: {dbm.root_dir}")
    print(f"Current period: {dbm.get_current_period()}")
    
    # 创建测试数据库
    test_db = dbm.create_database("test")
    print(f"Created: {test_db}")
