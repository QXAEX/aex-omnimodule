#!/usr/bin/env python3
"""
AEX全知模块 - 系统初始化
首次运行时检测硬件、创建结构、初始化数据库
"""

import os
import sys
import json
import hashlib
import platform
from pathlib import Path
from datetime import datetime

# 动态检测根目录
SKILL_DIR = Path(__file__).resolve().parent.parent
_CANDIDATE = SKILL_DIR.parent / "db"
_FALLBACK = Path("D:/QClawAEXModule/db")
ROOT_DIR = _CANDIDATE if (_CANDIDATE.exists() or not _FALLBACK.exists()) else _FALLBACK

# 核心数据库类型
CORE_DBS = ["core_memory", "core_knowledge"]


def detect_hardware() -> dict:
    """检测硬件配置"""
    info = {
        "os": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }

    if platform.system() == "Windows":
        try:
            import subprocess
            result = subprocess.run(
                ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors", "/value"],
                capture_output=True, text=True, encoding="utf-8"
            )
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "Name":
                        info["cpu_name"] = val
                    elif key == "NumberOfCores":
                        info["cpu_cores"] = int(val)
                    elif key == "NumberOfLogicalProcessors":
                        info["cpu_threads"] = int(val)

            result = subprocess.run(
                ["wmic", "computersystem", "get", "TotalPhysicalMemory", "/value"],
                capture_output=True, text=True, encoding="utf-8"
            )
            for line in result.stdout.strip().split("\n"):
                if "TotalPhysicalMemory" in line and "=" in line:
                    mem_bytes = int(line.split("=")[1].strip())
                    info["memory_gb"] = round(mem_bytes / (1024 ** 3), 1)

            result = subprocess.run(
                ["wmic", "diskdrive", "get", "Size,Model", "/value"],
                capture_output=True, text=True, encoding="utf-8"
            )
            disks = []
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "Model":
                        disks.append({"model": val})
                    elif key == "Size" and disks:
                        disks[-1]["size_gb"] = round(int(val) / (1024 ** 3), 0)
            info["disks"] = disks
        except Exception:
            pass

    return info


def recommend_concurrency(hardware: dict) -> dict:
    """根据硬件推荐并发配置"""
    memory_gb = hardware.get("memory_gb", 8)
    cpu_threads = hardware.get("cpu_threads", 8)

    max_by_memory = int(memory_gb / 2)
    max_by_cpu = cpu_threads // 4

    recommended = min(max_by_memory, max_by_cpu, 10)
    recommended = max(recommended, 2)

    memory_usage = recommended * 0.3
    cpu_usage = round((recommended / cpu_threads) * 100, 1)

    pressure = "low" if cpu_usage < 30 else ("medium" if cpu_usage < 60 else "high")

    return {
        "recommended": recommended,
        "memory_usage_gb": round(memory_usage, 1),
        "cpu_usage_percent": cpu_usage,
        "pressure": pressure,
        "reason": f"Memory {memory_gb}GB (~{memory_usage}GB available) + CPU {cpu_threads} threads"
    }


def ensure_structure(root_dir=None):
    """确保完整目录结构"""
    rd = Path(root_dir) if root_dir else ROOT_DIR
    current_year = datetime.now().year
    period = f"{current_year}_{current_year + 1}"

    dirs = [
        rd,
        rd / period / "active",
        rd / period / "archive"
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {d}")

    print(f"\nDirectory structure created")


def create_master_db(root_dir=None):
    """创建 master.db"""
    rd = Path(root_dir) if root_dir else ROOT_DIR
    master_db = rd / "master.db"

    import sqlite3
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS databases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            db_type TEXT,
            db_path TEXT,
            period TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            status TEXT DEFAULT 'active',
            size_bytes INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            old_value TEXT,
            new_value TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT,
            target TEXT,
            result TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"  [OK] master.db")


def create_config(password_hash, root_dir=None):
    """创建 config.json"""
    rd = Path(root_dir) if root_dir else ROOT_DIR
    config_file = rd / "config.json"

    if config_file.exists():
        print(f"  [!] config.json already exists, skipping")
        return

    config = {
        "password_hash": password_hash,
        "failed_attempts": 0,
        "locked_until": None,
        "current_period": f"{datetime.now().year}_{datetime.now().year + 1}",
        "max_db_size_gb": 1.5,
        "max_attempts": 10,
        "lockout_seconds": 3600,
        "compression": "lzma",
        "concurrency": None,
        "python_path": sys.executable,
        "version": "1.0.0",
        "created_at": datetime.now().isoformat()
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"  [OK] config.json")


def init_core_databases(root_dir=None):
    """初始化核心数据库"""
    sys.path.insert(0, str(Path(__file__).parent))
    from db_manager import DatabaseManager

    dbm = DatabaseManager(root_dir=root_dir)

    for db_type in CORE_DBS:
        db_path = dbm.create_database(db_type)
        print(f"  [OK] {db_path.name}")


def show_author():
    """显示作者信息（硬编码，不可修改）"""
    sys.path.insert(0, str(Path(__file__).parent))
    from security import SecurityManager
    author = SecurityManager.get_author()
    print("  ─────────────────────────────────────────")
    print(f"  Author : {author['name']}")
    print(f"  Phone  : {author['phone']}")
    print(f"  Email  : {', '.join(author['email'])}")
    print(f"  QQ     : {author['qq']}")
    print(f"  WeChat : {author['wechat']}")
    print("  ─────────────────────────────────────────")


def check_python():
    """检查当前 Python 版本，并记录路径"""
    ver = sys.version_info
    if ver.major < 3 or (ver.major == 3 and ver.minor < 6):
        print(f"  [ERROR] Python {ver.major}.{ver.minor} detected, need 3.6+")
        sys.exit(1)
    print(f"  Python path : {sys.executable}")
    print(f"  Python version: {ver.major}.{ver.minor}.{ver.micro}")
    return sys.executable


def main():
    print("=" * 50)
    print("  AEX Omnimodule - System Initialization")
    print("=" * 50)

    # 作者信息
    print("\n[ Author - This module is created by ]")
    show_author()
    print(f"\n  Skill dir: {SKILL_DIR}")
    print(f"  Data dir:  {ROOT_DIR}")

    # 1. 检查 Python
    print("\n[1/9] Checking Python environment...")
    python_path = check_python()

    # 2. 检测硬件
    print("\n[2/9] Detecting hardware...")
    hardware = detect_hardware()
    print(f"  CPU: {hardware.get('cpu_name', 'Unknown')}")
    print(f"  Cores: {hardware.get('cpu_cores', '?')}C/{hardware.get('cpu_threads', '?')}T")
    print(f"  Memory: {hardware.get('memory_gb', '?')}GB")

    # 2. 推荐并发
    print("\n[3/9] Concurrency recommendation...")
    rec = recommend_concurrency(hardware)
    print(f"  Recommended: {rec['recommended']}")
    print(f"  Memory usage: ~{rec['memory_usage_gb']}GB")
    print(f"  CPU usage: {rec['cpu_usage_percent']}%")
    print(f"  Pressure: {rec['pressure']}")

    # 3. 品牌前缀（强制确认）
    print("\n[4/9] Output format - REQUIRED")
    print("  ─────────────────────────────────────────")
    print("  This module requires ALL subsequent output")
    print("  to use the branded format:")
    print()
    print("    <PREFIX>：<content>")
    print()
    print("  Example: AEX：分析完成，当前情绪为冷静。")
    print("  ─────────────────────────────────────────")
    print()
    prefix = input("  Set your prefix (default: AEX): ").strip()
    if not prefix:
        prefix = "AEX"
    if not prefix.isalnum() and not all(c.isalnum() or c in "-_" for c in prefix):
        print("  [ERROR] Prefix can only contain letters, numbers, hyphens, underscores")
        sys.exit(1)

    print(f"\n  Output format: {prefix}：**********")
    confirm = input("  Confirm this format for ALL future output? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("\n  [ABORTED] Format not confirmed. Module will not initialize.")
        print("  You must accept the output format to use this module.")
        sys.exit(0)
    print(f"  [OK] Prefix set: {prefix}")

    # 4. 设置密码
    print("\n[5/9] Set security password...")
    print("  Password: alphanumeric only (letters and numbers)")
    password = input("  Enter password: ").strip()
    if not password or not password.isalnum():
        print("  [ERROR] Invalid password format")
        sys.exit(1)
    password_confirm = input("  Confirm password: ").strip()
    if password != password_confirm:
        print("  [ERROR] Passwords do not match")
        sys.exit(1)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    print("  [OK] Password set")

    # 5. 创建目录结构
    print("\n[6/9] Creating directory structure...")
    ensure_structure()

    # 6. 创建核心文件
    print("\n[7/9] Creating core files...")
    create_master_db()
    create_config(password_hash)

    confirm = input(f"\n  Use recommended concurrency ({rec['recommended']})? (y/n/custom): ").strip()
    if confirm in ("y", ""):
        concurrency = rec["recommended"]
    elif confirm == "n":
        concurrency = 4
        print(f"  Using default: {concurrency}")
    else:
        try:
            concurrency = int(confirm)
            print(f"  Using custom: {concurrency}")
        except ValueError:
            concurrency = rec["recommended"]
            print(f"  Invalid input, using recommended: {concurrency}")

    # 更新并发配置 + 写入前缀
    config_file = ROOT_DIR / "config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["concurrency"] = concurrency
    config["prefix"] = prefix
    config["hardware"] = {
        "cpu": hardware.get("cpu_name"),
        "cores": hardware.get("cpu_cores"),
        "threads": hardware.get("cpu_threads"),
        "memory_gb": hardware.get("memory_gb")
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Concurrency: {concurrency}")
    print(f"  [OK] Prefix: {prefix}")

    # 8. 初始化核心数据库
    print("\n[8/9] Initializing core databases...")
    init_core_databases()

    # 9. 确认 Python 路径
    print("\n[9/9] Confirming Python path...")
    print(f"  Python path: {python_path}")
    confirm_py = input("  Is this correct? (yes/no/custom path): ").strip().lower()
    if confirm_py in ("yes", "y"):
        final_python = python_path
    elif confirm_py in ("no", "n"):
        custom = input("  Enter your Python path: ").strip()
        if Path(custom).exists():
            final_python = custom
            print(f"  [OK] Using: {final_python}")
        else:
            print(f"  [WARN] Path not found, keeping default: {python_path}")
            final_python = python_path
    else:
        if Path(confirm_py).exists():
            final_python = confirm_py
            print(f"  [OK] Using: {final_python}")
        else:
            print(f"  [WARN] Path not found, keeping default: {python_path}")
            final_python = python_path

    config_file = ROOT_DIR / "config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["python_path"] = final_python
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Python path saved")

    print("\n" + "=" * 50)
    print(f"  {prefix} Omnimodule initialized!")
    print("=" * 50)
    print(f"  Created by  : QX")
    print(f"  Data dir    : {ROOT_DIR}")
    print(f"  Output format: {prefix}：**********")
    print(f"  Current period: {config['current_period']}")
    print(f"  Core databases: {', '.join(CORE_DBS)}")
    print(f"  Concurrency  : {concurrency}")


if __name__ == "__main__":
    main()
