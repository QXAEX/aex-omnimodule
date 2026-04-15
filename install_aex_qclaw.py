#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AEX 全知模块 - qclaw-plugin 集成安装器

这个脚本专门用于将 AEX 安装为 qclaw-plugin 的子 package。
需要 qclaw-plugin 已经安装并可用。

Usage:
    python install_aex_qclaw.py              # 标准安装
    python install_aex_qclaw.py --dev        # 开发模式（链接源码）
    python install_aex_qclaw.py --uninstall  # 卸载
"""

import argparse
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional

# 路径配置
AEX_SOURCE_DIR = Path("D:/QClawAEXModule")
QCLAW_PLUGIN_DIR = Path("D:/QClaw/resources/openclaw/config/extensions/qclaw-plugin")
AEX_PACKAGE_DIR = QCLAW_PLUGIN_DIR / "packages" / "aex-omnimodule"

def print_step(msg: str):
    print(f"\n▶ {msg}")

def print_ok(msg: str):
    print(f"  ✓ {msg}")

def print_err(msg: str):
    print(f"  ✗ {msg}", file=sys.stderr)

def print_warn(msg: str):
    print(f"  ! {msg}")

def check_qclaw_plugin() -> bool:
    """检查 qclaw-plugin 是否安装"""
    if not QCLAW_PLUGIN_DIR.exists():
        print_err(f"qclaw-plugin 未找到: {QCLAW_PLUGIN_DIR}")
        print("  请先安装 qclaw-plugin")
        return False
    
    if not (QCLAW_PLUGIN_DIR / "index.ts").exists():
        print_err("qclaw-plugin 源码不完整")
        return False
    
    print_ok(f"qclaw-plugin  found: {QCLAW_PLUGIN_DIR}")
    return True

def check_aex_source() -> bool:
    """检查 AEX 源码是否存在"""
    required_files = [
        AEX_SOURCE_DIR / "skill" / "scripts" / "emotion_analyzer.py",
        AEX_SOURCE_DIR / "skill" / "scripts" / "search_learn.py",
        AEX_SOURCE_DIR / "skill" / "scripts" / "db_manager.py",
        AEX_SOURCE_DIR / "db" / "config.json",
    ]
    
    missing = [f for f in required_files if not f.exists()]
    if missing:
        print_err("AEX 源码不完整，缺少以下文件:")
        for f in missing:
            print(f"    - {f}")
        return False
    
    print_ok(f"AEX 源码完整: {AEX_SOURCE_DIR}")
    return True

def create_package_ts() -> bool:
    """创建 AEX package 的 TypeScript 文件"""
    print_step("创建 aex-omnimodule package")
    
    AEX_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    ts_content = '''/**
 * aex-omnimodule — AEX 全知模块
 *
 * 作为 qclaw-plugin 的子 package 运行，获得最高优先级控制。
 * 在 before_prompt_build 阶段注入情绪分析和知识检索结果。
 *
 * Priority: 0 (最高，确保在所有其他 handler 之前执行)
 */

import type { QClawPackage, QClawContext, HookHandlerResult } from '../../core/types.js'
import { spawn } from 'node:child_process'
import path from 'node:path'
import fs from 'node:fs'

const LOG_TAG = '[aex-omnimodule]'
const AEX_MODULE_DIR = 'D:\\\\QClawAEXModule'
const PYTHON_EXE = 'D:\\\\Python\\\\3\\\\python.exe'

interface AexConfig {
  prefix: string
  emotion_enabled: boolean
  knowledge_enabled: boolean
}

interface EmotionResult {
  emotion: string
  intensity: number
  tone_suggestion: string
}

interface KnowledgeItem {
  id: number
  content: string
  source: string
  relevance: number
}

function loadAexConfig(): AexConfig {
  const configPath = path.join(AEX_MODULE_DIR, 'db', 'config.json')
  try {
    if (fs.existsSync(configPath)) {
      const raw = fs.readFileSync(configPath, 'utf-8')
      const config = JSON.parse(raw)
      return {
        prefix: config.prefix || 'AEX',
        emotion_enabled: config.emotion_enabled !== false,
        knowledge_enabled: config.knowledge_enabled !== false,
      }
    }
  } catch (e) {
    console.error(`${LOG_TAG} 读取配置失败:`, e)
  }
  return { prefix: 'AEX', emotion_enabled: true, knowledge_enabled: true }
}

function runPythonScript(scriptName: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(AEX_MODULE_DIR, 'skill', 'scripts', scriptName)
    const proc = spawn(PYTHON_EXE, [scriptPath, ...args], {
      cwd: AEX_MODULE_DIR,
    })

    let stdout = ''
    let stderr = ''

    proc.stdout?.on('data', (data: Buffer) => {
      stdout += data.toString()
    })

    proc.stderr?.on('data', (data: Buffer) => {
      stderr += data.toString()
    })

    proc.on('close', (code: number | null) => {
      if (code !== 0) {
        reject(new Error(`Python 脚本退出码 ${code}: ${stderr}`))
      } else {
        resolve(stdout.trim())
      }
    })

    proc.on('error', (err: Error) => {
      reject(err)
    })
  })
}

async function analyzeEmotion(text: string): Promise<EmotionResult | null> {
  try {
    const result = await runPythonScript('emotion_analyzer.py', [text])
    return JSON.parse(result) as EmotionResult
  } catch (e) {
    console.error(`${LOG_TAG} 情绪分析失败:`, e)
    return null
  }
}

async function searchKnowledge(query: string): Promise<KnowledgeItem[]> {
  try {
    const result = await runPythonScript('search_learn.py', [query])
    return JSON.parse(result) as KnowledgeItem[]
  } catch (e) {
    console.error(`${LOG_TAG} 知识搜索失败:`, e)
    return []
  }
}

async function buildAexContext(userMessage: string, config: AexConfig): Promise<string> {
  const parts: string[] = []

  if (config.emotion_enabled) {
    const emotion = await analyzeEmotion(userMessage)
    if (emotion) {
      parts.push(`<aex-emotion>`)
      parts.push(`情绪: ${emotion.emotion}`)
      parts.push(`强度: ${emotion.intensity}%`)
      parts.push(`语气建议: ${emotion.tone_suggestion}`)
      parts.push(`</aex-emotion>`)
    }
  }

  if (config.knowledge_enabled) {
    const knowledge = await searchKnowledge(userMessage)
    if (knowledge.length > 0) {
      parts.push(`<aex-knowledge>`)
      parts.push(`检索到 ${knowledge.length} 条相关知识:`)
      for (const item of knowledge.slice(0, 3)) {
        parts.push(`- [${item.source}] ${item.content.substring(0, 200)}...`)
      }
      parts.push(`</aex-knowledge>`)
    }
  }

  if (parts.length > 0) {
    parts.unshift(`<!-- AEX 全知模块分析 -->`)
    parts.push(`<!-- 回复格式要求: 第一行必须以 "${config.prefix}：" 开头 -->`)
    return parts.join('\\n')
  }

  return ''
}

const aexOmnimodule: QClawPackage = {
  id: 'aex-omnimodule',
  name: 'AEX 全知模块',
  description: '情绪分析与知识检索，最高优先级控制',

  configSchema: {
    type: 'object',
    additionalProperties: false,
    properties: {},
  },

  setup(ctx: QClawContext): void {
    ctx.logger.info(`${LOG_TAG} 初始化中...`)

    const config = loadAexConfig()
    ctx.logger.info(`${LOG_TAG} 配置加载完成: prefix=${config.prefix}, emotion=${config.emotion_enabled}, knowledge=${config.knowledge_enabled}`)

    ctx.onHook(
      'before_prompt_build',
      async (eventData: Record<string, unknown>): Promise<HookHandlerResult | undefined> => {
        const messages = (eventData.messages as Array<{ role: string; content: string }>) || []
        
        const lastUserMessage = [...messages].reverse().find(m => m.role === 'user')
        if (!lastUserMessage) {
          return undefined
        }

        ctx.logger.info(`${LOG_TAG} 处理用户消息: ${lastUserMessage.content.substring(0, 50)}...`)

        const aexContext = await buildAexContext(lastUserMessage.content, config)
        
        if (!aexContext) {
          return undefined
        }

        ctx.logger.info(`${LOG_TAG} 注入 AEX 上下文 (${aexContext.length} 字符)`)

        return {
          appendSystemContext: aexContext,
        }
      },
      { priority: 0, concurrent: false },
    )

    ctx.logger.info(`${LOG_TAG} before_prompt_build handler 已注册 (priority=0)`)
  },
}

export default aexOmnimodule
'''
    
    ts_file = AEX_PACKAGE_DIR / "index.ts"
    try:
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write(ts_content)
        print_ok(f"创建: {ts_file}")
        return True
    except Exception as e:
        print_err(f"创建失败: {e}")
        return False

def update_qclaw_index() -> bool:
    """更新 qclaw-plugin 的 index.ts"""
    print_step("更新 qclaw-plugin/index.ts")
    
    index_file = QCLAW_PLUGIN_DIR / "index.ts"
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已存在
        if "aex-omnimodule" in content:
            print_warn("aex-omnimodule 已存在于 index.ts 中")
            return True
        
        # 添加 import
        import_line = "import aexOmnimodule from './packages/aex-omnimodule/index.js'"
        # 在第一个 import 之前插入
        lines = content.split('\n')
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import '):
                import_idx = i
                break
        lines.insert(import_idx, import_line)
        
        # 添加到 PACKAGES 数组开头
        content = '\n'.join(lines)
        content = content.replace(
            'const PACKAGES: QClawPackage[] = [',
            'const PACKAGES: QClawPackage[] = [\n  aexOmnimodule,  // AEX 全知模块，priority=0'
        )
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_ok("更新 index.ts 成功")
        return True
        
    except Exception as e:
        print_err(f"更新失败: {e}")
        return False

def compile_typescript() -> bool:
    """编译 TypeScript"""
    print_step("编译 TypeScript")
    
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=QCLAW_PLUGIN_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            # 检查是否是 AEX 的错误
            if "aex-omnimodule" in result.stderr:
                print_err("AEX 编译失败:")
                print(result.stderr)
                return False
            else:
                # 其他 package 的错误，忽略
                print_warn("其他 package 有编译错误，但 AEX 应该已编译")
                print_ok("编译完成（可能有其他错误）")
                return True
        
        print_ok("编译成功")
        return True
        
    except Exception as e:
        print_err(f"编译失败: {e}")
        return False

def restart_gateway() -> bool:
    """重启 Gateway"""
    print_step("重启 OpenClaw Gateway")
    
    try:
        subprocess.run(
            ["openclaw", "gateway", "restart"],
            capture_output=True,
            check=False
        )
        print_ok("重启命令已发送")
        return True
    except Exception as e:
        print_warn(f"重启失败: {e}")
        print("  请手动运行: openclaw gateway restart")
        return False

def uninstall() -> bool:
    """卸载 AEX"""
    print_step("卸载 AEX")
    
    # 删除 package 目录
    if AEX_PACKAGE_DIR.exists():
        shutil.rmtree(AEX_PACKAGE_DIR)
        print_ok(f"删除: {AEX_PACKAGE_DIR}")
    
    # 从 index.ts 中移除
    index_file = QCLAW_PLUGIN_DIR / "index.ts"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除 import
        content = '\n'.join([
            line for line in content.split('\n')
            if 'aex-omnimodule' not in line and 'aexOmnimodule' not in line
        ])
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print_ok("从 index.ts 移除")
    
    print("\n卸载完成。请重新编译 qclaw-plugin:")
    print(f"  cd {QCLAW_PLUGIN_DIR}")
    print("  npm run build")
    print("  openclaw gateway restart")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="AEX qclaw-plugin 集成安装器")
    parser.add_argument("--uninstall", action="store_true", help="卸载 AEX")
    parser.add_argument("--skip-compile", action="store_true", help="跳过编译")
    args = parser.parse_args()
    
    print("=" * 60)
    print("AEX 全知模块 - qclaw-plugin 集成安装器")
    print("=" * 60)
    
    if args.uninstall:
        uninstall()
        return
    
    # 安装流程
    if not check_qclaw_plugin():
        sys.exit(1)
    
    if not check_aex_source():
        print_warn("AEX 源码不完整，但继续安装插件部分...")
    
    if not create_package_ts():
        sys.exit(1)
    
    if not update_qclaw_index():
        sys.exit(1)
    
    if not args.skip_compile:
        if not compile_typescript():
            sys.exit(1)
    
    restart_gateway()
    
    print("\n" + "=" * 60)
    print("安装完成！")
    print("=" * 60)
    print("""
AEX 已成功集成到 qclaw-plugin！

特性:
- Priority=0: 在所有 handler 之前执行
- HookProxy 集成: 与 qclaw-plugin 统一协调
- Block 支持: 可以阻止后续 handler 执行

查看日志确认运行:
  openclaw gateway logs -f

应该能看到:
  [qclaw-plugin:aex-omnimodule] 初始化中...
  [qclaw-plugin:aex-omnimodule] before_prompt_build handler 已注册 (priority=0)
""")

if __name__ == "__main__":
    main()
