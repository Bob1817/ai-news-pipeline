# AI 新闻自动化系统 - Windows 安装指南

## 快速开始

### 方式一：一键启动（推荐）

1. **双击运行** `start_windows.bat`
2. 脚本将自动完成以下操作：
   - 检查 Python 环境
   - 创建虚拟环境
   - 安装所有依赖
   - 安装 Playwright 浏览器
3. Web 管理后台将自动启动

### 方式二：命令行启动

```batch
:: 1. 双击 start_windows.bat 完成初始化
:: 2. 打开命令行，进入项目目录
:: 3. 启动 Web 服务
python main.py web --port 8080
```

### 方式三：快速采集

```batch
:: 双击 quick_run.bat 使用默认参数采集
:: 或自定义参数
quick_run.bat 科技 人工智能 20
```

---

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本（推荐 3.12）
- **内存**: 至少 4GB
- **网络**: 需要访问互联网下载依赖和新闻源

---

## 手动安装步骤

### 1. 安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.12.x 安装程序
3. 运行安装程序，**务必勾选** "Add Python to PATH"
4. 验证安装：
   ```batch
   python --version
   ```

### 2. 安装项目依赖

```batch
:: 创建虚拟环境
python -m venv venv

:: 激活虚拟环境
venv\Scripts\activate.bat

:: 安装依赖
pip install -r requirements.txt

:: 安装 Playwright 浏览器
playwright install chromium
```

### 3. 启动服务

```batch
:: 启动 Web 管理后台
python main.py web --port 8080
```

---

## 常见问题

### Q1: 运行时报错 "Python 未找到"

**解决方案**:
1. 确认已安装 Python 3.10+
2. 安装时勾选 "Add Python to PATH"
3. 重启命令行窗口

### Q2: 依赖安装失败

**解决方案**:
```batch
:: 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: Playwright 浏览器安装失败

**解决方案**:
```batch
:: 手动安装
venv\Scripts\activate.bat
playwright install chromium
playwright install-deps chromium
```

### Q4: 端口 8080 被占用

**解决方案**:
```batch
:: 使用其他端口
python main.py web --port 8081
```

---

## 配置说明

### 1. 配置 LLM

编辑 `config/settings.yaml`:

```yaml
llm:
  provider: "ollama"  # 或 "openai"
  model: "qwen2:7b"
  api_url: ""  # OpenAI 兼容 API 地址
  api_key: ""  # API Key
```

### 2. 配置新闻源

编辑 `config/news_sources.yaml`:

```yaml
sources:
  - name: "示例新闻源"
    type: "browser"
    search_url: "https://example.com/search?q={keyword}"
    selectors:
      list: ".result-item"
      title: "a.title"
      summary: ".summary"
      time: ".time"
```

### 3. 配置发布平台

编辑 `config/platforms.yaml` 和 `config/settings.yaml`

---

## 使用说明

### Web 管理后台

访问 http://localhost:8080

1. **采集新闻**: 选择行业和主题，点击采集
2. **分析主题**: 选择新闻，点击分析提炼主题
3. **生成文章**: 选择主题，点击生成文章
4. **发布文章**: 选择文章，选择平台发布

### 命令行模式

```batch
:: 完整流程
python main.py run --industry "科技" --topic "人工智能" --count 10 --auto-publish

:: 仅采集不发布
python main.py run --industry "财经" --count 20
```

---

## 项目结构

```
ai-news-pipeline/
├── config/              # 配置文件
│   ├── settings.yaml    # 全局配置
│   ├── news_sources.yaml # 新闻源配置
│   └── platforms.yaml   # 发布平台配置
├── src/                 # 源代码
│   ├── collector/       # 采集模块
│   ├── generator/       # 生成模块
│   ├── distributor/     # 分发模块
│   ├── monitor/         # 监控模块
│   └── utils/           # 工具模块
├── web/                 # Web 管理后台
├── data/                # 数据存储
├── tests/               # 测试文件
├── main.py              # 主入口
├── requirements.txt     # 依赖列表
├── start_windows.bat    # Windows 启动脚本
├── quick_run.bat        # 快速采集脚本
└── README.md            # 项目说明
```

---

## 技术支持

- 项目地址：[GitHub](https://github.com/your-repo/ai-news-pipeline)
- 问题反馈：[Issues](https://github.com/your-repo/ai-news-pipeline/issues)
