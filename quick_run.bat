@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: AI 新闻自动化系统 - 命令行采集模式
:: 使用方法：
::   1. 双击运行：quick_run.bat
::   2. 自定义参数：quick_run.bat 科技 人工智能 20
:: ============================================================

cd /d "%~dp0"

:: 默认参数
set "INDUSTRY=%~1"
set "TOPIC=%~2"
set "COUNT=%~3"

:: 使用默认值
if "%INDUSTRY%"=="" set "INDUSTRY=科技"
if "%TOPIC%"=="" set "TOPIC=人工智能"
if "%COUNT%"=="" set "COUNT=10"

echo ========================================
echo    AI 新闻自动化系统 - 快速采集
echo ========================================
echo.
echo 行业：%INDUSTRY%
echo 主题：%TOPIC%
echo 数量：%COUNT%
echo.

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行 start_windows.bat
    pause
    exit /b 1
)

:: 激活并运行采集
call venv\Scripts\activate.bat
python main.py run --industry "%INDUSTRY%" --topic "%TOPIC%" --count %COUNT%

pause
