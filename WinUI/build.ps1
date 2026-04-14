<#
AI新闻自动化系统 - WinUI 打包脚本
#>

param(
    [string]$Configuration = "Release",
    [string]$Platform = "x64",
    [string]$OutputPath = "bin"
)

$ErrorActionPreference = "Stop"

Write-Host "开始构建 AI新闻自动化系统..." -ForegroundColor Cyan

# 确保输出目录存在
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

try {
    # 构建主应用
    Write-Host "`n1. 构建主应用..." -ForegroundColor Yellow
    dotnet publish "AINewsPipeline.WinUI\AINewsPipeline.WinUI.csproj" `
        -c $Configuration `
        -r win-$Platform `
        --self-contained true `
        -o "$OutputPath\win-$Platform" `
        /p:PublishSingleFile=true `
        /p:PublishTrimmed=true
    
    Write-Host "主应用构建成功!" -ForegroundColor Green

    # 创建打包目录
    $packageDir = "$OutputPath\package"
    New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

    # 复制必要文件
    Write-Host "`n2. 复制配置文件..." -ForegroundColor Yellow
    Copy-Item -Path "..\config\*" -Destination "$packageDir\config" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "..\resources\styles\*" -Destination "$packageDir\resources\styles" -Recurse -Force -ErrorAction SilentlyContinue
    
    # 创建数据目录
    New-Item -ItemType Directory -Path "$packageDir\data\export" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packageDir\data\images" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packageDir\data\llm_cache" -Force | Out-Null
    New-Item -ItemType Directory -Path "$packageDir\logs" -Force | Out-Null

    Write-Host "配置文件复制成功!" -ForegroundColor Green

    # 创建批处理启动脚本
    Write-Host "`n3. 创建启动脚本..." -ForegroundColor Yellow
    $startScript = @"
@echo off
cd /d "%~dp0"
if not exist "data\news_pipeline.db" (
    echo 初始化数据库...
)
start "" "AINewsPipeline.WinUI.exe"
"@
    $startScript | Out-File -FilePath "$OutputPath\win-$Platform\start.bat" -Encoding utf8

    Write-Host "启动脚本创建成功!" -ForegroundColor Green

    # 创建ZIP压缩包
    Write-Host "`n4. 创建压缩包..." -ForegroundColor Yellow
    $zipPath = "$OutputPath\AI新闻自动化系统_v1.0.0_win-$Platform.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path "$OutputPath\win-$Platform\*" -DestinationPath $zipPath -Force

    Write-Host "压缩包创建成功: $zipPath" -ForegroundColor Green

    Write-Host "`n==============================================" -ForegroundColor Cyan
    Write-Host "构建完成!" -ForegroundColor Green
    Write-Host "输出目录: $OutputPath\win-$Platform" -ForegroundColor White
    Write-Host "压缩包: $zipPath" -ForegroundColor White
    Write-Host "==============================================" -ForegroundColor Cyan

} catch {
    Write-Host "`n构建失败: $_" -ForegroundColor Red
    exit 1
}