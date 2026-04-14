# GitHub 上传与构建指南

## 步骤 1：创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 **+** 号，选择 **New repository**
3. 填写仓库信息：
   - **Repository name**: `ai-news-pipeline`
   - **Description**: AI新闻自动化系统 - 基于WinUI 3的桌面端应用
   - **Visibility**: 选择 Public 或 Private
   - 勾选 **Add a README file**（可选）
4. 点击 **Create repository**

## 步骤 2：上传项目到 GitHub

### 方法一：使用 Git 命令行

```bash
# 初始化 Git 仓库
cd /path/to/ai-news-pipeline
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit: AI新闻自动化系统 WinUI 3 版本"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-username/ai-news-pipeline.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 方法二：使用 GitHub Desktop

1. 下载并安装 [GitHub Desktop](https://desktop.github.com)
2. 打开 GitHub Desktop
3. 点击 **File** -> **Add Local Repository**
4. 选择项目目录 `/path/to/ai-news-pipeline`
5. 点击 **Publish repository**
6. 选择目标仓库或创建新仓库
7. 点击 **Publish**

## 步骤 3：配置 GitHub Actions

### 启用 Actions

1. 进入你的 GitHub 仓库
2. 点击顶部导航栏的 **Actions**
3. GitHub 会自动检测到 `.github/workflows/build-winui.yml` 文件
4. 点击 **Enable workflow**

### 手动触发构建

1. 在 **Actions** 页面
2. 选择左侧的 **Build WinUI Application**
3. 点击 **Run workflow**
4. 选择分支（main 或 master）
5. 点击 **Run workflow**

## 步骤 4：查看构建结果

### 查看工作流状态

1. 进入 **Actions** 页面
2. 点击正在运行或已完成的工作流
3. 点击 **build** 任务查看详细日志

### 下载构建产物

#### 方式 1：从工作流结果下载

1. 进入完成的工作流
2. 向下滚动到 **Artifacts** 部分
3. 点击 `AI新闻自动化系统` 下载压缩包

#### 方式 2：从 Release 下载

当推送到 main/master 分支时，工作流会自动创建 Release：

1. 进入仓库的 **Releases** 页面
2. 找到最新的 Release（如 `v1.0.0`）
3. 下载 `AI新闻自动化系统_v1.0.0_win-x64.zip`

## 步骤 5：运行应用

### 在 Windows 上运行

1. 下载并解压 `AI新闻自动化系统_v1.0.0_win-x64.zip`
2. 双击 `start.bat` 或 `AINewsPipeline.WinUI.exe`
3. 应用启动后，配置 LLM 参数和发布平台

## GitHub Actions 配置说明

### 工作流触发条件

| 触发方式 | 说明 |
|----------|------|
| `push` | 推送到 main 或 master 分支时触发 |
| `pull_request` | 创建或更新 Pull Request 时触发 |
| `workflow_dispatch` | 手动触发 |

### 构建步骤

1. **Setup .NET**: 安装 .NET 8 SDK
2. **Install Windows App SDK**: 安装 WinUI 运行时
3. **Restore dependencies**: 还原 NuGet 依赖
4. **Build WinUI Application**: 编译并发布应用
5. **Create directory structure**: 创建必要的目录
6. **Copy configuration files**: 复制配置文件
7. **Create start script**: 创建启动脚本
8. **Create zip archive**: 打包成 ZIP 文件
9. **Upload artifact**: 上传构建产物
10. **Create Release**: （仅 push 到主分支时）创建 GitHub Release

### 环境变量

| 变量 | 说明 |
|------|------|
| `GITHUB_TOKEN` | GitHub 自动提供的访问令牌，用于创建 Release |

## 故障排除

### 构建失败

1. 检查工作流日志，查看具体错误信息
2. 常见问题：
   - **NuGet 包版本冲突**: 检查 `csproj` 文件中的包版本
   - **Windows App SDK 安装失败**: 确保使用正确的下载链接
   - **路径问题**: 确保项目结构正确

### Release 未创建

1. 确保推送的分支是 `main` 或 `master`
2. 检查工作流条件是否满足
3. 确保 `GITHUB_TOKEN` 具有足够的权限

### 下载的文件无法运行

1. 确保解压完整
2. 检查是否有杀毒软件拦截
3. 确保 Windows 版本 >= 10.0.17763

## 项目结构

```
ai-news-pipeline/
├── .github/
│   └── workflows/
│       └── build-winui.yml    # GitHub Actions 配置
├── WinUI/                     # WinUI 3 项目
│   ├── AINewsPipeline.WinUI/
│   ├── AINewsPipeline.Package/
│   └── build.ps1
├── config/                    # 配置文件
├── resources/                 # 资源文件
├── src/                       # Python 后端代码
├── README.md
└── GITHUB_GUIDE.md            # 本文件
```

## 注意事项

1. **仓库大小**: 确保 `.gitignore` 文件排除了 `bin/`、`obj/`、`logs/` 等目录
2. **敏感信息**: 不要将 API 密钥、密码等敏感信息提交到仓库
3. **版本管理**: 使用语义化版本控制（如 v1.0.0, v1.0.1）

## 参考链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [WinUI 3 文档](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)
- [.NET 发布文档](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish)