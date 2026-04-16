# AEX 插件加载与测试准备

## 插件加载状态
### 1. AEX Context Plugin (独立插件)
- **状态**: loaded
- **Python**: D:\Python\3\python.exe (3.12.4)
- **脚本目录**: D:\QClawAEXModule\skill\scripts
- **数据库目录**: D:\QClawAEXModule\db
- **功能**: emotion=true, knowledge=true
- **注册时间**: 网关重启后自动加载

### 2. qclaw-plugin (aex-omnimodule 子包)
- **状态**: initialized
- **钩子注册**:
  - `before_prompt_build` (priority=0) - 情绪分析与知识检索注入
  - `llm_output` - 对话后学习存储触发
- **配置**: prefix=AEX, emotion=true, knowledge=true
- **初始化时间**: 11.8ms

## 数据库架构验证
### 当前结构
```
D:\QClawAEXModule\db\
├── config.json
├── *.py
├── Flutter.db          # 主题知识库（完整索引）
├── Python.db
├── AI.db
├── 2026_2027/
│   ├── general.db      # 通用知识库（完整索引）
│   ├── active/
│   └── archive/
├── archive/
└── master.db
```

### 索引状态
- **general.db**: idx_entries_created, idx_entries_weight, idx_entries_credibility, idx_entries_source, idx_tags_entry
- **主题数据库**: 新建时自动包含完整索引集
- **查询优化**: EXPLAIN QUERY PLAN 显示使用 weight 索引

## 功能测试结果
### 存储功能 ✅
```bash
# 工程目录
python search_learn.py --store "测试存储功能" "test"
# 输出: {"status": "stored", "id": 3}

# 技能目录  
python search_learn.py --store "技能目录测试" "test"
# 输出: {"status": "stored", "id": 4}
```

### 路径生成 ✅
```python
# 测试脚本输出
Flutter.db → 根目录（存在）
Python.db → 根目录（存在）
AI.db → 根目录（存在）
general.db → 2026_2027/（存在）
conversations_2026_04.db → 2026_2027/（未创建）
```

### 对话处理 ✅
```bash
python search_learn.py --conversation "Python列表推导式" "..." "test" 0.6
# 输出: {"storage_status": "not_stored", "weight_score": 0.295}
# 权重低于阈值，未存储（符合预期）
```

## 插件集成关键日志
```
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] 初始化中...
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] 配置加载完成
[qclaw-plugin:hook-proxy] registering api.on('before_prompt_build') for package aex-omnimodule
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] before_prompt_build handler 已注册 (priority=0)
[qclaw-plugin:hook-proxy] registering api.on('llm_output') for package aex-omnimodule
[qclaw-plugin:aex-omnimodule] [aex-omnimodule] after_completion handler 已注册
```

## 优先级顺序
1. **AEX (0)** - 情绪分析 + 知识检索
2. **error-response-handler (50)** - 错误响应处理
3. **qmemory (100)** - 记忆管理
4. **content-plugin (200)** - 内容插件
5. **pcmgr-ai-security (250)** - 安全审计
6. **prompt-optimizer (900)** - 提示优化

## 待测试功能
### 1. 情绪分析注入
- 用户消息 → 情绪分析 → 系统提示注入 `AEX：情绪检测 — ...`
- 验证回复是否包含 AEX 前缀

### 2. 知识检索注入
- 对话涉及已知主题 → 检索相关记忆 → 注入系统提示
- 验证回复是否引用历史知识

### 3. 自动学习存储
- 对话完成 → llm_output 钩子 → 调用 search_learn.py
- 权重评估 → 存储到相应数据库
- 验证 general.db 或主题数据库是否有新条目

### 4. 主题检测
- 对话包含"Flutter" → 建议存储到 Flutter.db
- 当前逻辑：所有知识仍存储到 general.db（待实现）

## 网络状态
- **VPN 已开启**：解决之前远程获取 HTTP 403 错误
- **插件远程获取**：应恢复正常（error-response-handler 等）

## 后续步骤
### 立即测试
1. 发送测试消息验证情绪分析注入
2. 发送技术对话验证学习存储
3. 检查数据库更新情况

### 功能完善
1. 实现主题关键词提取（search_learn.py）
2. 添加跨主题联合搜索（db_manager.py）
3. 优化归档触发条件（文件大小 + 周期结束）

## 风险点
- **钩子执行顺序**：AEX priority=0 确保最先执行，但可能被其他插件覆盖
- **存储阈值**：默认 0.7，可能过高导致学习存储较少
- **主题检测延迟**：当前未实现，所有知识存到 general.db