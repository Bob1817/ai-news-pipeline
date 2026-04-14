# AI 新闻自动化系统 - Windows 发布包说明

## 文件列表

```
ai-news-pipeline-windows/
├── config/                    # 配置文件
│   ├── settings.yaml          # 全局配置（需要配置 API 密钥）
│   ├── settings.yaml.example  # 配置示例
│   ├── news_sources.yaml      # 新闻源配置
│   └── platforms.yaml         # 发布平台配置
├── src/                       # 源代码
├── web/                       # Web 管理后台
├── data/                      # 数据存储（运行后生成）
├── logs/                      # 日志目录（运行后生成）
├── tests/                     # 测试文件
├── main.py                    # 主入口
├── requirements.txt           # Python 依赖列表
├── pytest.ini                 # 测试配置
├── README.md                  # 项目说明
├── WINDOWS_SETUP.md           # Windows 安装指南
├── TESTING.md                 # 测试指南
├── start_windows.bat          # 一键启动脚本
└── quick_run.bat              # 快速采集脚本
```

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本（推荐 3.12）
- **内存**: 至少 4GB
- **磁盘空间**: 约 2GB（包含 Playwright 浏览器）
- **网络**: 需要访问互联网下载依赖和新闻源

## 快速开始

### 1. 安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.12.x
3. 运行安装程序，**务必勾选** "Add Python to PATH"
4. 验证安装：打开命令提示符，输入 `python --version`

### 2. 解压并启动

1. 解压压缩包到任意目录（建议不要包含中文路径）
2. 双击 `start_windows.bat`
3. 等待自动安装完成（首次运行需要 5-10 分钟）
4. 浏览器自动打开 http://localhost:8080

## 配置说明

### 重要配置项

在 `config/settings.yaml` 中配置：

```yaml
llm:
  provider: "ollama"  # 或 "openai"
  model: "qwen2:7b"   # 或你的模型名称
  api_url: ""         # OpenAI 兼容 API 地址（如使用 OpenAI）
  api_key: ""         # API Key
```

### 使用 Ollama（推荐，免费）

1. 安装 Ollama: https://ollama.com/download/windows
2. 拉取模型：`ollama pull qwen2:7b`
3. 配置 `settings.yaml`:
   ```yaml
   llm:
     provider: "ollama"
     model: "qwen2:7b"
   ```

### 使用 OpenAI

1. 获取 API Key: https://platform.openai.com/api-keys
2. 配置 `settings.yaml`:
   ```yaml
   llm:
     provider: "openai"
     model: "gpt-3.5-turbo"
     api_url: "https://api.openai.com/v1"
     api_key: "sk-xxxxx"
   ```

## 使用方式

### Web 管理后台

访问 http://localhost:8080

1. **采集新闻**: 选择行业和主题，点击采集
2. **分析主题**: 选择新闻，点击分析提炼主题
3. **生成文章**: 选择主题，点击生成文章
4. **发布文章**: 选择文章，选择平台发布

### 命令行采集

```batch
:: 使用默认参数
quick_run.bat

:: 自定义参数
quick_run.bat 科技 人工智能 20
```

## 常见问题

### Q: 启动时提示 "Python 未找到"

A: 请确认已正确安装 Python 并添加到 PATH，重启命令行窗口后重试。

### Q: 依赖安装失败

A: 使用国内镜像源：
```batch
set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
start_windows.bat
```

### Q: Playwright 浏览器安装失败

A: 手动安装：
```batch
venv\Scripts\activate.bat
playwright install chromium
```

### Q: 端口 8080 被占用

A: 修改启动脚本中的端口号，或使用：
```batch
python main.py web --port 8081
```

## 技术支持

- 项目文档：README.md, WINDOWS_SETUP.md
- 测试指南：TESTING.md
- 问题反馈：查看 logs 目录下的日志文件

## 注意事项

1. **首次运行**需要下载 Playwright 浏览器（约 300MB），请耐心等待
2. **配置文件**中的 API 密钥需要自行配置才能使用 AI 功能
3. **数据存储**在 data 目录下，建议定期备份
4. **日志文件**在 logs 目录下，用于排查问题
