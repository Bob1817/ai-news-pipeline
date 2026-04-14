# AI新闻自动化系统 - Windows桌面端技术文档

## 1. 技术方案概述

### 1.1 项目背景
本技术文档针对AI新闻自动化系统的Windows桌面端应用进行设计。原项目为Python命令行/Web服务模式，现需要开发一个可视化桌面端应用，提供更好的用户体验和操作便捷性。

### 1.2 技术选型

| 分类 | 技术 | 版本 | 选型理由 |
| :--- | :--- | :--- | :--- |
| 语言 | Python | 3.12+ | 原项目已有成熟的Python代码库，无需重构 |
| GUI框架 | PyQt6 | 6.6+ | 成熟稳定，跨平台支持好，原生Windows风格，性能优秀 |
| 浏览器自动化 | Playwright | 1.40+ | 原项目已使用，支持无头/有头模式切换 |
| 数据库 | SQLite | 3.45+ | 轻量级嵌入式数据库，无需额外服务，适合桌面应用 |
| 图标资源 | Qt SVG/Font Awesome | 6.5+ | 矢量图标，缩放不失真 |
| 打包工具 | PyInstaller | 6.5+ | 成熟的Python打包工具，支持单文件和目录模式 |

### 1.3 核心设计原则

1. **架构清晰**：采用分层架构，分离UI层、业务逻辑层、数据层
2. **异步处理**：长时间任务（采集、生成、发布）使用异步线程，避免UI阻塞
3. **响应式设计**：支持不同分辨率屏幕自适应
4. **错误处理**：完善的异常捕获和用户友好的错误提示
5. **可扩展性**：模块化设计，便于后续功能扩展

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI 层 (PyQt6)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐   │
│  │ 主窗口      │ │ 采集配置    │ │ 文章管理    │ │ 设置    │   │
│  │ MainWindow  │ │ CollectTab  │ │ ArticleTab  │ │ Setting │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 信号/槽
┌──────────────────────────▼──────────────────────────────────────┐
│                   业务逻辑层 (Business Layer)                   │
│  ┌────────────────┐ ┌────────────────┐ ┌─────────────────────┐  │
│  │ TaskManager    │ │ PipelineRunner │ │ ConfigManager       │  │
│  │ 任务管理       │ │ 流程执行器     │ │ 配置管理            │  │
│  └────────────────┘ └────────────────┘ └─────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 调用
┌──────────────────────────▼──────────────────────────────────────┐
│                   核心模块层 (Core Modules)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │ Collector   │ │ Analyzer    │ │ Generator   │ │ Distributor││
│  │ 新闻采集    │ │ 主题分析    │ │ 文章生成    │ │ 内容分发   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 存储/读取
┌──────────────────────────▼──────────────────────────────────────┐
│                        数据层 (Data Layer)                      │
│              SQLite数据库 + 文件系统存储                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ news_pipeline.db (新闻/主题/文章/发布记录)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ data/images/ (配图文件)                                 │   │
│  │ data/export/ (导出文件)                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责说明

| 模块 | 职责 | 说明 |
| :--- | :--- | :--- |
| UI层 | 用户交互界面 | PyQt6实现，包含主窗口和多个功能标签页 |
| TaskManager | 异步任务管理 | 管理采集、生成、发布等耗时任务的线程 |
| PipelineRunner | 流程编排 | 编排采集→分析→生成→配图→分发的完整流程 |
| ConfigManager | 配置管理 | 加载/保存YAML配置文件和环境变量 |
| Collector | 新闻采集 | 调用原项目browser_collector，支持浏览器自动化采集 |
| Analyzer | 主题分析 | 调用原项目analyzer，使用LLM分析新闻提炼主题 |
| Generator | 文章生成 | 调用原项目article_writer和image_generator |
| Distributor | 内容分发 | 调用原项目distributor，支持网站和微信公众号发布 |
| Database | 数据存储 | SQLite数据库操作封装 |

---

## 3. 目录结构

```
ai-news-pipeline/
├── src/                              # 核心源代码目录
│   ├── ui/                           # UI层代码
│   │   ├── __init__.py
│   │   ├── main_window.py            # 主窗口
│   │   ├── collect_tab.py            # 采集配置标签页
│   │   ├── article_tab.py            # 文章管理标签页
│   │   ├── publish_tab.py            # 发布管理标签页
│   │   ├── settings_dialog.py        # 设置对话框
│   │   └── task_progress.py          # 任务进度组件
│   ├── business/                     # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── task_manager.py           # 任务管理
│   │   ├── pipeline_runner.py        # 流程执行器
│   │   └── config_manager.py         # 配置管理
│   ├── collector/                    # 采集模块(复用原代码)
│   ├── generator/                    # 生成模块(复用原代码)
│   ├── distributor/                  # 分发模块(复用原代码)
│   ├── monitor/                      # 监测模块(复用原代码)
│   └── utils/                        # 工具模块(复用原代码)
├── resources/                        # 资源文件
│   ├── icons/                        # 图标资源
│   │   ├── app.ico                   # 应用图标
│   │   ├── collect.svg               # 采集图标
│   │   ├── generate.svg              # 生成图标
│   │   ├── publish.svg               # 发布图标
│   │   └── settings.svg              # 设置图标
│   └── styles/                       # 样式文件
│       └── main.qss                  # 全局样式
├── config/                           # 配置文件(复用)
├── data/                             # 数据存储(复用)
├── logs/                             # 日志文件
├── main.py                           # 桌面端主入口
├── requirements.txt                  # 依赖清单
└── pyinstaller.spec                  # PyInstaller打包配置
```

---

## 4. 关键类设计

### 4.1 主窗口类 (MainWindow)

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| central_widget | QWidget | 中央容器 |
| tab_widget | QTabWidget | 标签页容器 |
| status_bar | QStatusBar | 状态栏 |
| collect_tab | CollectTab | 采集配置标签页 |
| article_tab | ArticleTab | 文章管理标签页 |
| publish_tab | PublishTab | 发布管理标签页 |
| task_manager | TaskManager | 任务管理器实例 |

| 方法 | 功能说明 |
| :--- | :--- |
| __init__() | 初始化主窗口，创建标签页 |
| setup_ui() | 设置UI布局 |
| setup_menu() | 设置菜单栏 |
| setup_status_bar() | 设置状态栏 |
| on_task_start() | 任务开始时更新状态栏 |
| on_task_progress() | 任务进度更新时显示进度 |
| on_task_complete() | 任务完成时更新状态 |

### 4.2 任务管理器类 (TaskManager)

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| thread_pool | QThreadPool | Qt线程池 |
| active_tasks | dict | 活跃任务字典 |
| progress_signal | Signal | 进度信号 |
| complete_signal | Signal | 完成信号 |
| error_signal | Signal | 错误信号 |

| 方法 | 功能说明 |
| :--- | :--- |
| submit_task(task_type, params) | 提交异步任务 |
| run_collection(params) | 执行采集任务 |
| run_generation(params) | 执行生成任务 |
| run_publish(params) | 执行发布任务 |
| run_full_pipeline(params) | 执行完整流程 |
| cancel_task(task_id) | 取消任务 |

### 4.3 流程执行器类 (PipelineRunner)

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| collector | BrowserNewsCollector | 采集器实例 |
| analyzer | NewsAnalyzer | 分析器实例 |
| writer | ArticleWriter | 文章生成器实例 |
| image_gen | ImageGenerator | 配图生成器实例 |
| distributor | Distributor | 分发器实例 |

| 方法 | 功能说明 |
| :--- | :--- |
| run_full_pipeline(industry, topic, count, theme_count, platforms, auto_publish) | 执行完整流程 |
| run_collection(industry, topic, count) | 执行采集 |
| run_analysis(news_list, theme_count) | 执行分析 |
| run_generation(themes, news_list) | 执行文章生成 |
| run_image_generation(articles) | 执行配图生成 |
| run_distribution(articles, platforms) | 执行分发 |

### 4.4 配置管理类 (ConfigManager)

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| settings | dict | 全局设置 |
| news_sources | dict | 新闻源配置 |
| platforms | dict | 发布平台配置 |
| env_vars | dict | 环境变量 |

| 方法 | 功能说明 |
| :--- | :--- |
| load_settings() | 加载settings.yaml |
| load_news_sources() | 加载news_sources.yaml |
| load_platforms() | 加载platforms.yaml |
| load_env() | 加载.env文件 |
| save_settings(settings) | 保存设置 |
| get_industries() | 获取行业列表 |
| get_platforms() | 获取平台列表 |

---

## 5. UI设计

### 5.1 主窗口布局

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 【AI新闻自动化系统】  [文件] [设置] [帮助]               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ┌─────────┬─────────┬─────────┐                        │  │
│  │  │ 采集    │ 文章管理 │ 发布    │                        │  │
│  │  └────┬────┴────┬────┴────┬────┘                        │  │
│  │       │         │         │                              │  │
│  │  ┌────▼────┐                                            │  │
│  │  │         │                                            │  │
│  │  │   采集  │                                            │  │
│  │  │   配置  │                                            │  │
│  │  │   区域  │                                            │  │
│  │  │         │                                            │  │
│  │  └─────────┘                                            │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 进度条: [████████████████████████] 100%         │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 状态: 就绪 | 日志: 无                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 采集配置标签页 (CollectTab)

| 控件 | 类型 | 功能 |
| :--- | :--- | :--- |
| industry_combo | QComboBox | 行业选择下拉框 |
| topic_edit | QLineEdit | 主题关键词输入框 |
| count_spin | QSpinBox | 采集数量选择(10/20/30) |
| theme_count_spin | QSpinBox | 主题数量选择(3/5/8) |
| time_range_combo | QComboBox | 时间范围选择 |
| start_btn | QPushButton | 开始采集按钮 |
| progress_bar | QProgressBar | 采集进度条 |
| news_table | QTableWidget | 采集结果列表 |

### 5.3 文章管理标签页 (ArticleTab)

| 控件 | 类型 | 功能 |
| :--- | :--- | :--- |
| article_table | QTableWidget | 文章列表 |
| title_label | QLabel | 文章标题显示 |
| content_text | QTextEdit | 文章内容编辑区 |
| keywords_label | QLabel | 关键词显示 |
| image_label | QLabel | 配图预览 |
| edit_btn | QPushButton | 编辑按钮 |
| delete_btn | QPushButton | 删除按钮 |
| export_btn | QPushButton | 导出按钮 |

### 5.4 设置对话框 (SettingsDialog)

| 控件 | 类型 | 功能 |
| :--- | :--- | :--- |
| llm_provider_combo | QComboBox | LLM提供商选择 |
| model_edit | QLineEdit | 模型名称输入 |
| api_url_edit | QLineEdit | API地址输入 |
| api_key_edit | QLineEdit | API密钥输入(密码模式) |
| auto_image_check | QCheckBox | 自动生成配图开关 |
| min_words_spin | QSpinBox | 最小字数设置 |
| max_words_spin | QSpinBox | 最大字数设置 |
| require_review_check | QCheckBox | 发布审核开关 |
| save_btn | QPushButton | 保存按钮 |
| cancel_btn | QPushButton | 取消按钮 |

---

## 6. 数据库设计

### 6.1 表结构

#### 表：collected_news (采集新闻)

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| title | TEXT | NOT NULL | 新闻标题 |
| url | TEXT | | 新闻链接 |
| summary | TEXT | | 新闻摘要 |
| source | TEXT | | 来源名称 |
| publish_time | DATETIME | | 发布时间 |
| collected_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 采集时间 |
| industry | TEXT | | 所属行业 |
| topic_keyword | TEXT | | 搜索关键词 |

#### 表：generated_themes (生成主题)

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| theme | TEXT | NOT NULL | 主题名称 |
| description | TEXT | | 主题描述 |
| related_news_ids | TEXT | | 关联新闻ID(JSON数组) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 表：generated_articles (生成文章)

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| theme_id | INTEGER | FOREIGN KEY | 关联主题ID |
| title | TEXT | NOT NULL | 文章标题 |
| content | TEXT | NOT NULL | 文章正文 |
| summary | TEXT | | 文章摘要 |
| keywords | TEXT | | SEO关键词(JSON数组) |
| image_description | TEXT | | 配图描述 |
| image_path | TEXT | | 配图路径 |
| status | TEXT | DEFAULT 'draft' | 状态(draft/published) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 表：publish_records (发布记录)

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| article_id | INTEGER | FOREIGN KEY | 关联文章ID |
| platform | TEXT | NOT NULL | 发布平台 |
| status | TEXT | NOT NULL | 发布状态(success/failed) |
| response_data | TEXT | | 平台响应数据 |
| published_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 发布时间 |

---

## 7. 接口设计

### 7.1 内部模块接口

#### 7.1.1 TaskManager接口

| 方法名 | 参数 | 返回值 | 说明 |
| :--- | :--- | :--- | :--- |
| submit_task | task_type: str, params: dict | task_id: str | 提交异步任务 |
| cancel_task | task_id: str | bool | 取消任务 |

#### 7.1.2 PipelineRunner接口

| 方法名 | 参数 | 返回值 | 说明 |
| :--- | :--- | :--- | :--- |
| run_full_pipeline | industry: str, topic: str, count: int, theme_count: int, platforms: list, auto_publish: bool | dict | 执行完整流程 |
| run_collection | industry: str, topic: str, count: int | list | 执行采集 |
| run_analysis | news_list: list, theme_count: int | tuple | 执行分析 |
| run_generation | themes: list, news_list: list | list | 执行文章生成 |
| run_image_generation | articles: list | list | 执行配图生成 |
| run_distribution | articles: list, platforms: list | dict | 执行分发 |

#### 7.1.3 ConfigManager接口

| 方法名 | 参数 | 返回值 | 说明 |
| :--- | :--- | :--- | :--- |
| load_settings | 无 | dict | 加载全局设置 |
| save_settings | settings: dict | bool | 保存全局设置 |
| get_industries | 无 | list | 获取行业列表 |
| get_platforms | 无 | list | 获取平台列表 |

---

## 8. 部署与打包

### 8.1 依赖安装

```bash
pip install pyqt6 playwright python-dotenv pyyaml loguru beautifulsoup4
```

### 8.2 浏览器驱动安装

```bash
playwright install chromium
```

### 8.3 PyInstaller打包配置

**pyinstaller.spec** 关键配置：

```python
a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('config/', 'config/'),
        ('resources/', 'resources/'),
        ('data/', 'data/'),
    ],
    hiddenimports=[
        'playwright',
        'playwright._impl._api_types',
        'pyyaml',
        'loguru',
        'beautifulsoup4',
    ],
    ...
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI新闻自动化系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关闭控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico'
)
```

### 8.4 打包命令

```bash
pyinstaller pyinstaller.spec
```

### 8.5 打包产物

```
dist/
└── AI新闻自动化系统/
    ├── AI新闻自动化系统.exe    # 主程序
    ├── config/                  # 配置文件目录
    ├── resources/               # 资源文件目录
    ├── data/                    # 数据存储目录
    └── logs/                    # 日志目录
```

---

## 9. 安全性考虑

### 9.1 敏感信息保护

1. **API密钥加密存储**：使用`.env`文件存储敏感信息，不提交版本控制
2. **密码输入框**：使用QLineEdit的密码模式，输入时显示掩码
3. **日志脱敏**：日志记录时过滤敏感信息

### 9.2 浏览器安全配置

1. **User-Agent伪装**：模拟真实浏览器UA
2. **反爬防护**：设置合理的请求间隔，避免被封IP
3. **无头模式**：默认使用无头模式，减少资源占用

### 9.3 数据安全

1. **本地数据库**：SQLite文件设置合适的权限
2. **数据备份**：支持一键导出数据
3. **定期清理**：自动清理过期数据（默认90天）

---

## 10. 性能优化

### 10.1 异步处理

1. **耗时任务异步化**：采集、生成、发布等任务使用QThreadPool异步执行
2. **UI线程隔离**：避免阻塞主线程，保持界面响应

### 10.2 资源管理

1. **浏览器连接池**：复用浏览器实例，减少启动开销
2. **图片缓存**：已生成的配图缓存到本地，避免重复生成

### 10.3 日志优化

1. **日志级别控制**：支持不同级别日志输出
2. **日志轮转**：定期清理旧日志文件