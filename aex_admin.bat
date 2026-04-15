@echo off
chcp 65001 >nul
title AEX 全知模块 - 超级管理控制台
echo.
echo ═══════════════════════════════════════════════════════════════════
echo   AEX 全知模块 - 超级管理控制台
echo ═══════════════════════════════════════════════════════════════════
echo.

python "%~dp0aex_admin.py" %*

if errorlevel 1 (
    echo.
    echo 发生错误，请检查 Python 环境
    pause
)
