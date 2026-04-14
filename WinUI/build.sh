#!/bin/bash

# AI新闻自动化系统 - WinUI 打包脚本
# 注意：WinUI 3项目需要在Windows环境下构建

CONFIGURATION="Release"
PLATFORM="x64"
OUTPUT_PATH="bin"

echo "=============================================="
echo "AI新闻自动化系统 - WinUI 打包脚本"
echo "=============================================="
echo ""

if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
    echo "警告：当前环境不是Windows"
    echo ""
    echo "WinUI 3项目需要在Windows环境下构建，因为XAML编译器是Windows特定的。"
    echo ""
    echo "请在Windows系统中执行以下步骤："
    echo "1. 安装 Visual Studio 2022（含 .NET 8 开发工具）"
    echo "2. 安装 Windows App SDK 1.5"
    echo "3. 打开项目文件 AINewsPipeline.WinUI.sln"
    echo "4. 右键点击项目 -> 发布 -> 创建配置文件"
    echo "5. 选择 '文件夹' 目标，配置发布设置"
    echo "6. 点击 '发布' 按钮"
    echo ""
    echo "或者使用PowerShell脚本："
    echo "powershell -File build.ps1"
    echo ""
    echo "=============================================="
    exit 1
fi

echo "开始构建 AI新闻自动化系统..."

# 确保输出目录存在
mkdir -p "$OUTPUT_PATH"

# 构建主应用
echo ""
echo "1. 构建主应用..."
dotnet publish "AINewsPipeline.WinUI/AINewsPipeline.WinUI.csproj" \
    -c "$CONFIGURATION" \
    -r "win-$PLATFORM" \
    --self-contained true \
    -o "$OUTPUT_PATH/win-$PLATFORM" \
    /p:PublishSingleFile=true \
    /p:PublishTrimmed=true \
    /p:WindowsAppSDKSelfContained=true

if [ $? -eq 0 ]; then
    echo "主应用构建成功!"
else
    echo "主应用构建失败!"
    exit 1
fi

# 复制必要文件
echo ""
echo "2. 复制配置文件..."
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/config"
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/resources/styles"
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/data/export"
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/data/images"
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/data/llm_cache"
mkdir -p "$OUTPUT_PATH/win-$PLATFORM/logs"

cp -r ../config/* "$OUTPUT_PATH/win-$PLATFORM/config/" 2>/dev/null || true
cp -r ../resources/styles/* "$OUTPUT_PATH/win-$PLATFORM/resources/styles/" 2>/dev/null || true

echo "配置文件复制成功!"

# 创建批处理启动脚本
echo ""
echo "3. 创建启动脚本..."
cat > "$OUTPUT_PATH/win-$PLATFORM/start.bat" << 'EOF'
@echo off
cd /d "%~dp0"
if not exist "data\news_pipeline.db" (
    echo 初始化数据库...
)
start "" "AINewsPipeline.WinUI.exe"
EOF

echo "启动脚本创建成功!"

# 创建ZIP压缩包
echo ""
echo "4. 创建压缩包..."
ZIP_PATH="$OUTPUT_PATH/AI新闻自动化系统_v1.0.0_win-$PLATFORM.zip"
rm -f "$ZIP_PATH"

cd "$OUTPUT_PATH/win-$PLATFORM"
zip -r "../$(basename "$ZIP_PATH")" *
cd - > /dev/null

echo "压缩包创建成功: $ZIP_PATH"

echo ""
echo "=============================================="
echo "构建完成!"
echo "输出目录: $OUTPUT_PATH/win-$PLATFORM"
echo "压缩包: $ZIP_PATH"
echo "=============================================="