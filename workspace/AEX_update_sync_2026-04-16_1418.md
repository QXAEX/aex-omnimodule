# AEX 更新同步与网关重启

## 执行步骤
### 1. 同步脚本到 QClaw 技能目录
- 复制 `db_manager.py` 到 `D:\QClaw\resources\openclaw\config\skills\aex-omnimodule\scripts\`
- 复制 `search_learn.py` 到相同目录
- 复制 `knowledge_weight_analyzer.py` 到相同目录

### 2. 修复 TypeScript 构建依赖
- 安装 `@types/archiver` 解决 archiver 模块类型声明缺失问题
- 其他构建错误（content-plugin、pcmgr-ai-security）暂未修复，但不影响 aex-omnimodule 功能

### 3. 单独编译 aex-omnimodule 包
```bash
npx tsc packages/aex-omnimodule/index.ts --outDir packages/aex-omnimodule/dist --module commonjs --target es2020 --esModuleInterop
```
- 成功生成 `dist/packages/aex-omnimodule/index.js`（7.7KB）

### 4. 重启网关
- 发送 SIGUSR1 信号重启 OpenClaw 网关
- 延迟 2 秒，等待插件重新加载

## 验证结果
### 存储功能测试（技能目录）
```bash
python search_learn.py --store "技能目录测试" "test"
# 输出: {"status": "stored", "id": 4}
```
- 成功存储到 `2026_2027/general.db`（core_knowledge 映射）

### 路径生成验证
```python
# 测试脚本输出
Flutter.db          → 根目录（存在✅）
Python.db           → 根目录（存在✅）
AI.db               → 根目录（存在✅）
general.db          → 2026_2027/（存在✅）
conversations_2026_04.db → 2026_2027/（未创建，正常）
```

## 当前架构状态
### 数据库结构
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
- **general.db**：已添加完整索引集（weight、credibility、source、created_at、tags）
- **主题数据库**：新建时自动包含完整索引
- **master.db**：无 entries 表，无需索引

## 待解决问题
### 1. TypeScript 构建错误
- `content-plugin/src/cos-client.ts`：Buffer 类型不匹配
- `content-plugin/src/interceptor.ts`：可能为 null 的变量
- `pcmgr-ai-security/index.ts`：回调函数返回类型不匹配
- **影响**：整体构建失败，但 aex-omnimodule 已单独编译成功

### 2. 主题检测逻辑未实现
- search_learn.py 尚未集成主题关键词提取
- 所有知识仍存储到 general.db，未按主题分流

### 3. 插件钩子集成验证
- llm_output 钩子是否成功注册
- 情绪分析和知识检索是否在对话中注入
- 自动学习存储是否触发

## 后续测试计划
### 立即测试
1. 确认插件加载状态（`openclaw plugins list`）
2. 发送测试消息验证 AEX 插件输出格式
3. 检查对话后是否自动触发学习存储

### 功能完善
1. 实现主题关键词提取（search_learn.py）
2. 添加跨主题联合搜索（db_manager.py）
3. 优化归档触发条件（文件大小 + 周期结束）

## 风险与缓解
- **插件加载失败**：检查网关日志，重新编译 aex-omnimodule
- **路径不一致**：确保所有脚本使用相同的 db_manager.py 版本
- **索引不生效**：使用 EXPLAIN QUERY PLAN 验证查询计划