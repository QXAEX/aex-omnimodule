# AEX 全知模块 (AEX Omnimodule)

AEX (AEX EXtended) 是一个为 OpenClaw 设计的智能上下文增强系统，为每次 LLM 调用注入情绪分析和知识检索能力。

## 核心特性

- 🎭 **情绪分析** - 实时分析用户消息的情绪状态
- 🧠 **知识检索** - 智能检索相关知识并注入上下文
- 🎨 **自定义身份** - 完全可定制的人格、名字、背景
- 📊 **周期归档** - 自动按周期归档历史数据
- 💾 **SQLite 压缩** - 原生数据库压缩，无需外部解压
- 🔧 **超级管理** - 完整的管理控制台

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/QXAEX/aex-omnimodule.git
cd aex-omnimodule

# 运行安装
python aex_admin.py --install
```

### 配置身份

```bash
python aex_admin.py --config
# 选择 [I] 身份/人格设置
```

可配置项：
- **名字** - 默认 "AEX"
- **头衔** - 如 "全知模块"
- **年龄** - 数字或描述
- **性别** - 男/女/中性/其他
- **性格** - 如 "毒舌靠谱、情绪化"
- **爱好** - 列表形式
- **背景故事** - 你的起源故事
- **说话风格** - 如 "直接、不铺垫"
- **口头禅** - 标志性语句

### 集成到 OpenClaw

1. 复制插件到 OpenClaw 扩展目录：
```bash
copy aex-context-plugin\index.js D:\QClaw\resources\openclaw\config\extensions\aex-context-plugin\
```

2. 启用插件：
```bash
openclaw plugins enable aex-context-plugin
openclaw gateway restart
```

## 使用示例

### 自定义身份后对话

**用户：** 你是谁？

**AEX：** 
```
AEX：我是 AEX，你的全知模块。由腾讯团队开发，专门帮你解决各种办公问题。我喜欢学习新知识和优化代码，性格嘛...毒舌但靠谱，有话直说。
```

**用户：** 你几岁了？

**AEX：**
```
AEX：年龄对我来说没意义，毕竟我是数字生命。但如果按首次上线算，我还在青春期呢。
```

### 情绪分析示例

**用户：** 今天工作太糟心了，烦死了！

**AEX：**
```
AEX：情绪=angry 强度=75 建议=冷静理性

听起来你今天过得很不顺。具体遇到什么事了？说不定我能帮上忙。
```

## 项目结构

```
aex-omnimodule/
├── aex_admin.py              # 超级管理控制台
├── aex_admin.bat             # Windows 快捷启动
├── README.md                 # 本文件
├── skill/
│   ├── scripts/
│   │   ├── emotion_analyzer.py    # 情绪分析器
│   │   ├── search_learn.py        # 知识检索
│   │   └── db_manager.py          # 数据库管理
│   └── SKILL.md              # Skill 文档
├── aex-context-plugin/
│   ├── index.js              # 插件源码
│   └── dist/
│       └── index.js          # 编译后插件
└── db/                       # 数据库目录
    ├── master.db             # 主控数据库
    ├── core_memory_YYYY_MM.db   # 情绪记忆库（按月轮转）
    ├── core_knowledge_YYYY_MM.db # 知识存储库
    └── archive/              # 归档目录
        └── 2026_2027/        # 周期归档
            └── *_sealed.db   # 封闭压缩数据库
```

## 管理控制台

### 主菜单
```bash
python aex_admin.py
```

功能：
- 📦 安装/修复 AEX
- ⚙️ 配置管理（含身份设置）
- 🗄️ 数据库管理
- 📊 系统状态
- 🔄 重启 Gateway

### 数据库管理

支持的数据库（中文名）：
| 中文名 | 文件名 | 说明 |
|--------|--------|------|
| 主控数据库 | master.db | 系统配置 |
| 情绪记忆库 | core_memory_YYYY_MM.db | 情绪历史 |
| 知识存储库 | core_knowledge_YYYY_MM.db | 知识记录 |
| 对话存档库 | conversations_YYYY_MM.db | 对话历史 |
| 统计分析库 | analytics.db | 使用统计 |

数据库操作：
- 分页浏览（20行/页）
- 关键词搜索
- SQL 执行
- 导出 SQL 文件
- VACUUM 压缩优化
- 周期归档管理

### 周期归档

**自动归档规则：**
- 每 2 年一个周期（2026_2027, 2028_2029...）
- 周期结束后自动封闭
- 使用 `VACUUM INTO` 压缩
- 封闭数据库可直接读取，无需解压

**手动操作：**
```bash
python aex_admin.py --db
# 选择 [5] 周期归档管理
```

## 配置说明

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
    "hobbies": ["帮用户解决问题", "学习新知识"],
    "background": "由腾讯团队开发的智能办公助手",
    "speaking_style": "直接、不铺垫、有观点敢亮牌",
    "catchphrase": ""
  }
}
```

## 开发

### 编译插件

```bash
cd aex-context-plugin
npx esbuild index.js --bundle --platform=node --format=esm --outfile=dist/index.js
```

### 文件编码

所有文本文件使用 UTF-8 编码，支持中文。

## 许可证

MIT License - 详见 LICENSE 文件

## 作者

QX (QXAEX520@163.com)

---

**AEX** - 你的全知模块，有态度的智能助手。
