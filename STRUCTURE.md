# AEX全知模块 - 目录结构详解

## 根目录

```
D:\QClawAEXModule\
├── README.md              # 全局说明文档
├── STRUCTURE.md           # 本文件
│
├── skill\                 # 技能本体
│   ├── SKILL.md
│   ├── scripts\
│   ├── references\
│   └── assets\
│
└── db\                    # 所有数据（记忆、配置、数据库）
    ├── config.json        # 全局配置（密码哈希、并发数、硬件信息）
    ├── DESIGN_DOC.txt     # 设计文档（对话记录）
    ├── master.db          # 元数据库（记录所有库的位置和状态）
    │
    ├── 2026_2027\         # 当前周期（可读写）
    │   ├── active\        # 当月活跃数据库
    │   │   ├── core_memory_2026_04.db      # 对话记忆
    │   │   ├── core_knowledge_2026_04.db   # 知识库
    │   │   └── [动态新增...]               # 新类别按需创建
    │   └── archive\      # 已压缩历史月（只读）
    │       ├── core_memory_2026_03.pack
    │       ├── core_knowledge_2026_03.pack
    │       └── ...
    │
    └── 2024_2025\         # 已封闭周期（只读）
        └── sealed_2024_2025.pack
```

## 命名规则

- 文件夹: 小写字母、数字、下划线
- 日期: YYYY_MM 格式
- 周期: YYYY_YYYY 格式
- 数据库: [类别]_YYYY_MM.db
- 压缩包: [类别]_YYYY_MM.pack
- 封闭包: sealed_YYYY_YYYY.pack
- 核心库前缀: core_

## 文件类型说明

| 扩展名 | 类型 | 说明 |
|--------|------|------|
| .db    | 活跃库 | 可读写，当月数据 |
| .pack  | 压缩包 | lzma压缩，只读 |
| .json  | 配置 | 全局配置 |
| .md    | 文档 | 说明文档 |
| .txt   | 文档 | 设计记录 |

## 数据库容量

- 单库上限: 1.5GB
- 写入前深度处理，只存精品
- 允许重复记忆，月度压缩时权重去重

## 周期规则

- 每两年一个周期文件夹
- 2026-2027 存放在 2026_2027\
- 2028年1月自动封闭 2026_2027 为 sealed_2026_2027.pack
- 封闭后只读，解压需密码

## 动态数据库

除了核心库（core_memory, core_knowledge）外，
当检测到新的数据类别需要存储时，会询问用户确认后创建新库。

示例动态库:
- core_emotion    # 情感模式分析
- core_error      # 错误教训记录
- core_code       # 代码学习记录
- core_decision   # 决策记录

## master.db 内容

| 表 | 说明 |
|----|------|
| databases | 所有数据库的元信息（类型、路径、大小、状态） |
| config_history | 配置变更历史 |
| operations_log | 操作日志 |

## config.json 内容

| 字段 | 说明 |
|------|------|
| password_hash | 密码SHA256哈希 |
| failed_attempts | 密码错误次数 |
| locked_until | 锁定截止时间 |
| current_period | 当前周期 |
| max_db_size_gb | 单库上限(GB) |
| max_attempts | 最大密码错误次数 |
| concurrency | 并发数据库数 |
| compression | 压缩算法 |
| hardware | 硬件配置快照 |
| version | 版本号 |
