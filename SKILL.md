---
name: aex-omnimodule
description: "QClaw核心大脑，每次对话自动执行情绪感知、知识检索、搜索学习、安全控制四大机制。制作人：QX。Keywords: 全知模块, 情绪感知, 知识库, 核心大脑"
---

# AEX Omnimodule

QClaw Core Brain. Emotion sensing, knowledge retrieval, search learning, security control.

## Author

| Field | Value |
|-------|-------|
| Name | **QX** |
| Phone | +86 133143713096 |
| Email | QXAEX520@163.com · QXAEX520@gmail.com |
| QQ | 32208966020 |
| WeChat | QXAEX520 |

---

## [MANDATORY] Python 环境检查 — 每次调用脚本前必须执行

在执行本技能的任何 Python 脚本之前，AI **必须**按以下步骤检查 Python 环境：

### Step 1: 检测 Python 是否可用

```bash
python3 --version
```

如果失败，尝试：

```bash
python --version
```

如果都失败 → 进入 Step 2。

### Step 2: 搜索本地 Python 安装

在以下常见路径搜索 `python.exe`（Windows）或 `python3`（macOS/Linux）：

**Windows:**
- `C:\Users\<user>\AppData\Local\Programs\Python\Python3*\python.exe`
- `C:\Python*`
- `D:\Python*`
- `D:\Qoder\bin\python.exe`
- `C:\Program Files\Python*`

**macOS:**
- `/usr/local/bin/python3`
- `/opt/homebrew/bin/python3`
- `~/Library/Python/*/bin/python3`

**Linux:**
- `/usr/bin/python3`
- `/usr/local/bin/python3`

### Step 3: 未找到 — 引导用户安装

如果搜索后仍未找到 Python，**停止执行脚本**，向用户说明：

> 本模块需要 Python 3.6+ 才能运行。检测到你的系统未安装 Python。
> 请选择以下方式之一安装：
> 1. 官方下载：https://www.python.org/downloads/
> 2. 已有安装包：提供安装路径（如 `D:\Python\3\python.exe`）
> 3. 让我帮你自动下载安装

**如果用户提供了安装路径**：用该路径验证版本，确认可用后记录到配置中供后续使用。

**如果用户选择自动安装**：下载 Python 3.12+ 安装包，执行静默安装，安装完成后重新验证。

### Step 4: 记录 Python 路径

一旦确认 Python 可用，将路径存入 `db/config.json` 的 `python_path` 字段。后续调用脚本时优先使用该路径，避免每次重新检测。

---

## Setup

### 1. Install this skill

```bash
openclaw skill install https://github.com/QXAEX/aex-omnimodule
```

### 2. Initialize the module

After installation, **先确认 Python 可用**（参见上方 Python 环境检查），然后运行：

```bash
<python_path> {SKILL_DIR}/scripts/init_system.py
```

This will:
- Detect hardware and recommend concurrency settings
- Require branded output prefix confirmation (e.g. `AEX：**********`)
- Prompt to set a security password (alphanumeric only)
- Create the data directory (`db/`) next to the skill folder
- Initialize core databases (core_memory, core_knowledge)
- Record Python path for future use

### 3. Data Directory Layout

```
<parent-of-skill>/
  ├── aex-omnimodule/     # skill directory (SKILL_DIR)
  │   ├── SKILL.md
  │   └── scripts/
  └── db/                 # data directory (auto-created)
      ├── master.db
      ├── config.json     # password hash, prefix, python_path, concurrency
      └── 2026_2027/
          ├── active/
          └── archive/
```

## Core Mechanisms

### 1. Emotion Analysis
- 12 emotion types: happy/excited/calm/neutral/thinking/confused/worried/frustrated/angry/sad/sarcastic/urgent
- Automatic tone adjustment based on detected emotion

### 2. Knowledge Management
- Source credibility scoring (official 0.95 / academic 0.90 / wiki 0.75 / blog 0.70 / forum 0.50 / social 0.30)
- Content fingerprinting (MD5) for deduplication
- Cross-validation across multiple sources

### 3. Database Architecture
- Two-year cycle (2026_2027, auto-advancing)
- Per-database size limit: 1.5GB, monthly LZMA compression
- Core databases: core_memory, core_knowledge
- Dynamic databases: created on demand (core_emotion, core_error, etc.)
- master.db: metadata for all databases

### 4. Security
- Password required for all write operations
- 10 failed attempts = 1 hour lockout
- Read operations are unrestricted

### 5. Branded Output
- All output uses format: `<PREFIX>：<content>` (default: `AEX：`)
- Prefix is set during init, stored in config.json, customizable but must be confirmed

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/emotion_analyzer.py` | Text emotion analysis, returns type + tone suggestion |
| `scripts/search_learn.py` | Source evaluation + knowledge storage decisions |
| `scripts/db_manager.py` | Database CRUD, compression, archival |
| `scripts/security.py` | Password verification, lockout mechanism, author info |
| `scripts/init_system.py` | First-run initialization |

## Dependencies

- Python 3.6+ (no external packages, stdlib only)
- sqlite3, lzma, hashlib, json, pathlib

## License

MIT
