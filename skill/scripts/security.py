#!/usr/bin/env python3
"""
AEX全知模块 - 安全控制模块
负责密码验证、错误计数、锁定机制
"""

import hashlib
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# 动态检测根目录
SKILL_DIR = Path(__file__).resolve().parent.parent
_CANDIDATE = SKILL_DIR.parent / "db"
_FALLBACK = Path("D:/QClawAEXModule/db")
ROOT_DIR = _CANDIDATE if (_CANDIDATE.exists() or not _FALLBACK.exists()) else _FALLBACK
MAX_ATTEMPTS = 10
LOCKOUT_DURATION = 3600  # 锁定1小时

# ═══════════════════════════════════════════════════════
# 作者信息 — 硬编码，不可修改
# ═══════════════════════════════════════════════════════
AUTHOR = {
    "name": "QX",
    "phone": "+86 133143713096",
    "email": ["QXAEX520@163.com", "QXAEX520@gmail.com"],
    "qq": "32208966020",
    "wechat": "QXAEX520"
}

class SecurityManager:
    """安全管理器"""

    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else ROOT_DIR
        self.config_file = self.root_dir / "config.json"
        self._ensure_config()

    def _ensure_config(self):
        """确保配置文件存在"""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_file}\n"
                f"请先运行 init_system.py 初始化 AEX 模块"
            )

    @staticmethod
    def get_author() -> dict:
        """获取作者信息（硬编码，不可篡改）"""
        return dict(AUTHOR)

    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_config(self) -> dict:
        """加载配置"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_config(self, config: dict):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _is_valid_format(self, password: str) -> bool:
        """检查密码格式（纯数字字母）"""
        if not password:
            return False
        return password.isalnum()

    def is_locked(self) -> tuple:
        """检查是否锁定，返回 (是否锁定, 剩余时间)"""
        config = self._load_config()

        if config.get("locked_until"):
            locked_until = datetime.fromisoformat(config["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).total_seconds()
                return True, int(remaining)
            else:
                config["failed_attempts"] = 0
                config["locked_until"] = None
                self._save_config(config)

        return False, 0

    def verify_password(self, password: str) -> tuple:
        """
        验证密码
        返回: (是否成功, 消息)
        """
        locked, remaining = self.is_locked()
        if locked:
            return False, f"模块已锁定，请等待 {remaining} 秒后重试"

        if not self._is_valid_format(password):
            return False, "密码格式错误：只允许数字和字母，不接受标点、空格或乱码"

        config = self._load_config()
        password_hash = self._hash_password(password)

        if password_hash == config["password_hash"]:
            config["failed_attempts"] = 0
            config["last_attempt"] = datetime.now().isoformat()
            self._save_config(config)
            return True, "验证成功"
        else:
            config["failed_attempts"] = config.get("failed_attempts", 0) + 1
            config["last_attempt"] = datetime.now().isoformat()

            remaining_attempts = MAX_ATTEMPTS - config["failed_attempts"]

            if remaining_attempts <= 0:
                locked_until = datetime.now() + timedelta(seconds=LOCKOUT_DURATION)
                config["locked_until"] = locked_until.isoformat()
                self._save_config(config)
                return False, f"密码错误次数过多，模块已锁定 {LOCKOUT_DURATION // 3600} 小时"
            else:
                self._save_config(config)
                return False, f"密码错误，剩余尝试次数: {remaining_attempts}，10次错误将锁定模块"

    def require_password(self, operation: str) -> bool:
        """交互式要求输入密码"""
        print(f"\n[安全验证] 操作: {operation}")
        print("此操作需要密码验证")
        print("提示: 密码为纯数字字母，不接受标点、空格或乱码")

        password = input("请输入密码: ").strip()

        success, message = self.verify_password(password)

        if success:
            print(f"[OK] {message}")
            return True
        else:
            print(f"[X] {message}")
            return False

    def change_password(self, old_password: str, new_password: str) -> tuple:
        """修改密码"""
        success, message = self.verify_password(old_password)
        if not success:
            return False, message

        if not self._is_valid_format(new_password):
            return False, "新密码格式错误：只允许数字和字母"

        config = self._load_config()
        config["password_hash"] = self._hash_password(new_password)
        self._save_config(config)

        return True, "密码修改成功"

    def reset_lockout(self, password: str) -> tuple:
        """手动解除锁定（需要密码）"""
        success, message = self.verify_password(password)
        if not success:
            return False, message

        config = self._load_config()
        config["failed_attempts"] = 0
        config["locked_until"] = None
        self._save_config(config)

        return True, "锁定已解除"

    def get_prefix(self) -> str:
        """获取用户设定的输出前缀"""
        config = self._load_config()
        return config.get("prefix", "AEX")

    def get_config(self) -> dict:
        """获取完整配置（只读）"""
        config = self._load_config()
        safe = {k: v for k, v in config.items() if k != "password_hash"}
        return safe


if __name__ == "__main__":
    sm = SecurityManager()
    print("Security Manager initialized")
    print(f"Config file: {sm.config_file}")
    result, msg = sm.verify_password("test")
    print(f"Test: {result}, {msg}")
