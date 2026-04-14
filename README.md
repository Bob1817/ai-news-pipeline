# AI 新闻自动化系统

一个基于 AI 的新闻自动化采集、分析和发布系统。支持多行业新闻采集、AI 主题分析、文章自动生成和多渠道发布。

## 功能特性

- **新闻采集**: 支持浏览器自动化采集和 API 采集两种方式
- **AI 分析**: 自动提炼新闻主题，智能分类
- **文章生成**: 基于 LLM 自动生成高质量文章
- **配图生成**: 支持本地 SD 或 API 生成配图
- **SEO 优化**: 自动优化关键词，提升搜索引擎排名
- **多渠道发布**: 支持网站后台和微信公众号发布
- **数据监控**: 实时监测文章表现数据
- **Web 管理**: 可视化的 Web 管理后台

## 快速开始

### Windows 系统

#### 方式一：一键启动（推荐）

1. 双击运行 `start_windows.bat`
2. 脚本将自动完成环境配置和依赖安装
3. Web 管理后台将自动启动

#### 方式二：快速采集

```batch
:: 双击运行
quick_run.bat

:: 或自定义参数
quick_run.bat 科技 人工智能 20
```

详细安装指南请参考 [WINDOWS_SETUP.md](./WINDOWS_SETUP.md)

### macOS/Linux 系统

```bash
# 1. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器
playwright install chromium

# 4. 启动 Web 管理后台
python main.py web --port 8080
```

## 项目结构

```
ai-news-pipeline/
├── config/              # 配置文件
│   ├── settings.yaml    # 全局配置
│   ├── news_sources.yaml # 新闻源配置
│   └── platforms.yaml   # 发布平台配置
├── src/                 # 源代码
│   ├── collector/       # 采集模块
│   │   ├── browser_collector.py  # 浏览器采集
│   │   ├── api_collector.py      # API 采集
│   │   └── analyzer.py           # 新闻分析
│   ├── generator/       # 生成模块
│   │   ├── article_writer.py     # 文章生成
│   │   ├── image_generator.py    # 配图生成
│   │   └── seo_optimizer.py      # SEO 优化
│   ├── distributor/     # 分发模块
│   │   ├── website_publisher.py  # 网站发布
│   │   └── wechat_publisher.py   # 微信发布
│   ├── monitor/         # 监控模块
│   └── utils/           # 工具模块
├── web/                 # Web 管理后台
├── data/                # 数据存储
├── tests/               # 测试文件
├── main.py              # 主入口
├── requirements.txt     # 依赖列表
├── start_windows.bat    # Windows 启动脚本
├── quick_run.bat        # 快速采集脚本
├── pytest.ini           # 测试配置
├── TESTING.md           # 测试指南
└── WINDOWS_SETUP.md     # Windows 安装指南
```

## 使用方法

### Web 管理后台

访问 http://localhost:8080

1. **采集新闻**: 选择行业和主题，点击采集
2. **分析主题**: 选择新闻，点击分析提炼主题
3. **生成文章**: 选择主题，点击生成文章
4. **发布文章**: 选择文章，选择平台发布

### 命令行模式

```bash
# 完整流程（采集 + 分析 + 生成 + 发布）
python main.py run --industry "科技" --topic "人工智能" --count 10 --auto-publish

# 仅采集
python main.py run --industry "财经" --count 20

# 启动 Web 服务
python main.py web --port 8080
```

## 配置说明

### 1. LLM 配置 (config/settings.yaml)

```yaml
llm:
  provider: "ollama"  # 或 "openai"
  model: "qwen2:7b"
  api_url: ""  # OpenAI 兼容 API 地址
  api_key: ""  # API Key
```

### 2. 新闻源配置 (config/news_sources.yaml)

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

### 3. 行业列表

在 `config/settings.yaml` 中配置：

```yaml
industries:
  - name: "科技"
    keywords: ["人工智能", "芯片", "5G"]
  - name: "财经"
    keywords: ["股市", "基金", "央行"]
```

## 测试

详细测试指南请参考 [TESTING.md](./TESTING.md)

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 系统要求

- **Python**: 3.10 或更高版本（推荐 3.12）
- **内存**: 至少 4GB
- **网络**: 需要访问互联网下载依赖和新闻源
- **浏览器**: Playwright 支持的现代浏览器

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
