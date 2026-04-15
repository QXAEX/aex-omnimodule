# AEX 全知模块 (AEX Omnimodule)

> 自我进化型 AI 助手系统 — 每次对话都在感知、学习、进化。

## ✨ 特性

- 🧠 **知识管理** — 自动搜索学习、深度验证、本地存储、月度压缩
- 💭 **情感感知** — 文字情绪分析、语气自适应调整
- 🧩 **结构化思维** — 多角度分析、质疑反驳、逻辑推理
- 🔒 **安全机制** — 密码验证、错误锁定、权限分级
- 📦 **零依赖** — 纯 Python 标准库（sqlite3、json、hashlib、lzma）

## 📦 包含组件

| 组件 | 说明 |
|------|------|
| `skill/` | AEX 核心技能（SKILL.md + Python 脚本） |
| `aex-context-plugin/` | OpenClaw Gateway 插件（自动注入情绪/知识分析） |
| `db/` | 数据库目录（config.example.json 模板） |

## 🚀 快速开始

### 前置条件

- Python 3.8+
- [OpenClaw](https://github.com/openclaw)（用于插件功能）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/QXAEX/aex-omnimodule.git

# 2. 初始化数据库
python skill/scripts/init_system.py

# 3. 安装 OpenClaw 插件
# 将 aex-context-plugin/ 复制到你的 OpenClaw extensions 目录
cp -r aex-context-plugin/ <openclaw-config>/extensions/
openclaw plugins enable aex-context-plugin
openclaw gateway restart
```

### 4. 配置技能路径

将 `skill/` 目录注册到你的 OpenClaw skills 配置中，确保 SKILL.md 被正确发现。

## 📐 架构

```
用户消息 → OpenClaw Gateway
              ↓
        aex-context-plugin (before_prompt_build hook)
              ↓
        ┌─────────────────────┐
        │ emotion_analyzer.py  │ → 情绪分析
        │ search_learn.py      │ → 知识检索
        └─────────────────────┘
              ↓
        注入 <aex-emotion> + <aex-knowledge> 到系统提示
              ↓
        LLM 根据分析结果调整回复
```

## ⚙️ 可配置项

在 `db/config.json` 中：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `prefix` | `"AEX"` | 分析结果输出前缀 |
| `max_db_size_gb` | `1.5` | 单库上限 (GB) |
| `max_attempts` | `10` | 密码错误锁定次数 |
| `lockout_seconds` | `3600` | 锁定时长 (秒) |
| `compression` | `"lzma"` | 压缩算法 |

## 🔐 安全

- 所有写操作需要密码验证（SHA-256 哈希）
- 密码错误 10 次后锁定 1 小时
- 数据库写入经过可信度评分

## 📁 目录结构

详见 [STRUCTURE.md](STRUCTURE.md)

## 📄 License

MIT

## 👤 Author

**QX** — QXAEX520@163.com
