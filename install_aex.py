#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AEX 全知模块 - 一键安装程序
AEX Omnimodule One-Click Installer

功能：
1. 检测 Python 环境
2. 安装依赖包
3. 创建目录结构
4. 复制/编译插件文件
5. 配置 OpenClaw
6. 重启 Gateway

Usage:
    python install_aex.py              # 交互式安装
    python install_aex.py --auto       # 自动模式（使用默认配置）
    python install_aex.py --uninstall  # 卸载
"""

import argparse
import os
import sys
import shutil
import subprocess
import json
import platform
from pathlib import Path
from typing import Optional, Tuple

# ============================================================================
# 配置常量
# ============================================================================

AEX_VERSION = "1.0.0"
AEX_MODULE_NAME = "aex-omnimodule"

# 默认安装路径
DEFAULT_AEX_DIR = Path("D:/QClawAEXModule")
DEFAULT_OPENCLAW_DIR = Path("D:/QClaw/resources/openclaw")

# 依赖包
REQUIRED_PACKAGES = [
    "numpy",
    "scikit-learn",
]

# GitHub 仓库
GITHUB_REPO = "https://github.com/QXAEX/aex-omnimodule"
GITHUB_RAW = "https://raw.githubusercontent.com/QXAEX/aex-omnimodule/main"

# ============================================================================
# 工具函数
# ============================================================================

def print_banner():
    """打印安装横幅"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           AEX 全知模块 (AEX Omnimodule) v{AEX_VERSION}              ║
║                                                                  ║
║     情绪分析 · 知识检索 · 智能上下文注入 · 最高优先级控制          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_step(step_num: int, total: int, message: str):
    """打印步骤信息"""
    print(f"\n[{step_num}/{total}] {message}")
    print("-" * 60)

def print_success(message: str):
    """打印成功信息"""
    print(f"  ✓ {message}")

def print_error(message: str):
    """打印错误信息"""
    print(f"  ✗ {message}", file=sys.stderr)

def print_warning(message: str):
    """打印警告信息"""
    print(f"  ! {message}")

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd,
                output=result.stdout, stderr=result.stderr
            )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        if check:
            raise
        return -1, "", str(e)

def check_python() -> Tuple[bool, str]:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python {version.major}.{version.minor}.{version.micro}"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"

def find_python_executable() -> Optional[Path]:
    """查找 Python 可执行文件"""
    # 首先检查当前 Python
    current = Path(sys.executable)
    if current.exists():
        return current
    
    # 检查常见路径
    candidates = [
        Path("D:/Python/3/python.exe"),
        Path("C:/Python312/python.exe"),
        Path("C:/Python311/python.exe"),
        Path("C:/Python310/python.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python/Python312/python.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python/Python311/python.exe",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    
    # 尝试从 PATH 查找
    python_cmd = shutil.which("python") or shutil.which("python3")
    if python_cmd:
        return Path(python_cmd)
    
    return None

def check_pip() -> bool:
    """检查 pip 是否可用"""
    try:
        import pip
        return True
    except ImportError:
        pass
    
    # 尝试运行 pip
    code, _, _ = run_command([sys.executable, "-m", "pip", "--version"], check=False)
    return code == 0

def install_package(package: str) -> bool:
    """安装 Python 包"""
    try:
        run_command([sys.executable, "-m", "pip", "install", "-q", package])
        return True
    except subprocess.CalledProcessError:
        return False

def download_file(url: str, dest: Path) -> bool:
    """下载文件"""
    try:
        import urllib.request
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception:
        return False

def clone_or_update_repo(dest: Path) -> bool:
    """克隆或更新 GitHub 仓库"""
    try:
        if (dest / ".git").exists():
            # 更新现有仓库
            run_command(["git", "pull"], cwd=dest)
        else:
            # 克隆新仓库
            if dest.exists():
                shutil.rmtree(dest)
            parent = dest.parent
            run_command(["git", "clone", GITHUB_REPO, dest.name], cwd=parent)
        return True
    except subprocess.CalledProcessError:
        return False

# ============================================================================
# 安装步骤
# ============================================================================

class AEXInstaller:
    """AEX 安装器"""
    
    def __init__(self, auto_mode: bool = False):
        self.auto_mode = auto_mode
        self.aex_dir: Path = DEFAULT_AEX_DIR
        self.openclaw_dir: Path = DEFAULT_OPENCLAW_DIR
        self.python_exe: Optional[Path] = None
        self.errors: list = []
        
    def detect_paths(self) -> bool:
        """检测安装路径"""
        print_step(1, 7, "检测安装环境")
        
        # 检测 AEX 目录
        if not self.auto_mode:
            print(f"  默认 AEX 安装目录: {self.aex_dir}")
            response = input("  是否使用默认目录? [Y/n]: ").strip().lower()
            if response and response not in ('y', 'yes'):
                custom_dir = input("  请输入 AEX 安装目录: ").strip()
                if custom_dir:
                    self.aex_dir = Path(custom_dir)
        
        # 检测 OpenClaw 目录
        if not self.auto_mode:
            print(f"  默认 OpenClaw 目录: {self.openclaw_dir}")
            response = input("  是否使用默认目录? [Y/n]: ").strip().lower()
            if response and response not in ('y', 'yes'):
                custom_dir = input("  请输入 OpenClaw 目录: ").strip()
                if custom_dir:
                    self.openclaw_dir = Path(custom_dir)
        
        # 验证 OpenClaw 目录
        if not (self.openclaw_dir / "config" / "extensions").exists():
            print_error(f"OpenClaw 目录无效: {self.openclaw_dir}")
            print("  请确认 OpenClaw 已正确安装")
            return False
        
        print_success(f"AEX 目录: {self.aex_dir}")
        print_success(f"OpenClaw 目录: {self.openclaw_dir}")
        return True
    
    def check_dependencies(self) -> bool:
        """检查依赖"""
        print_step(2, 7, "检查 Python 环境")
        
        # 检查 Python 版本
        ok, version = check_python()
        if not ok:
            print_error(f"Python 版本过低: {version}")
            print("  需要 Python 3.8 或更高版本")
            return False
        print_success(f"Python 版本: {version}")
        
        # 查找 Python 可执行文件
        self.python_exe = find_python_executable()
        if not self.python_exe:
            print_error("无法找到 Python 可执行文件")
            return False
        print_success(f"Python 路径: {self.python_exe}")
        
        # 检查 pip
        if not check_pip():
            print_error("pip 未安装")
            return False
        print_success("pip 可用")
        
        return True
    
    def install_python_packages(self) -> bool:
        """安装 Python 依赖包"""
        print_step(3, 7, "安装 Python 依赖包")
        
        for package in REQUIRED_PACKAGES:
            print(f"  安装 {package}...")
            if install_package(package):
                print_success(f"{package} 安装完成")
            else:
                print_error(f"{package} 安装失败")
                return False
        
        return True
    
    def setup_directories(self) -> bool:
        """创建目录结构"""
        print_step(4, 7, "创建目录结构")
        
        dirs = [
            self.aex_dir / "db",
            self.aex_dir / "skill" / "scripts",
            self.aex_dir / "skill" / "templates",
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"创建目录: {dir_path}")
        
        return True
    
    def download_source(self) -> bool:
        """下载 AEX 源代码"""
        print_step(5, 7, "下载 AEX 源代码")
        
        # 尝试从 GitHub 克隆
        print("  尝试从 GitHub 克隆仓库...")
        if clone_or_update_repo(self.aex_dir):
            print_success("从 GitHub 克隆成功")
            return True
        
        print_warning("GitHub 克隆失败，尝试下载单个文件...")
        
        # 备用方案：下载关键文件
        files_to_download = [
            ("skill/scripts/emotion_analyzer.py", self.aex_dir / "skill" / "scripts" / "emotion_analyzer.py"),
            ("skill/scripts/search_learn.py", self.aex_dir / "skill" / "scripts" / "search_learn.py"),
            ("skill/scripts/db_manager.py", self.aex_dir / "skill" / "scripts" / "db_manager.py"),
            ("db/config.example.json", self.aex_dir / "db" / "config.example.json"),
        ]
        
        success = True
        for remote_path, local_path in files_to_download:
            url = f"{GITHUB_RAW}/{remote_path}"
            print(f"  下载 {remote_path}...")
            if download_file(url, local_path):
                print_success(f"下载成功: {remote_path}")
            else:
                print_error(f"下载失败: {remote_path}")
                success = False
        
        return success
    
    def create_config(self) -> bool:
        """创建配置文件"""
        print_step(6, 7, "创建配置文件")
        
        config_path = self.aex_dir / "db" / "config.json"
        
        if config_path.exists():
            print_warning("配置文件已存在，跳过创建")
            return True
        
        config = {
            "initialized": True,
            "version": AEX_VERSION,
            "prefix": "AEX",
            "emotion_enabled": True,
            "knowledge_enabled": True,
            "python_path": str(self.python_exe),
            "scripts_dir": str(self.aex_dir / "skill" / "scripts"),
            "db_dir": str(self.aex_dir / "db"),
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print_success(f"创建配置文件: {config_path}")
            return True
        except Exception as e:
            print_error(f"创建配置文件失败: {e}")
            return False
    
    def install_plugin(self) -> bool:
        """安装 OpenClaw 插件"""
        print_step(7, 7, "安装 OpenClaw 插件")
        
        # 检查 qclaw-plugin 是否存在
        qclaw_plugin_dir = self.openclaw_dir / "config" / "extensions" / "qclaw-plugin"
        if not qclaw_plugin_dir.exists():
            print_error("qclaw-plugin 未安装")
            print("  AEX 需要 qclaw-plugin 作为宿主")
            return False
        
        # 复制 AEX package 到 qclaw-plugin
        aex_package_src = self.aex_dir / "aex-context-plugin" / "index.js"
        if not aex_package_src.exists():
            # 尝试从源码目录查找
            aex_package_src = self.aex_dir / "index.js"
        
        # 创建 package 目录
        package_dir = qclaw_plugin_dir / "packages" / "aex-omnimodule"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制 TypeScript 源码
        ts_src = self.aex_dir / "aex-context-plugin" / "index.ts"
        if ts_src.exists():
            shutil.copy2(ts_src, package_dir / "index.ts")
            print_success(f"复制 TypeScript 源码到: {package_dir}")
        
        # 更新 qclaw-plugin 的 index.ts
        print("  更新 qclaw-plugin 主入口...")
        
        # 这里需要手动修改 index.ts，添加 import 和 PACKAGES
        # 由于涉及代码修改，我们提供指导而不是自动修改
        print_warning("请手动修改 qclaw-plugin/index.ts:")
        print("  1. 在 import 部分添加: import aexOmnimodule from './packages/aex-omnimodule/index.js'")
        print("  2. 在 PACKAGES 数组开头添加: aexOmnimodule,")
        print("  3. 运行: npm run build")
        print("  4. 重启 OpenClaw Gateway")
        
        return True
    
    def restart_gateway(self) -> bool:
        """重启 OpenClaw Gateway"""
        print("\n" + "=" * 60)
        print("重启 OpenClaw Gateway")
        print("=" * 60)
        
        try:
            run_command(["openclaw", "gateway", "restart"], check=False)
            print_success("Gateway 重启命令已发送")
            return True
        except Exception as e:
            print_error(f"重启失败: {e}")
            print("  请手动运行: openclaw gateway restart")
            return False
    
    def install(self) -> bool:
        """执行完整安装"""
        print_banner()
        
        steps = [
            ("检测安装环境", self.detect_paths),
            ("检查 Python 环境", self.check_dependencies),
            ("安装 Python 依赖", self.install_python_packages),
            ("创建目录结构", self.setup_directories),
            ("下载 AEX 源代码", self.download_source),
            ("创建配置文件", self.create_config),
            ("安装 OpenClaw 插件", self.install_plugin),
        ]
        
        for name, step_func in steps:
            try:
                if not step_func():
                    print(f"\n安装中止: {name} 失败")
                    return False
            except Exception as e:
                print_error(f"步骤异常: {e}")
                return False
        
        # 重启 Gateway
        self.restart_gateway()
        
        # 完成
        print("\n" + "=" * 60)
        print("安装完成！")
        print("=" * 60)
        print(f"""
AEX 全知模块已成功安装！

安装目录: {self.aex_dir}
配置文件: {self.aex_dir}/db/config.json

使用方法:
1. 启动 OpenClaw Gateway（如果尚未启动）
2. 开始对话，AEX 会自动分析情绪和检索知识
3. 查看日志确认 AEX 正在运行

故障排除:
- 如果 AEX 未生效，检查 Gateway 日志
- 确认 qclaw-plugin 已正确编译 (npm run build)
- 检查 Python 路径配置是否正确

更多信息: {GITHUB_REPO}
""")
        
        return True
    
    def uninstall(self) -> bool:
        """卸载 AEX"""
        print_banner()
        print("卸载 AEX 全知模块")
        print("=" * 60)
        
        if not self.auto_mode:
            response = input("确认卸载 AEX? 这将删除所有数据! [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("卸载已取消")
                return False
        
        # 删除 AEX 目录
        if self.aex_dir.exists():
            shutil.rmtree(self.aex_dir)
            print_success(f"删除目录: {self.aex_dir}")
        
        # 删除插件文件
        qclaw_plugin_dir = self.openclaw_dir / "config" / "extensions" / "qclaw-plugin"
        package_dir = qclaw_plugin_dir / "packages" / "aex-omnimodule"
        if package_dir.exists():
            shutil.rmtree(package_dir)
            print_success(f"删除插件: {package_dir}")
        
        print("\n卸载完成")
        print("请手动从 qclaw-plugin/index.ts 中移除 aex-omnimodule 的 import 和引用")
        
        return True

# ============================================================================
# 主入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AEX 全知模块一键安装程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python install_aex.py              # 交互式安装
  python install_aex.py --auto       # 自动安装（使用默认配置）
  python install_aex.py --uninstall  # 卸载 AEX
        """
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="自动模式，不询问配置"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="卸载 AEX"
    )
    parser.add_argument(
        "--aex-dir",
        type=Path,
        default=DEFAULT_AEX_DIR,
        help=f"AEX 安装目录 (默认: {DEFAULT_AEX_DIR})"
    )
    parser.add_argument(
        "--openclaw-dir",
        type=Path,
        default=DEFAULT_OPENCLAW_DIR,
        help=f"OpenClaw 目录 (默认: {DEFAULT_OPENCLAW_DIR})"
    )
    
    args = parser.parse_args()
    
    installer = AEXInstaller(auto_mode=args.auto)
    installer.aex_dir = args.aex_dir
    installer.openclaw_dir = args.openclaw_dir
    
    if args.uninstall:
        success = installer.uninstall()
    else:
        success = installer.install()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
