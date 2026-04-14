# AI新闻自动化系统 - WinUI 3 版本

## 项目概述

这是基于 WinUI 3 框架的 AI 新闻自动化系统桌面端应用。

## 技术栈

- **框架**: WinUI 3 (Windows App SDK)
- **语言**: C# .NET 8
- **UI组件**: Windows UI Library
- **HTTP客户端**: System.Net.Http
- **JSON处理**: Newtonsoft.Json

## 项目结构

```
WinUI/
├── AINewsPipeline.WinUI.sln          # 解决方案文件
├── build.sh                           # macOS/Linux构建脚本
├── build.ps1                          # Windows构建脚本
├── AINewsPipeline.WinUI/              # 主应用项目
│   ├── Models/                        # 数据模型
│   ├── Services/                      # 服务层
│   ├── Views/                         # UI页面
│   ├── MainWindow.xaml(.cs)           # 主窗口
│   ├── App.xaml(.cs)                  # 应用入口
│   └── AINewsPipeline.WinUI.csproj    # 项目配置
└── AINewsPipeline.Package/            # MSIX打包项目
    ├── Package.appxmanifest           # 包清单
    └── AINewsPipeline.Package.wapproj # 打包配置
```

## 功能特性

### 1. 采集配置
- 行业选择（科技、财经、娱乐等）
- 关键词输入
- 采集数量设置
- 采集源选择（新闻网站、百度百科、微博热点）
- 实时日志显示

### 2. 文章管理
- 文章列表展示
- 搜索和筛选功能
- 文章预览和编辑
- 导出和删除功能

### 3. 发布管理
- 多平台选择（微信公众号、微博、知乎等）
- 批量发布功能
- 发布历史记录

### 4. 系统设置
- LLM配置（Ollama/OpenAI）
- 文章参数设置
- 发布设置
- 采集设置

## 构建说明

### 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 17763+ |
| Visual Studio | 2022（含 .NET 8 开发工具） |
| Windows App SDK | 1.5 或更高版本 |

### 方法一：使用 Visual Studio 2022

1. 打开解决方案文件 `AINewsPipeline.WinUI.sln`
2. 右键点击项目 `AINewsPipeline.WinUI`
3. 选择 **发布** -> **创建配置文件**
4. 选择 **文件夹** 作为目标
5. 配置发布设置：
   - 配置：Release
   - 目标框架：net8.0-windows10.0.19041.0
   - 运行时：win-x64（或 win-x86）
   - 勾选 "生成单个文件"
6. 点击 **发布** 按钮

### 方法二：使用 PowerShell

```powershell
cd WinUI
.\build.ps1
```

### 方法三：使用命令行

```powershell
dotnet publish "AINewsPipeline.WinUI/AINewsPipeline.WinUI.csproj" `
    -c Release `
    -r win-x64 `
    --self-contained true `
    -o bin/win-x64 `
    /p:PublishSingleFile=true `
    /p:PublishTrimmed=true `
    /p:WindowsAppSDKSelfContained=true
```

## 输出文件

构建完成后，输出目录结构：

```
WinUI/bin/win-x64/
├── AINewsPipeline.WinUI.exe    # 主可执行文件
├── start.bat                    # 启动脚本
├── config/                      # 配置文件目录
├── resources/                   # 资源文件目录
├── data/                        # 数据目录
│   ├── export/                  # 导出文章
│   ├── images/                  # 配图
│   └── llm_cache/               # LLM缓存
└── logs/                        # 日志目录
```

## MSIX 打包

### 创建 MSIX 安装包

1. 打开解决方案文件
2. 设置 `AINewsPipeline.Package` 为启动项目
3. 右键点击打包项目 -> **发布** -> **创建应用包**
4. 按照向导完成配置
5. 生成 `.msix` 或 `.msixbundle` 文件

### 安装 MSIX 包

```powershell
Add-AppxPackage -Path "AI新闻自动化系统_1.0.0.0_x64.msix"
```

## 运行方式

**开发模式**：
```powershell
cd WinUI/AINewsPipeline.WinUI
dotnet run
```

**发布后运行**：
```powershell
# 方式1：直接运行
.\bin\win-x64\AINewsPipeline.WinUI.exe

# 方式2：使用启动脚本
.\bin\win-x64\start.bat
```

## 与 Python 后端通信

WinUI 应用通过 HTTP API 与 Python 后端服务通信：

1. 启动 Python 后端服务：
   ```bash
   python main.py --mode=api
   ```

2. 服务监听端口：`http://localhost:5000`

3. 调用 `/run-pipeline` 端点执行采集流程

## 许可证

MIT License

## 注意事项

> ⚠️ **重要**：WinUI 3 项目需要在 Windows 环境下构建，因为 XAML 编译器是 Windows 特定的工具。
> 如果您在 macOS 或 Linux 上工作，请使用 Windows 虚拟机或远程桌面进行构建。