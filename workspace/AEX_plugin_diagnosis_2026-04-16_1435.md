# AEX 插件诊断与调试

## 诊断步骤执行情况

### ✅ 方案 A：检查插件配置（已完成）
- **配置文件**: `D:\QClawAEXModule\db\config.json`
  - `prefix: "AEX"` ✓
  - `python_path: "D:\\Python\\3\\python.exe"` ✓
  - `initialized: true` ✓
  - 缺少 `emotion_enabled` 和 `knowledge_enabled` 字段（插件从 config 读取）
- **插件配置**: `plugins.entries.aex-context-plugin`
  - `enabled: true` ✓
  - `emotionAnalysis: true` ✓
  - `knowledgeSearch: true` ✓
  - 已添加 `logLevel: "debug"`（通过 config.patch）

### ✅ 方案 B：启用调试日志（已完成）
- **配置更新**: `config.patch` 添加 `logLevel: "debug"`
- **网关重启**: 已触发（SIGUSR1）
- **预期效果**: 插件将输出详细日志，包括：
  - 情绪分析调用结果
  - 知识检索调用结果
  - 上下文注入详情

### 🔄 方案 C：手动测试插件脚本（部分完成）
- **情绪分析脚本**: `emotion_analyzer.py`
  ```bash
  python emotion_analyzer.py "今天天气怎么样"
  ```
  - **结果**: 输出乱码（编码问题），但脚本能运行
  - **问题**: 脚本可能返回示例数据而非真实分析

- **知识检索脚本**: `search_learn.py`
  ```bash
  python search_learn.py "今天天气怎么样"
  ```
  - **结果**: `[]`（空数组，无相关知识，正常）

- **存储功能测试**: ✅ 通过
  ```bash
  python search_learn.py --conversation "Flutter框架" "..." "webchat" 0.3
  ```
  - **结果**: `storage_status: "stored"`, `entry_id: 5`

## 插件集成状态分析

### 1. 插件加载确认
```
[plugins] [aex-context] Python found: D:\Python\3\python.exe → Python 3.12.4
[plugins] [aex-context] Scripts dir: D:\QClawAEXModule\skill\scripts
[plugins] [aex-context] DB dir: D:\QClawAEXModule\db
[plugins] [aex-context] Registered. Python=..., Scripts=..., DB=..., emotion=true, knowledge=true
[plugins] [aex-context] Plugin ready
```

### 2. qclaw-plugin 子包加载确认
```
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] 初始化中...
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] 配置加载完成: prefix=AEX, emotion=true, knowledge=true
[qclaw-plugin:hook-proxy] registering api.on('before_prompt_build') for package aex-omnimodule
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] before_prompt_build handler 已注册 (priority=0)
[qclaw-plugin:hook-proxy] registering api.on('llm_output') for package aex-omnimodule
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] after_completion handler 已注册
```

### 3. 优先级冲突分析
- **aex-context-plugin**: 独立插件，注册 `before_prompt_build`（优先级未知）
- **aex-omnimodule**: qclaw-plugin 子包，注册 `before_prompt_build`（priority=0）
- **潜在问题**: 两个插件可能都注入内容，导致冲突或重复

## 核心问题：AEX 前缀缺失

### 观察现象
- 用户消息："今天天气怎么样"
- AI 回复：正常天气回答，**无** `AEX：` 前缀
- 预期行为：回复第一行应为 `AEX：情绪=[emotion] 强度=[intensity] 建议=[tone]`

### 可能原因
1. **插件未注入**：钩子未执行或执行失败
2. **模型忽略格式**：DeepSeek 模型可能忽略系统提示中的格式要求
3. **优先级冲突**：其他插件覆盖了 AEX 的注入
4. **脚本执行失败**：情绪分析脚本返回空或错误

### 调试计划
1. **等待网关重启完成**（当前进行中）
2. **发送测试消息**，观察调试日志输出
3. **检查插件日志**，确认钩子执行和脚本调用
4. **验证系统提示**，查看实际注入内容

## 数据库架构验证

### 当前结构
```
D:\QClawAEXModule\db\
├── config.json
├── Flutter.db          # 主题知识库（根目录）
├── Python.db
├── AI.db
├── 2026_2027/
│   ├── general.db      # 通用知识库（已存储测试条目 id=5）
│   ├── active/
│   └── archive/
└── archive/
```

### 索引状态
- **general.db**: 完整索引集（created_at, weight, credibility, source, tags）
- **主题数据库**: 新建时自动创建相同索引
- **查询优化**: EXPLAIN QUERY PLAN 确认使用索引

## 待验证功能

### 1. 情绪分析注入
- 触发条件：任何用户消息
- 预期输出：`AEX：情绪检测 — happy (30%)，建议语气：轻松自然`
- 验证方法：发送测试消息，观察回复前缀

### 2. 知识检索注入
- 触发条件：对话涉及已知主题
- 预期输出：`AEX：知识检索 — 找到 3 条相关记忆`
- 验证方法：发送技术问题，观察是否引用历史知识

### 3. 自动学习存储
- 触发条件：对话完成（llm_output 钩子）
- 预期行为：调用 `search_learn.py --conversation`
- 验证方法：发送技术对话，检查数据库新条目

### 4. 主题检测
- 当前状态：所有知识存储到 `general.db`
- 目标状态：自动检测主题，存储到对应数据库
- 实现状态：待开发

## 下一步行动

### 立即执行
1. **确认网关重启完成**
2. **发送测试消息**，观察调试日志
3. **分析日志**，定位注入失败原因

### 备选方案
- **禁用 aex-context-plugin**，只使用 qclaw-plugin 子包
- **修改插件代码**，强制模型输出前缀
- **调整提示工程**，使用更严格的格式指令

### 长期改进
- 修复情绪分析脚本编码问题
- 实现主题检测逻辑
- 优化存储阈值和评分算法