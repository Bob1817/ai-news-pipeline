@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: AI 新闻自动化系统 - Windows 快速启动脚本
:: 使用方法：双击运行，或在命令行执行：start_windows.bat
:: ============================================================

cd /d "%~dp0"

set "PORT=8080"
set "VENV_DIR=%~dp0venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "PYTHON_CMD="

echo ========================================
echo    AI 新闻自动化系统 - Windows 启动
echo ========================================
echo.

:: 检测 Python 命令
where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -c "import sys" >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=py -3.12"
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [错误] 未找到 Python 环境!
    echo.
    echo 请先安装 Python 3.10+:
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载安装程序并运行
    echo 3. 安装时勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python 环境已就绪
%PYTHON_CMD% --version
echo.

:: 检查虚拟环境
if not exist "%VENV_PYTHON%" (
    echo [步骤 1/4] 创建虚拟环境...
    call %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败!
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
) else (
    echo [步骤 1/4] 虚拟环境已存在
)
echo.

:: 更新 pip
echo [步骤 2/4] 更新 pip...
call "%VENV_PYTHON%" -m pip install --upgrade pip -q
if errorlevel 1 (
    echo [错误] pip 更新失败!
    pause
    exit /b 1
)
echo [OK] pip 已更新
echo.

:: 安装项目依赖
echo [步骤 3/4] 安装项目依赖...
call "%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败!
    echo 请检查网络连接后重试
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

:: 安装 Playwright 浏览器
echo [步骤 4/4] 安装 Playwright 浏览器...
if not exist "%VENV_DIR%\Lib\site-packages\playwright\.msplaywright" (
    call "%VENV_PYTHON%" -m playwright install chromium
    call "%VENV_PYTHON%" -m playwright install-deps chromium
) else (
    echo [提示] 浏览器已存在，检查最新版本...
    call "%VENV_PYTHON%" -m playwright install --force
)
if errorlevel 1 (
    echo [错误] Playwright 浏览器安装失败!
    echo 请检查网络连接后重试
    pause
    exit /b 1
)
echo [OK] Playwright 浏览器已就绪
echo.

echo ========================================
echo    启动完成!
echo ========================================
echo.
echo 可用命令:
echo   1. 双击 start_windows.bat (启动 Web 管理后台)
echo   2. 命令行执行：python main.py web --port 8080
echo   3. 命令行采集：python main.py run --industry "科技" --topic "人工智能" --count 10
echo.
echo Web 管理后台：http://127.0.0.1:%PORT%
echo.

:: 自动打开浏览器
start "" "http://127.0.0.1:%PORT%"

:: 启动 Web 服务
call "%VENV_PYTHON%" main.py web --port %PORT%

endlocal
