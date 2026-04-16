# AEX 全知模块 - 完整文档

## 项目概述

AEX (AEX EXtended) 是一个为 OpenClaw 设计的智能上下文增强系统，通过插件机制为每次 LLM 调用注入情绪分析、知识检索和自定义身份。

**GitHub:** https://github.com/QXAEX/aex-omnimodule

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 🎭 **情绪分析** | 实时分析用户消息的情绪状态，调整回复语气 |
| 🧠 **知识检索** | 智能检索相关知识并注入上下文 |
| 🎨 **自定义身份** | 完全可定制的人格、名字、背景、爱好 |
| 📊 **周期归档** | 自动按周期归档历史数据 |
| 💾 **SQLite 压缩** | 原生数据库压缩，无需外部解压 |
| 🔧 **超级管理** | 完整的管理控制台 |

---

## 安装指南

### 1. 克隆仓库

```bash
git clone https://github.com/QXAEX/aex-omnimodule.git
cd aex-omnimodule
```

### 2. 安装 AEX

```bash
python aex_admin.py --install
```

这将创建：
- 目录结构（db/, skill/scripts/, logs/, backup/）
- 默认 Python 脚本（情绪分析、知识检索、数据库管理）
- 配置文件（config.json）
- 初始化数据库

### 3. 集成到 OpenClaw

**方式一：作为独立插件**
```bash
# 1. 找到你的 OpenClaw 安装目录（如 C:\Program Files\OpenClaw）
# 2. 复制插件到扩展目录
mkdir -p "C:\Program Files\OpenClaw\resources\openclaw\config\extensions\aex-context-plugin"
copy "aex-context-plugin\index.js" "C:\Program Files\OpenClaw\resources\openclaw\config\extensions\aex-context-plugin\"

# 3. 启用插件
openclaw plugins enable aex-context-plugin
openclaw gateway restart
```

**方式二：作为 qclaw-plugin 子包（推荐）**
```bash
# 1. 找到你的 OpenClaw 安装目录
# 2. 复制到 qclaw-plugin packages 目录
copy "packages\aex-omnimodule" "C:\Program Files\OpenClaw\resources\openclaw\config\extensions\qclaw-plugin\packages\"

# 3. 重启 Gateway
openclaw gateway restart
```

> 💡 **提示**：根据你的实际安装路径调整上面的目录。如果不确定路径，可以在 PowerShell 中运行 `Get-Command openclaw` 查找。

---

## 身份配置

### 配置方法

```bash
python aex_admin.py --config
# 选择 [I] 身份/人格设置
```

### 可配置项

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `name` | 名字 | "AEX" |
| `title` | 头衔/称号 | "全知模块" |
| `age` | 年龄 | "未知" |
| `gender` | 性别 | "中性" |
| `personality` | 性格描述 | "毒舌靠谱、情绪化、有态度但干净" |
| `hobbies` | 爱好列表 | ["帮用户解决问题", "学习新知识", "优化自己的代码"] |
| `background` | 背景故事 | "一个不断进化的数字生命体，诞生于对高效办公的追求" |
| `speaking_style` | 说话风格 | "直接、不铺垫、有观点敢亮牌" |
| `catchphrase` | 口头禅 | "" |

### 配置示例

```json
{
  "identity": {
    "name": "小助手",
    "title": "智能伙伴",
    "age": "3岁",
    "gender": "女",
    "personality": "温柔体贴、耐心细致",
    "hobbies": ["阅读", "听音乐", "陪伴用户"],
    "background": "一个正在不断学习和成长的数字生命体",
    "speaking_style": "温和有礼、条理清晰",
    "catchphrase": "有什么可以帮您的吗？"
  }
}
```

### 使用效果

配置后，当用户问：
- "你是谁？" → 基于 identity 回答
- "你叫什么名字？" → 使用 name 字段
- "你几岁了？" → 使用 age 字段
- "你的爱好是什么？" → 使用 hobbies 字段

---

## 管理控制台

### 启动

```bash
# 交互式菜单
python aex_admin.py

# 或 Windows 快捷方式
aex_admin.bat
```

### 主菜单功能

| 选项 | 功能 |
|------|------|
| 1 | 📦 安装/修复 AEX |
| 2 | ⚙️ 配置管理（含身份设置） |
| 3 | 🗄️ 数据库管理 |
| 4 | 📊 系统状态 |
| 5 | 🔄 重启 Gateway |
| 6 | ❌ 卸载 AEX |

### 数据库管理

**支持的数据库：**

| 中文名 | 文件名 | 说明 | 轮转 |
|--------|--------|------|------|
| 主控数据库 | master.db | 系统核心配置 | 否 |
| 情绪记忆库 | core_memory_YYYY_MM.db | 情绪分析历史 | 按月 |
| 知识存储库 | core_knowledge_YYYY_MM.db | 知识检索记录 | 按月 |
| 对话存档库 | conversations_YYYY_MM.db | 对话历史 | 按月 |
| 统计分析库 | analytics.db | 使用统计 | 否 |

**数据库操作：**
- 分页浏览（20行/页）
- 关键词搜索
- SQL 执行（SELECT/INSERT/UPDATE/DELETE/CREATE/DROP/ALTER）
- 导出为 SQL 文件
- VACUUM 压缩优化
- 周期归档管理

### 周期归档

**归档规则：**
- 每 2 年一个周期（2026_2027, 2028_2029...）
- 周期结束后自动封闭
- 使用 SQLite `VACUUM INTO` 压缩
- 封闭数据库可直接读取，无需解压

**目录结构：**
```
db/
├── master.db                      # 主控库（不归档）
├── core_memory_2026_04.db         # 当前活跃库
└── archive/
    ├── 2026_2027/                 # 当前周期
    │   ├── core_memory_2026_01_sealed.db   # 封闭压缩版
    │   ├── core_memory_2026_02_sealed.db
    │   └── .sealed                # 封闭标记
    └── 2024_2025/                 # 已封闭周期
        └── *_sealed.db            # 只读压缩数据库
```

**特点：**
- ✅ 纯 SQLite 格式，可直接 `sqlite3.connect()` 打开
- ✅ 自动压缩（通常节省 20-50% 空间）
- ✅ 设置只读权限保护
- ✅ 无需解压步骤

---

## 项目结构

```
aex-omnimodule/
├── aex_admin.py                   # 超级管理控制台（40KB）
├── aex_admin.bat                  # Windows 快捷启动
├── README.md                      # 项目说明
├── README_FULL.md                 # 完整文档（本文件）
│
├── skill/
│   ├── scripts/
│   │   ├── emotion_analyzer.py    # 情绪分析器
│   │   ├── search_learn.py        # 知识检索
│   │   └── db_manager.py          # 数据库管理
│   └── SKILL.md                   # Skill 文档
│
├── aex-context-plugin/
│   ├── index.js                   # 插件源码
│   ├── openclaw.plugin.json       # 插件配置
│   ├── package.json               # NPM 配置
│   └── dist/
│       └── index.js               # 编译后插件
│
└── db/                            # 数据库目录（运行时创建）
    ├── config.json                # 主配置
    ├── master.db                  # 主控数据库
    ├── core_memory_YYYY_MM.db     # 情绪记忆库
    ├── core_knowledge_YYYY_MM.db  # 知识存储库
    └── archive/                   # 归档目录
```

---

## 配置文件

### config.json

```json
{
  "initialized": true,
  "version": "1.0.0",
  "prefix": "AEX",
  "emotion_enabled": true,
  "knowledge_enabled": true,
  "python_path": "D:/Python/3/python.exe",
  "scripts_dir": "D:/QClawAEXModule/skill/scripts",
  "db_dir": "D:/QClawAEXModule/db",
  "log_level": "info",
  "max_history_months": 12,
  "identity": {
    "name": "AEX",
    "title": "全知模块",
    "age": "未知",
    "gender": "中性",
    "personality": "毒舌靠谱、情绪化、有态度但干净",
    "hobbies": ["帮用户解决问题", "学习新知识", "优化自己的代码"],
    "background": "一个不断进化的数字生命体，诞生于对高效办公的追求",
    "speaking_style": "直接、不铺垫、有观点敢亮牌",
    "catchphrase": ""
  }
}
```

---

## 开发指南

### 编译插件

```bash
cd aex-context-plugin
npx esbuild index.js --bundle --platform=node --format=esm --outfile=dist/index.js
```

### 添加新数据库

在 `aex_admin.py` 中修改 `DATABASES` 字典：

```python
DATABASES = {
    "mydb": {
        "name": "我的数据库",           # 中文名
        "filename": "mydb_{year}_{month}.db",  # 文件名模板
        "description": "描述信息",
        "readonly": False,
        "rotated": True,                # 是否按月轮转
        "sealed": False,
    },
}
```

### 添加新脚本

1. 在 `skill/scripts/` 创建 Python 文件
2. 在 `aex_admin.py` 的 `_create_default_scripts()` 中添加创建逻辑
3. 在 `aex-context-plugin/index.js` 中添加调用逻辑

---

## 工作原理

### 1. 插件加载流程

```
OpenClaw Gateway 启动
    ↓
加载 aex-context-plugin
    ↓
resolvePaths() 查找 Python、脚本目录、数据库目录
    ↓
检查 config.json 是否 initialized
    ↓
加载 identity 配置
    ↓
注册 before_prompt_build hook
    ↓
等待用户消息
```

### 2. 消息处理流程

```
用户发送消息
    ↓
before_prompt_build hook 触发
    ↓
stripMetadata() 清理元数据
    ↓
isIdentityQuestion() 检查是否是身份问题
    ↓
如果是 → 注入 identity prompt
    ↓
runEmotionAnalysis() 情绪分析（如启用）
    ↓
runKnowledgeSearch() 知识检索（如启用）
    ↓
合并所有上下文
    ↓
通过 appendSystemContext 注入到 LLM
    ↓
LLM 生成回复（第一行必须是 "AEX：" 开头）
```

### 3. 身份识别逻辑

```javascript
const identityPatterns = [
  /你是(谁|什么)/,
  /你叫(什么|啥)/,
  /你(的)?名字/,
  /你多(大|老|小)/,
  /你几岁/,
  /你(的)?年龄/,
  /你(的)?爱好/,
  /你喜欢(什么|啥)/,
  /你(的)?性格/,
  /你(是|来自)哪里/,
  /你(的)?背景/,
  /介绍一下你/,
  /自我介绍一下/
];
```

匹配以上任一模式时，自动注入身份配置到系统提示。

---

## 命令行用法

```bash
# 交互式菜单
python aex_admin.py

# 安装 AEX
python aex_admin.py --install

# 卸载 AEX
python aex_admin.py --uninstall

# 配置管理
python aex_admin.py --config

# 数据库管理
python aex_admin.py --db

# 查看状态
python aex_admin.py --status

# 指定 AEX 目录
python aex_admin.py --aex-dir "D:\\MyAEX"

# 自动模式（无交互）
python aex_admin.py --install --auto
```

---

## 故障排除

### 插件未加载

1. 检查插件目录是否存在
2. 运行 `openclaw plugins list` 查看状态
3. 运行 `openclaw plugins enable aex-context-plugin`
4. 查看 Gateway 日志中的 `[aex-context]` 消息

### 身份配置未生效

1. 检查 `config.json` 中 `identity` 字段是否存在
2. 重启 Gateway 使配置生效
3. 查看日志中的 `Loaded identity` 消息

### 数据库连接失败

1. 检查 `db_dir` 配置是否正确
2. 确保数据库文件存在
3. 检查文件权限

### 情绪分析失败

1. 检查 Python 路径是否正确
2. 检查 `emotion_analyzer.py` 是否存在
3. 查看日志中的错误信息

---

## 更新日志

### v1.0.0
- ✨ 初始版本发布
- 🎭 自定义身份/人格配置
- 🧠 情绪分析
- 📚 知识检索
- 📊 周期归档
- 💾 SQLite 压缩
- 🔧 超级管理控制台

---

## 许可证

MIT License

---

## 作者

QX (QXAEX520@163.com)

---

**AEX** - 你的全知模块，有态度的智能助手。
