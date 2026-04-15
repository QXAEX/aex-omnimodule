# AEX 全知模块 - 外部支持安装指南

AEX (AEX Omnimodule) 是 QClaw 的外部支持系统，提供情绪分析和知识检索能力。

## 架构说明

AEX 现在以 **qclaw-plugin 子 package** 的形式运行，拥有最高优先级控制权：

```
┌─────────────────────────────────────────┐
│           qclaw-plugin                  │
│  ┌─────────────────────────────────┐    │
│  │   aex-omnimodule (priority=0)   │ ← 最先执行，可 block 其他
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   error-response-handler        │    │
│  │   cron-delivery-guard           │    │
│  │   prompt-optimizer (priority=900)│   │
│  │   ...                           │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 安装方式

### 方式一：一键安装（推荐）

```bash
# 下载安装脚本
curl -o install_aex.py https://raw.githubusercontent.com/QXAEX/aex-omnimodule/main/install_aex.py

# 运行安装
python install_aex.py
```

### 方式二：qclaw-plugin 集成安装

如果你已经安装了 qclaw-plugin，使用专用安装器：

```bash
# 下载安装脚本
curl -o install_aex_qclaw.py https://raw.githubusercontent.com/QXAEX/aex-omnimodule/main/install_aex_qclaw.py

# 运行安装
python install_aex_qclaw.py
```

这个安装器会：
1. 创建 `qclaw-plugin/packages/aex-omnimodule/index.ts`
2. 更新 `qclaw-plugin/index.ts` 添加 import 和 PACKAGES 引用
3. 编译 TypeScript
4. 重启 Gateway

### 方式三：手动安装

#### 1. 准备 AEX 源码

```bash
# 克隆仓库
git clone https://github.com/QXAEX/aex-omnimodule.git D:/QClawAEXModule

# 或者下载 ZIP 解压到 D:/QClawAEXModule
```

#### 2. 创建目录结构

```
D:/QClawAEXModule/
├── db/
│   └── config.json          # 配置文件
├── skill/
│   └── scripts/
│       ├── emotion_analyzer.py
│       ├── search_learn.py
│       └── db_manager.py
└── ...
```

#### 3. 创建配置文件

创建 `D:/QClawAEXModule/db/config.json`：

```json
{
  "initialized": true,
  "version": "1.0.0",
  "prefix": "AEX",
  "emotion_enabled": true,
  "knowledge_enabled": true,
  "python_path": "D:/Python/3/python.exe",
  "scripts_dir": "D:/QClawAEXModule/skill/scripts",
  "db_dir": "D:/QClawAEXModule/db"
}
```

#### 4. 安装为 qclaw-plugin 子 package

复制 `aex-context-plugin/index.ts` 到：

```
D:/QClaw/resources/openclaw/config/extensions/qclaw-plugin/packages/aex-omnimodule/index.ts
```

#### 5. 修改 qclaw-plugin/index.ts

添加 import：

```typescript
// 在文件顶部的 import 部分添加
import aexOmnimodule from './packages/aex-omnimodule/index.js'
```

添加到 PACKAGES 数组（**必须放在第一个位置**）：

```typescript
const PACKAGES: QClawPackage[] = [
  aexOmnimodule,  // AEX 全知模块，priority=0 确保最先执行
  errorResponseHandler,
  cronDeliveryGuard,
  // ... 其他 packages
]
```

#### 6. 编译并重启

```bash
cd D:/QClaw/resources/openclaw/config/extensions/qclaw-plugin
npm run build
openclaw gateway restart
```

## 验证安装

查看 Gateway 日志：

```bash
openclaw gateway logs -f
```

应该看到：

```
[qclaw-plugin:aex-omnimodule] 初始化中...
[qclaw-plugin:aex-omnimodule] 配置加载完成: prefix=AEX, emotion=true, knowledge=true
[qclaw-plugin:hook-proxy] registering api.on('before_prompt_build') for package aex-omnimodule
[qclaw-plugin:aex-omnimodule] before_prompt_build handler 已注册 (priority=0)
```

## 卸载

```bash
# 使用安装脚本卸载
python install_aex_qclaw.py --uninstall

# 或手动删除
rm -rf D:/QClaw/resources/openclaw/config/extensions/qclaw-plugin/packages/aex-omnimodule
# 然后从 qclaw-plugin/index.ts 中移除 import 和引用
```

## 配置说明

编辑 `D:/QClawAEXModule/db/config.json`：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `prefix` | 回复前缀 | `AEX` |
| `emotion_enabled` | 启用情绪分析 | `true` |
| `knowledge_enabled` | 启用知识检索 | `true` |

## 高级特性

### Block 能力

AEX 可以阻止后续 handler 执行：

```typescript
return {
  block: true,
  blockReason: "AEX 已处理",
  appendSystemContext: "..."
}
```

### 优先级系统

- AEX: `priority=0`（最高）
- error-response-handler: `priority=50`
- qmemory: `priority=100`
- content-plugin: `priority=200`
- prompt-optimizer: `priority=900`（最低）

数字越小优先级越高，AEX 总是最先执行。

## 故障排除

### 问题：AEX 未生效

1. 检查 Gateway 日志是否有 `[qclaw-plugin:aex-omnimodule]` 相关输出
2. 确认 `npm run build` 没有报错
3. 检查 `config.json` 中的路径是否正确

### 问题：编译错误

```bash
# 安装依赖
cd D:/QClaw/resources/openclaw/config/extensions/qclaw-plugin
npm install

# 重新编译
npm run build
```

### 问题：Python 脚本执行失败

1. 检查 Python 路径：`D:/Python/3/python.exe`
2. 检查依赖包：`pip install numpy scikit-learn`
3. 手动测试：
   ```bash
   cd D:/QClawAEXModule
   python skill/scripts/emotion_analyzer.py "测试消息"
   ```

## 文件说明

| 文件 | 说明 |
|------|------|
| `install_aex.py` | 通用一键安装器 |
| `install_aex_qclaw.py` | qclaw-plugin 专用安装器 |
| `skill/scripts/emotion_analyzer.py` | 情绪分析脚本 |
| `skill/scripts/search_learn.py` | 知识检索脚本 |
| `skill/scripts/db_manager.py` | 数据库管理 |

## 许可证

MIT License - 详见 LICENSE 文件
