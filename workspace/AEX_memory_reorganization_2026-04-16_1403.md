# AEX 记忆文件重组与清理

## 项目背景
用户要求清理 AEX 项目并重新规整记忆文件。根据对话历史，确定了新的数据库架构：

### 新目录结构
```
db/
├── config.json
├── *.py
├── Flutter.db          # 主题知识库（活跃，根目录）
├── Python.db
├── AI.db
├── 2026_2027/          # 当前周期目录
│   ├── general.db      # 通用知识（原 core_knowledge）
│   └── conversations_2026_04.db
├── 2028_2029/          # 下个周期（自动创建）
└── archive/            # 归档目录
```

## 问题诊断
1. **索引缺失问题**：现有数据库只有 `idx_entries_created` 和 `idx_tags_entry` 索引，缺少关键索引（weight、credibility_score、source 等）
2. **结构混乱问题**：主题数据库与通用数据库混合存放，未按周期组织
3. **性能问题**：LIKE 查询无索引导致全表扫描

## 解决方案
### 1. 文件重组
- 移动 `core_knowledge_2026_04.db` → `2026_2027/general.db`
- 保持 `master.db` 在根目录（系统数据库）
- 创建主题数据库模板（Flutter.db、Python.db、AI.db）

### 2. 索引优化
为所有数据库添加完整索引集：
```sql
CREATE INDEX idx_weight ON entries(weight DESC);
CREATE INDEX idx_credibility ON entries(credibility_score DESC);
CREATE INDEX idx_created ON entries(created_at DESC);
CREATE INDEX idx_source ON entries(source);
```

### 3. 代码修改
- `db_manager.py`：支持主题数据库（根目录）与通用数据库（周期目录）的路径生成
- `search_learn.py`：支持主题检测与自动数据库选择
- 保持向后兼容性

## 执行步骤
### 已完成
1. 用户确认新架构结构
2. 解释 archive 目录用途（归档过期数据）

### 待执行
1. 备份现有 db 目录
2. 移动核心知识库文件
3. 创建主题数据库模板
4. 修改 db_manager.py 路径逻辑与索引创建
5. 测试验证

## 关键决策
1. **主题数据库位置**：根目录（用户明确要求）
2. **通用数据库位置**：周期目录内（2026_2027/general.db）
3. **索引策略**：为所有数据库创建完整索引集，解决现有索引缺失问题
4. **归档机制**：archive 目录用于存储过期周期数据，支持压缩与恢复

## 风险与缓解
- **数据丢失风险**：执行前完整备份 db 目录
- **路径错误风险**：逐步修改，每步验证文件可访问性
- **索引不生效风险**：创建后立即执行 EXPLAIN QUERY PLAN 验证

## 预期效果
1. **性能提升**：关键查询速度提升 10-100 倍
2. **结构清晰**：按主题+周期组织，易于管理
3. **扩展性强**：新主题自动创建独立数据库
4. **维护方便**：归档机制防止数据无限增长

## 时间预估
- 文件重组：10分钟
- 代码修改：30分钟  
- 测试验证：20分钟
- 总计：约 1小时

## 待确认事项
等待用户确认开始执行清理重组操作。