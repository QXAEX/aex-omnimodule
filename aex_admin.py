#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AEX 全知模块 - 超级管理控制台 (AEX Super Admin Console)
═══════════════════════════════════════════════════════════

拥有 AEX 系统的最高权限，提供完整的管理功能：
- 安装/卸载/更新
- 配置管理
- 数据库操作（多数据库支持）
- SQL 执行
- 分页浏览
- 中文数据库名支持

Usage:
    python aex_admin.py                    # 交互式菜单
    python aex_admin.py --install          # 安装 AEX
    python aex_admin.py --uninstall        # 卸载 AEX
    python aex_admin.py --config           # 配置管理
    python aex_admin.py --db               # 数据库管理
    python aex_admin.py --status           # 查看状态
"""

import argparse
import os
import sys
import shutil
import subprocess
import json
import sqlite3
import platform
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# ═══════════════════════════════════════════════════════════════════════════
# 配置常量
# ═══════════════════════════════════════════════════════════════════════════

AEX_VERSION = "1.0.0"
AEX_ADMIN_VERSION = "1.0.0"

# 默认路径
DEFAULT_AEX_DIR = Path("D:/QClawAEXModule")
DEFAULT_OPENCLAW_DIR = Path("D:/QClaw/resources/openclaw")
DEFAULT_PYTHON = Path("D:/Python/3/python.exe")

# 数据库配置 - 支持中文名
DATABASES: Dict[str, Dict[str, Any]] = {
    "master": {
        "name": "主控数据库",
        "filename": "master.db",
        "description": "系统核心配置与注册信息",
        "readonly": False,
    },
    "emotion": {
        "name": "情绪记忆库",
        "filename": "core_memory_{year}_{month}.db",
        "description": "情绪分析历史记录与模式",
        "readonly": False,
        "rotated": True,  # 按月轮转
    },
    "knowledge": {
        "name": "知识存储库",
        "filename": "core_knowledge_{year}_{month}.db",
        "description": "检索到的知识与学习记录",
        "readonly": False,
        "rotated": True,
    },
    "conversation": {
        "name": "对话存档库",
        "filename": "conversations_{year}_{month}.db",
        "description": "完整对话历史记录",
        "readonly": False,
        "rotated": True,
    },
    "analytics": {
        "name": "统计分析库",
        "filename": "analytics.db",
        "description": "使用统计与性能分析",
        "readonly": False,
    },
    "backup": {
        "name": "备份归档库",
        "filename": "backup_{year}_{month}.db",
        "description": "自动备份与归档数据",
        "readonly": True,
        "rotated": True,
    },
}

# 依赖包
REQUIRED_PACKAGES = ["numpy", "scikit-learn"]

# GitHub 仓库
GITHUB_REPO = "https://github.com/QXAEX/aex-omnimodule"

# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AEXConfig:
    """AEX 配置"""
    initialized: bool = True
    version: str = AEX_VERSION
    prefix: str = "AEX"
    emotion_enabled: bool = True
    knowledge_enabled: bool = True
    python_path: str = str(DEFAULT_PYTHON)
    scripts_dir: str = str(DEFAULT_AEX_DIR / "skill" / "scripts")
    db_dir: str = str(DEFAULT_AEX_DIR / "db")
    admin_password_hash: str = ""  # 可选的安全控制
    log_level: str = "info"
    max_history_months: int = 12
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AEXConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class DBInfo:
    """数据库信息"""
    key: str
    chinese_name: str
    filename: str
    filepath: Path
    description: str
    size_bytes: int
    size_human: str
    last_modified: str
    table_count: int
    row_counts: Dict[str, int]
    is_rotated: bool
    readonly: bool

# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def clear_screen():
    """清屏"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_header(title: str):
    """打印标题"""
    print("\n" + "═" * 70)
    print(f"  {title}")
    print("═" * 70)

def print_success(msg: str):
    print(f"  ✓ {msg}")

def print_error(msg: str):
    print(f"  ✗ {msg}", file=sys.stderr)

def print_warning(msg: str):
    print(f"  ! {msg}")

def print_info(msg: str):
    print(f"  ℹ {msg}")

def print_menu_item(key: str, desc: str):
    print(f"    [{key}] {desc}")

def input_prompt(prompt: str) -> str:
    """输入提示"""
    return input(f"  > {prompt}: ").strip()

def confirm(prompt: str) -> bool:
    """确认提示"""
    response = input(f"  > {prompt} [y/N]: ").strip().lower()
    return response in ('y', 'yes')

def format_bytes(size: int) -> str:
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_current_year_month() -> Tuple[int, int]:
    """获取当前年月"""
    now = datetime.now()
    return now.year, now.month

def get_db_filename(template: str, year: int, month: int) -> str:
    """生成数据库文件名"""
    return template.format(year=year, month=f"{month:02d}")

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True) -> Tuple[int, str, str]:
    """运行命令"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            encoding='utf-8', errors='ignore'
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd,
                output=result.stdout, stderr=result.stderr
            )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        if check:
            raise
        return -1, "", str(e)

@contextmanager
def db_connection(db_path: Path, readonly: bool = False):
    """数据库连接上下文管理器"""
    conn = None
    try:
        uri = f"file:{db_path}?mode=ro" if readonly else str(db_path)
        conn = sqlite3.connect(uri, uri=readonly)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# AEX 管理员类
# ═══════════════════════════════════════════════════════════════════════════

class AEXAdmin:
    """AEX 超级管理员"""
    
    def __init__(self, aex_dir: Path = DEFAULT_AEX_DIR):
        self.aex_dir = aex_dir
        self.db_dir = aex_dir / "db"
        self.scripts_dir = aex_dir / "skill" / "scripts"
        self.config_path = self.db_dir / "config.json"
        self.config: Optional[AEXConfig] = None
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = AEXConfig.from_dict(data)
            except Exception as e:
                print_warning(f"加载配置失败: {e}")
                self.config = AEXConfig()
        else:
            self.config = AEXConfig()
    
    def _save_config(self):
        """保存配置"""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
    
    # ─────────────────────────────────────────────────────────────────────
    # 安装/卸载
    # ─────────────────────────────────────────────────────────────────────
    
    def install(self, auto: bool = False) -> bool:
        """安装 AEX"""
        print_header("安装 AEX 全知模块")
        
        # 检查环境
        if not self._check_python():
            return False
        
        # 创建目录
        print("\n▶ 创建目录结构...")
        for subdir in ["db", "skill/scripts", "skill/templates", "logs", "backup"]:
            (self.aex_dir / subdir).mkdir(parents=True, exist_ok=True)
            print_success(f"创建: {self.aex_dir / subdir}")
        
        # 安装依赖
        print("\n▶ 安装 Python 依赖...")
        for pkg in REQUIRED_PACKAGES:
            print(f"  安装 {pkg}...")
            try:
                run_command([sys.executable, "-m", "pip", "install", "-q", pkg])
                print_success(f"{pkg} 安装完成")
            except Exception as e:
                print_error(f"{pkg} 安装失败: {e}")
        
        # 创建默认脚本（如果源码不存在）
        self._create_default_scripts()
        
        # 保存配置
        self._save_config()
        print_success(f"配置文件: {self.config_path}")
        
        # 初始化数据库
        self._init_databases()
        
        print("\n" + "═" * 70)
        print("  安装完成！")
        print("═" * 70)
        print(f"""
  AEX 目录: {self.aex_dir}
  配置文件: {self.config_path}
  
  下一步:
  1. 运行 'python aex_admin.py --db' 查看数据库
  2. 运行 'python aex_admin.py --config' 修改配置
  3. 将 AEX 集成到 qclaw-plugin
        """)
        return True
    
    def uninstall(self, keep_data: bool = False) -> bool:
        """卸载 AEX"""
        print_header("卸载 AEX 全知模块")
        
        if not confirm("确认卸载 AEX？这将删除所有文件"):
            print("取消卸载")
            return False
        
        if keep_data:
            # 只删除程序，保留数据
            for subdir in ["skill", "logs"]:
                path = self.aex_dir / subdir
                if path.exists():
                    shutil.rmtree(path)
                    print_success(f"删除: {path}")
        else:
            # 完全删除
            if self.aex_dir.exists():
                shutil.rmtree(self.aex_dir)
                print_success(f"删除: {self.aex_dir}")
        
        print("\n  卸载完成")
        return True
    
    def _check_python(self) -> bool:
        """检查 Python 环境"""
        print("▶ 检查 Python 环境...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print_error(f"Python 版本过低: {version.major}.{version.minor}")
            return False
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def _create_default_scripts(self):
        """创建默认脚本"""
        # 情绪分析器
        emotion_script = self.scripts_dir / "emotion_analyzer.py"
        if not emotion_script.exists():
            self.scripts_dir.mkdir(parents=True, exist_ok=True)
            with open(emotion_script, 'w', encoding='utf-8') as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""情绪分析器"""
import sys
import json

class EmotionAnalyzer:
    def analyze(self, text: str) -> dict:
        # 简化版实现
        emotions = {
            "happy": ["开心", "快乐", "棒", "好", "喜欢"],
            "sad": ["难过", "伤心", "失望", "糟", "坏"],
            "angry": ["生气", "愤怒", "讨厌", "烦"],
            "neutral": []
        }
        
        text_lower = text.lower()
        detected = "neutral"
        intensity = 0.3
        
        for emotion, keywords in emotions.items():
            for kw in keywords:
                if kw in text_lower:
                    detected = emotion
                    intensity = min(0.9, intensity + 0.2)
                    break
        
        tone_map = {
            "happy": "轻松自然",
            "sad": "温和安慰",
            "angry": "冷静理性",
            "neutral": "专业客观"
        }
        
        return {
            "emotion": detected,
            "intensity": round(intensity * 100),
            "tone_suggestion": tone_map.get(detected, "专业客观")
        }

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    analyzer = EmotionAnalyzer()
    result = analyzer.analyze(text)
    print(json.dumps(result, ensure_ascii=False))
''')
            print_success(f"创建: {emotion_script}")
        
        # 知识检索
        search_script = self.scripts_dir / "search_learn.py"
        if not search_script.exists():
            with open(search_script, 'w', encoding='utf-8') as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识检索与学习"""
import sys
import json
import sqlite3
from pathlib import Path

class SearchLearnManager:
    def __init__(self):
        self.db_dir = Path("D:/QClawAEXModule/db")
    
    def search(self, query: str) -> list:
        # 简化版实现 - 返回空列表
        return []
    
    def evaluate_and_store(self, content: str, source: str, relevance: float):
        pass

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    manager = SearchLearnManager()
    results = manager.search(query)
    print(json.dumps(results, ensure_ascii=False))
''')
            print_success(f"创建: {search_script}")
        
        # 数据库管理
        db_script = self.scripts_dir / "db_manager.py"
        if not db_script.exists():
            with open(db_script, 'w', encoding='utf-8') as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库管理器"""
import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self):
        self.db_dir = Path("D:/QClawAEXModule/db")
        self.db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self, db_name: str):
        db_path = self.db_dir / db_name
        return sqlite3.connect(db_path)
''')
            print_success(f"创建: {db_script}")
    
    def _init_databases(self):
        """初始化数据库"""
        print("\n▶ 初始化数据库...")
        year, month = get_current_year_month()
        
        # 主控数据库
        master_path = self.db_dir / "master.db"
        with db_connection(master_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS databases (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    chinese_name TEXT,
                    filename TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                INSERT OR IGNORE INTO databases VALUES
                    (1, 'master', '主控数据库', 'master.db', '系统核心配置', datetime('now')),
                    (2, 'emotion', '情绪记忆库', 'core_memory_{year}_{month}.db', '情绪分析历史', datetime('now')),
                    (3, 'knowledge', '知识存储库', 'core_knowledge_{year}_{month}.db', '知识检索记录', datetime('now'));
            ''')
            conn.commit()
        print_success(f"初始化: {master_path}")
        
        # 情绪数据库
        emotion_path = self.db_dir / f"core_memory_{year}_{month:02d}.db"
        with db_connection(emotion_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    emotion TEXT,
                    intensity INTEGER,
                    tone_suggestion TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_emotion ON emotions(emotion);
                CREATE INDEX IF NOT EXISTS idx_created ON emotions(created_at);
            ''')
            conn.commit()
        print_success(f"初始化: {emotion_path}")
        
        # 知识数据库
        knowledge_path = self.db_dir / f"core_knowledge_{year}_{month:02d}.db"
        with db_connection(knowledge_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    source TEXT,
                    relevance REAL,
                    query TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_relevance ON knowledge(relevance);
                CREATE INDEX IF NOT EXISTS idx_query ON knowledge(query);
            ''')
            conn.commit()
        print_success(f"初始化: {knowledge_path}")
    
    # ─────────────────────────────────────────────────────────────────────
    # 配置管理
    # ─────────────────────────────────────────────────────────────────────
    
    def config_menu(self):
        """配置管理菜单"""
        while True:
            clear_screen()
            print_header("配置管理")
            
            print("\n  当前配置:")
            print(f"    前缀: {self.config.prefix}")
            print(f"    情绪分析: {'开启' if self.config.emotion_enabled else '关闭'}")
            print(f"    知识检索: {'开启' if self.config.knowledge_enabled else '关闭'}")
            print(f"    Python 路径: {self.config.python_path}")
            print(f"    日志级别: {self.config.log_level}")
            print(f"    历史保留: {self.config.max_history_months} 个月")
            
            print("\n  操作:")
            print_menu_item("1", "修改前缀")
            print_menu_item("2", "开关情绪分析")
            print_menu_item("3", "开关知识检索")
            print_menu_item("4", "修改 Python 路径")
            print_menu_item("5", "修改日志级别")
            print_menu_item("6", "修改历史保留时间")
            print_menu_item("7", "查看完整配置")
            print_menu_item("8", "保存并返回")
            print_menu_item("0", "放弃修改")
            
            choice = input_prompt("选择")
            
            if choice == "1":
                new_prefix = input_prompt("新前缀")
                if new_prefix:
                    self.config.prefix = new_prefix
                    print_success(f"前缀已修改为: {new_prefix}")
            
            elif choice == "2":
                self.config.emotion_enabled = not self.config.emotion_enabled
                print_success(f"情绪分析: {'开启' if self.config.emotion_enabled else '关闭'}")
            
            elif choice == "3":
                self.config.knowledge_enabled = not self.config.knowledge_enabled
                print_success(f"知识检索: {'开启' if self.config.knowledge_enabled else '关闭'}")
            
            elif choice == "4":
                new_path = input_prompt("Python 路径")
                if new_path and Path(new_path).exists():
                    self.config.python_path = new_path
                    print_success(f"Python 路径已修改")
                else:
                    print_error("路径无效")
            
            elif choice == "5":
                print("  可选: debug, info, warning, error")
                new_level = input_prompt("日志级别")
                if new_level in ["debug", "info", "warning", "error"]:
                    self.config.log_level = new_level
                    print_success(f"日志级别已修改")
            
            elif choice == "6":
                new_months = input_prompt("保留月数")
                if new_months.isdigit():
                    self.config.max_history_months = int(new_months)
                    print_success(f"历史保留时间已修改")
            
            elif choice == "7":
                print("\n  完整配置:")
                print(json.dumps(self.config.to_dict(), indent=4, ensure_ascii=False))
                input("\n  按 Enter 继续...")
            
            elif choice == "8":
                self._save_config()
                print_success("配置已保存")
                break
            
            elif choice == "0":
                self._load_config()  # 重新加载，放弃修改
                break
    
    # ─────────────────────────────────────────────────────────────────────
    # 数据库管理
    # ─────────────────────────────────────────────────────────────────────
    
    def db_menu(self):
        """数据库管理菜单"""
        while True:
            clear_screen()
            print_header("数据库管理")
            
            print("\n  数据库列表:")
            dbs = self._list_databases()
            
            for i, db in enumerate(dbs, 1):
                status = "📄" if db.readonly else "📝"
                rotated = " (轮转)" if db.is_rotated else ""
                print(f"    {status} [{i}] {db.chinese_name}")
                print(f"        文件: {db.filename}")
                print(f"        大小: {db.size_human}")
                print(f"        描述: {db.description}{rotated}")
                print()
            
            print("  操作:")
            print_menu_item("1-N", "查看数据库详情")
            print_menu_item("S", "SQL 查询")
            print_menu_item("B", "备份数据库")
            print_menu_item("C", "清理旧数据")
            print_menu_item("R", "刷新列表")
            print_menu_item("0", "返回主菜单")
            
            choice = input_prompt("选择")
            
            if choice == "0":
                break
            elif choice.upper() == "R":
                continue
            elif choice.upper() == "S":
                self._sql_query_menu(dbs)
            elif choice.upper() == "B":
                self._backup_menu(dbs)
            elif choice.upper() == "C":
                self._cleanup_menu()
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(dbs):
                    self._db_detail_menu(dbs[idx])
    
    def _list_databases(self) -> List[DBInfo]:
        """列出所有数据库"""
        dbs = []
        year, month = get_current_year_month()
        
        for key, info in DATABASES.items():
            if info.get("rotated"):
                filename = get_db_filename(info["filename"], year, month)
            else:
                filename = info["filename"]
            
            filepath = self.db_dir / filename
            
            if filepath.exists():
                stat = filepath.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # 获取表信息
                tables = {}
                row_counts = {}
                try:
                    with db_connection(filepath, readonly=True) as conn:
                        cursor = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                        for row in cursor.fetchall():
                            table_name = row[0]
                            tables[table_name] = True
                            try:
                                count = conn.execute(
                                    f"SELECT COUNT(*) FROM \"{table_name}\""
                                ).fetchone()[0]
                                row_counts[table_name] = count
                            except:
                                row_counts[table_name] = -1
                except Exception as e:
                    print_warning(f"读取 {filename} 失败: {e}")
                
                dbs.append(DBInfo(
                    key=key,
                    chinese_name=info["name"],
                    filename=filename,
                    filepath=filepath,
                    description=info["description"],
                    size_bytes=size,
                    size_human=format_bytes(size),
                    last_modified=mtime,
                    table_count=len(tables),
                    row_counts=row_counts,
                    is_rotated=info.get("rotated", False),
                    readonly=info.get("readonly", False),
                ))
            else:
                # 数据库不存在，显示占位
                dbs.append(DBInfo(
                    key=key,
                    chinese_name=info["name"],
                    filename=filename,
                    filepath=filepath,
                    description=info["description"],
                    size_bytes=0,
                    size_human="0 B",
                    last_modified="未创建",
                    table_count=0,
                    row_counts={},
                    is_rotated=info.get("rotated", False),
                    readonly=info.get("readonly", False),
                ))
        
        return dbs
    
    def _db_detail_menu(self, db: DBInfo):
        """数据库详情菜单"""
        while True:
            clear_screen()
            print_header(f"数据库详情 - {db.chinese_name}")
            
            print(f"\n  基本信息:")
            print(f"    中文名: {db.chinese_name}")
            print(f"    文件名: {db.filename}")
            print(f"    路径: {db.filepath}")
            print(f"    大小: {db.size_human}")
            print(f"    修改时间: {db.last_modified}")
            print(f"    描述: {db.description}")
            print(f"    只读: {'是' if db.readonly else '否'}")
            print(f"    轮转: {'是' if db.is_rotated else '否'}")
            
            print(f"\n  表信息 ({db.table_count} 个表):")
            for table, count in db.row_counts.items():
                if count >= 0:
                    print(f"    - {table}: {count} 行")
                else:
                    print(f"    - {table}: ? 行")
            
            print("\n  操作:")
            print_menu_item("1", "浏览数据（分页）")
            print_menu_item("2", "执行 SQL")
            print_menu_item("3", "导出数据")
            print_menu_item("4", "修复/优化")
            print_menu_item("0", "返回")
            
            choice = input_prompt("选择")
            
            if choice == "0":
                break
            elif choice == "1":
                self._browse_data_paginated(db)
            elif choice == "2":
                self._execute_sql_on_db(db)
            elif choice == "3":
                self._export_db(db)
            elif choice == "4":
                self._optimize_db(db)
    
    def _browse_data_paginated(self, db: DBInfo, table_name: Optional[str] = None):
        """分页浏览数据"""
        if not table_name:
            # 选择表
            tables = list(db.row_counts.keys())
            if not tables:
                print_error("没有可用的表")
                input("按 Enter 继续...")
                return
            
            print("\n  可用表:")
            for i, t in enumerate(tables, 1):
                print(f"    [{i}] {t}")
            
            choice = input_prompt("选择表编号")
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(tables):
                return
            table_name = tables[int(choice) - 1]
        
        # 分页浏览
        page_size = 20
        page = 0
        
        while True:
            clear_screen()
            print_header(f"浏览 {db.chinese_name}.{table_name}")
            
            try:
                with db_connection(db.filepath, readonly=True) as conn:
                    # 获取总数
                    total = conn.execute(
                        f'SELECT COUNT(*) FROM "{table_name}"'
                    ).fetchone()[0]
                    
                    # 获取列名
                    cursor = conn.execute(f'SELECT * FROM "{table_name}" LIMIT 0')
                    columns = [desc[0] for desc in cursor.description]
                    
                    # 获取数据
                    offset = page * page_size
                    rows = conn.execute(
                        f'SELECT * FROM "{table_name}" LIMIT {page_size} OFFSET {offset}'
                    ).fetchall()
                    
                    # 显示
                    print(f"\n  第 {page + 1}/{(total + page_size - 1) // page_size} 页 (共 {total} 行)\n")
                    
                    # 表头
                    header = " | ".join(f"{c[:15]:15}" for c in columns)
                    print(f"  {header}")
                    print("  " + "-" * len(header))
                    
                    # 数据
                    for row in rows:
                        values = []
                        for val in row:
                            s = str(val)[:15] if val is not None else "NULL"
                            values.append(f"{s:15}")
                        print(f"  {' | '.join(values)}")
                    
                    print(f"\n  操作: [N]下一页 [P]上一页 [J]跳转 [S]搜索 [0]返回")
                    choice = input_prompt("选择").upper()
                    
                    if choice == "0":
                        break
                    elif choice == "N":
                        if offset + page_size < total:
                            page += 1
                    elif choice == "P":
                        if page > 0:
                            page -= 1
                    elif choice == "J":
                        new_page = input_prompt("跳转到页")
                        if new_page.isdigit():
                            page = max(0, int(new_page) - 1)
                    elif choice == "S":
                        self._search_in_table(db, table_name, columns)
                        
            except Exception as e:
                print_error(f"查询失败: {e}")
                input("按 Enter 继续...")
                break
    
    def _search_in_table(self, db: DBInfo, table_name: str, columns: List[str]):
        """在表中搜索"""
        keyword = input_prompt("搜索关键词")
        if not keyword:
            return
        
        print(f"\n  在列 {columns} 中搜索 '{keyword}'...")
        
        try:
            with db_connection(db.filepath, readonly=True) as conn:
                # 构建 WHERE 子句
                conditions = [f'"{col}" LIKE ?' for col in columns]
                where_clause = " OR ".join(conditions)
                params = [f"%{keyword}%"] * len(columns)
                
                rows = conn.execute(
                    f'SELECT * FROM "{table_name}" WHERE {where_clause} LIMIT 50',
                    params
                ).fetchall()
                
                print(f"\n  找到 {len(rows)} 条结果:\n")
                for row in rows:
                    print(f"    {dict(zip(columns, row))}")
                
                input("\n按 Enter 继续...")
        except Exception as e:
            print_error(f"搜索失败: {e}")
            input("按 Enter 继续...")
    
    def _execute_sql_on_db(self, db: DBInfo):
        """在指定数据库执行 SQL"""
        print(f"\n  在 {db.chinese_name} 上执行 SQL")
        print("  支持: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER")
        
        sql = input_prompt("SQL 语句")
        if not sql:
            return
        
        try:
            readonly = db.readonly or sql.strip().upper().startswith("SELECT")
            
            with db_connection(db.filepath, readonly=readonly) as conn:
                cursor = conn.execute(sql)
                
                if sql.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        print(f"\n  返回 {len(rows)} 行:\n")
                        for row in rows[:20]:  # 最多显示20行
                            print(f"    {dict(zip(columns, row))}")
                        if len(rows) > 20:
                            print(f"    ... 还有 {len(rows) - 20} 行")
                else:
                    conn.commit()
                    print_success(f"执行成功，影响 {cursor.rowcount} 行")
                
                input("\n按 Enter 继续...")
        except Exception as e:
            print_error(f"执行失败: {e}")
            input("按 Enter 继续...")
    
    def _sql_query_menu(self, dbs: List[DBInfo]):
        """SQL 查询菜单"""
        clear_screen()
        print_header("SQL 查询")
        
        print("\n  选择数据库:")
        for i, db in enumerate(dbs, 1):
            print(f"    [{i}] {db.chinese_name} ({db.filename})")
        
        choice = input_prompt("数据库编号")
        if not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(dbs):
            return
        
        db = dbs[idx]
        self._execute_sql_on_db(db)
    
    def _export_db(self, db: DBInfo):
        """导出数据库"""
        print(f"\n  导出 {db.chinese_name}")
        
        export_dir = self.aex_dir / "backup"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"{db.key}_{timestamp}.sql"
        
        try:
            with db_connection(db.filepath, readonly=True) as conn:
                # 导出 schema 和 data
                with open(export_file, 'w', encoding='utf-8') as f:
                    for line in conn.iterdump():
                        f.write(line + '\n')
            
            print_success(f"导出完成: {export_file}")
            print_info(f"文件大小: {format_bytes(export_file.stat().st_size)}")
        except Exception as e:
            print_error(f"导出失败: {e}")
        
        input("\n按 Enter 继续...")
    
    def _optimize_db(self, db: DBInfo):
        """优化数据库"""
        print(f"\n  优化 {db.chinese_name}...")
        
        try:
            with db_connection(db.filepath) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            print_success("优化完成")
        except Exception as e:
            print_error(f"优化失败: {e}")
        
        input("\n按 Enter 继续...")
    
    def _backup_menu(self, dbs: List[DBInfo]):
        """备份菜单"""
        clear_screen()
        print_header("数据库备份")
        
        print("\n  选择要备份的数据库:")
        print_menu_item("A", "全部备份")
        for i, db in enumerate(dbs, 1):
            print_menu_item(str(i), f"{db.chinese_name}")
        print_menu_item("0", "取消")
        
        choice = input_prompt("选择")
        
        if choice == "0":
            return
        
        backup_dir = self.aex_dir / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if choice.upper() == "A":
            # 备份全部
            for db in dbs:
                if db.filepath.exists():
                    dest = backup_dir / f"{db.key}_{timestamp}.db"
                    shutil.copy2(db.filepath, dest)
                    print_success(f"备份: {db.chinese_name} -> {dest.name}")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(dbs):
                db = dbs[idx]
                if db.filepath.exists():
                    dest = backup_dir / f"{db.key}_{timestamp}.db"
                    shutil.copy2(db.filepath, dest)
                    print_success(f"备份: {db.chinese_name} -> {dest.name}")
        
        input("\n按 Enter 继续...")
    
    def _cleanup_menu(self):
        """清理旧数据菜单"""
        clear_screen()
        print_header("清理旧数据")
        
        print(f"\n  当前设置: 保留最近 {self.config.max_history_months} 个月的数据")
        
        year, month = get_current_year_month()
        cutoff_year = year
        cutoff_month = month - self.config.max_history_months
        while cutoff_month <= 0:
            cutoff_year -= 1
            cutoff_month += 12
        
        print(f"  将删除 {cutoff_year}年{cutoff_month:02d}月 之前的数据")
        
        if not confirm("确认清理"):
            return
        
        # 查找并删除旧数据库文件
        deleted = []
        for file in self.db_dir.glob("*.db"):
            # 解析文件名中的日期
            match = re.search(r'(\d{4})_(\d{2})', file.name)
            if match:
                file_year = int(match.group(1))
                file_month = int(match.group(2))
                
                if (file_year < cutoff_year or 
                    (file_year == cutoff_year and file_month < cutoff_month)):
                    if file.name != "master.db":  # 不删除主控库
                        file.unlink()
                        deleted.append(file.name)
        
        print(f"\n  已删除 {len(deleted)} 个旧数据库文件:")
        for name in deleted:
            print(f"    - {name}")
        
        input("\n按 Enter 继续...")
    
    # ─────────────────────────────────────────────────────────────────────
    # 状态查看
    # ─────────────────────────────────────────────────────────────────────
    
    def show_status(self):
        """显示状态"""
        clear_screen()
        print_header("AEX 系统状态")
        
        print("\n  📊 基本信息:")
        print(f"    AEX 版本: {AEX_VERSION}")
        print(f"    管理器版本: {AEX_ADMIN_VERSION}")
        print(f"    安装目录: {self.aex_dir}")
        print(f"    目录存在: {'是' if self.aex_dir.exists() else '否'}")
        
        print("\n  ⚙️ 配置状态:")
        print(f"    已初始化: {'是' if self.config.initialized else '否'}")
        print(f"    前缀: {self.config.prefix}")
        print(f"    情绪分析: {'开启' if self.config.emotion_enabled else '关闭'}")
        print(f"    知识检索: {'开启' if self.config.knowledge_enabled else '关闭'}")
        
        print("\n  🗄️ 数据库状态:")
        dbs = self._list_databases()
        total_size = 0
        for db in dbs:
            status = "✓" if db.filepath.exists() else "✗"
            total_size += db.size_bytes
            print(f"    {status} {db.chinese_name}: {db.size_human}")
        print(f"    总计: {format_bytes(total_size)}")
        
        print("\n  🐍 Python 环境:")
        print(f"    当前 Python: {sys.executable}")
        print(f"    版本: {sys.version.split()[0]}")
        print(f"    配置路径: {self.config.python_path}")
        
        # 检查依赖
        print("\n  📦 依赖包:")
        for pkg in REQUIRED_PACKAGES:
            try:
                __import__(pkg)
                print(f"    ✓ {pkg}")
            except ImportError:
                print(f"    ✗ {pkg} (未安装)")
        
        input("\n  按 Enter 返回...")
    
    # ─────────────────────────────────────────────────────────────────────
    # 主菜单
    # ─────────────────────────────────────────────────────────────────────
    
    def main_menu(self):
        """主菜单"""
        while True:
            clear_screen()
            print_header("AEX 全知模块 - 超级管理控制台")
            print(f"\n  版本: {AEX_ADMIN_VERSION} | 路径: {self.aex_dir}")
            
            print("\n  主菜单:")
            print_menu_item("1", "📦 安装/修复 AEX")
            print_menu_item("2", "⚙️ 配置管理")
            print_menu_item("3", "🗄️ 数据库管理")
            print_menu_item("4", "📊 系统状态")
            print_menu_item("5", "🔄 重启 Gateway")
            print_menu_item("6", "❌ 卸载 AEX")
            print_menu_item("0", "退出")
            
            choice = input_prompt("选择")
            
            if choice == "1":
                self.install()
                input("\n按 Enter 继续...")
            elif choice == "2":
                self.config_menu()
            elif choice == "3":
                self.db_menu()
            elif choice == "4":
                self.show_status()
            elif choice == "5":
                self._restart_gateway()
            elif choice == "6":
                if self.uninstall():
                    break
            elif choice == "0":
                print("\n  再见！")
                break
    
    def _restart_gateway(self):
        """重启 Gateway"""
        print("\n  正在重启 OpenClaw Gateway...")
        try:
            subprocess.Popen(
                ["openclaw", "gateway", "restart"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print_success("重启命令已发送")
        except Exception as e:
            print_error(f"重启失败: {e}")
        input("\n按 Enter 继续...")

# ═══════════════════════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AEX 全知模块 - 超级管理控制台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python aex_admin.py                    # 交互式菜单
    python aex_admin.py --install          # 安装 AEX
    python aex_admin.py --uninstall        # 卸载 AEX
    python aex_admin.py --config           # 配置管理
    python aex_admin.py --db               # 数据库管理
    python aex_admin.py --status           # 查看状态
        """
    )
    parser.add_argument("--install", action="store_true", help="安装 AEX")
    parser.add_argument("--uninstall", action="store_true", help="卸载 AEX")
    parser.add_argument("--config", action="store_true", help="配置管理")
    parser.add_argument("--db", action="store_true", help="数据库管理")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--aex-dir", type=Path, default=DEFAULT_AEX_DIR, help="AEX 目录")
    parser.add_argument("--auto", action="store_true", help="自动模式")
    
    args = parser.parse_args()
    
    admin = AEXAdmin(aex_dir=args.aex_dir)
    
    if args.install:
        admin.install(auto=args.auto)
    elif args.uninstall:
        admin.uninstall()
    elif args.config:
        admin.config_menu()
    elif args.db:
        admin.db_menu()
    elif args.status:
        admin.show_status()
    else:
        admin.main_menu()

if __name__ == "__main__":
    main()
