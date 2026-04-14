# AI新闻自动化系统 - 需求文档

## 1. 项目概述

### 1.1 项目背景
本项目是一个基于AI技术的新闻自动化系统，旨在实现从新闻采集、分析、生成到分发的全流程自动化。系统通过浏览器自动化技术采集多源新闻，利用大语言模型进行主题分析和文章生成，并支持多平台自动发布。

### 1.2 目标用户
- 内容运营团队
- 自媒体创作者
- 企业内容营销人员
- 新闻编辑人员

### 1.3 核心价值
- **效率提升**：自动化完成新闻采集到发布的全流程，节省90%以上的人力成本
- **内容质量**：基于AI生成高质量新闻文章，支持SEO优化
- **多平台分发**：一键发布到网站、微信公众号等多个平台
- **数据驱动**：完善的数据监测和分析能力

---

## 2. 功能需求

### 2.1 新闻采集模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-001 | 支持多新闻源采集（新浪新闻、网易新闻、今日头条、百度新闻等） | `config/news_sources.yaml` 配置的新闻源 |
| FR-002 | 支持按行业和主题关键词搜索 | `main.py` 命令行参数 `--industry`、`--topic` |
| FR-003 | 支持配置采集数量（10/20/30条） | `config/settings.yaml` collector.count_options |
| FR-004 | 支持时间范围过滤（默认24小时） | `config/settings.yaml` collector.time_range_hours |
| FR-005 | 自动去重（基于标题相似度） | `src/collector/browser_collector.py` _deduplicate方法 |
| FR-006 | 浏览器自动化采集，模拟真实用户行为 | `src/collector/browser_collector.py` BrowserNewsCollector |
| FR-007 | 支持浏览器连接池复用，提升性能 | `src/collector/browser_collector.py` BrowserPool |

### 2.2 新闻分析模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-008 | 自动分析新闻内容，提炼核心主题 | `src/collector/analyzer.py` |
| FR-009 | 支持配置提炼主题数量（3/5/8个） | `config/settings.yaml` generator.theme_options |
| FR-010 | 分析新闻热度评分 | `src/collector/analyzer.py` |
| FR-011 | 关联相关新闻到对应主题 | `src/generator/article_writer.py` generate_article方法 |

### 2.3 文章生成模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-012 | 根据主题和源新闻自动生成新闻文章 | `src/generator/article_writer.py` ArticleWriter |
| FR-013 | 支持配置文章字数范围（800-1500字） | `config/settings.yaml` generator.article_min_words/max_words |
| FR-014 | 自动生成SEO关键词（最多15个） | `src/generator/article_writer.py` _generate_keywords方法 |
| FR-015 | 自动生成文章摘要（50-100字） | `src/generator/article_writer.py` _generate_summary方法 |
| FR-016 | 自动生成配图描述（用于AI绘图） | `src/generator/article_writer.py` _generate_image_description方法 |
| FR-017 | 支持LLM提供商配置（ollama/openai） | `config/settings.yaml` llm.provider |

### 2.4 配图生成模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-018 | 根据文章内容自动生成配图 | `src/generator/image_generator.py` |
| FR-019 | 支持本地SD和API两种生成方式 | `config/settings.yaml` generator.image_generation_method |
| FR-020 | 配图自动保存到本地目录 | `data/images/` 目录结构 |

### 2.5 内容分发模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-021 | 支持发布到自有官网 | `src/distributor/website_publisher.py` |
| FR-022 | 支持发布到微信公众号 | `src/distributor/wechat_publisher.py` |
| FR-023 | 支持发布前人工审核 | `config/settings.yaml` distributor.require_review |
| FR-024 | 支持配置发布间隔（避免被封） | `config/settings.yaml` distributor.publish_interval |
| FR-025 | 批量分发多篇文章 | `src/distributor/distributor.py` batch_distribute方法 |

### 2.6 数据监测模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-026 | 定期检查系统状态 | `src/monitor/data_monitor.py` |
| FR-027 | 支持配置监测间隔（默认60分钟） | `config/settings.yaml` monitor.check_interval |
| FR-028 | 支持数据保留期限配置（默认90天） | `config/settings.yaml` monitor.data_retention_days |

### 2.7 数据管理模块

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-029 | 本地SQLite数据库存储 | `src/utils/db.py` |
| FR-030 | 采集新闻数据持久化 | `src/utils/db.py` save_collected_news |
| FR-031 | 生成文章数据持久化 | `src/utils/db.py` save_generated_article |
| FR-032 | 发布记录持久化 | `data/export/` 目录结构 |
| FR-033 | 数据导出功能（JSON/Markdown格式） | `src/utils/exporter.py` |

### 2.8 用户界面需求

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| FR-034 | Web管理后台界面 | `web/` 目录结构 |
| FR-035 | 命令行接口支持 | `main.py` argparse命令行参数 |
| FR-036 | 支持启动Web服务（指定端口） | `main.py` run_web_server函数 |

---

## 3. 非功能需求

### 3.1 性能需求

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| NFR-001 | 采集超时时间30秒 | `config/settings.yaml` collector.timeout |
| NFR-002 | 采集重试次数3次 | `config/settings.yaml` collector.retry_times |
| NFR-003 | 最大并发采集数3个源 | `src/collector/browser_collector.py` asyncio.Semaphore(3) |

### 3.2 安全性需求

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| NFR-004 | API密钥和敏感配置加密存储 | `.env` 文件管理 |
| NFR-005 | 浏览器采集模拟真实用户（UA伪装） | `src/collector/browser_collector.py` user_agent配置 |
| NFR-006 | 防止被反爬机制检测 | 浏览器参数配置（disable-blink-features等） |

### 3.3 兼容性需求

| 需求编号 | 需求描述 | 需求来源 |
| :--- | :--- | :--- |
| NFR-007 | 支持Windows操作系统 | `WINDOWS_SETUP.md` |
| NFR-008 | 支持Python 3.12+ | `venv/` Python版本 |
| NFR-009 | 支持多种LLM提供商（ollama/openai） | `config/settings.yaml` llm.provider |

---

## 4. 业务流程

### 4.1 完整自动化流程

```
[启动] → [1.采集新闻] → [2.分析主题] → [3.生成文章] → [4.生成配图] → [5.分发发布] → [结束]
           ↓              ↓              ↓              ↓              ↓
         浏览器采集     LLM分析       LLM写作       AI绘图        多平台发布
         多源并发       主题提炼       SEO优化       配图生成        间隔控制
```

### 4.2 各步骤详细说明

| 步骤 | 功能描述 | 输出 |
| :--- | :--- | :--- |
| 1. 采集 | 按行业/主题搜索多个新闻源，去重过滤 | 新闻列表（标题、摘要、来源、时间） |
| 2. 分析 | LLM分析新闻内容，提炼核心主题 | 主题列表（主题名称、描述、关联新闻） |
| 3. 生成 | 根据主题和源新闻生成文章，自动提取关键词和摘要 | 文章数据（标题、正文、关键词、摘要） |
| 4. 配图 | 根据文章内容生成配图描述并调用AI绘图 | 配图文件路径 |
| 5. 分发 | 发布到指定平台（网站、微信公众号等） | 发布结果统计 |

---

## 5. 数据结构

### 5.1 新闻数据结构

| 字段名 | 类型 | 说明 | 来源 |
| :--- | :--- | :--- | :--- |
| id | int | 主键ID | 数据库自动生成 |
| title | str | 新闻标题 | 采集结果 |
| url | str | 新闻链接 | 采集结果 |
| summary | str | 新闻摘要 | 采集结果 |
| source | str | 来源名称 | 采集结果 |
| publish_time | datetime | 发布时间 | 采集结果 |
| collected_at | datetime | 采集时间 | 系统生成 |
| industry | str | 所属行业 | 用户输入 |
| topic_keyword | str | 搜索关键词 | 用户输入 |

### 5.2 主题数据结构

| 字段名 | 类型 | 说明 | 来源 |
| :--- | :--- | :--- | :--- |
| id | int | 主键ID | 数据库自动生成 |
| theme | str | 主题名称 | LLM生成 |
| description | str | 主题描述 | LLM生成 |
| related_news_ids | list | 关联新闻ID列表 | LLM分析 |
| created_at | datetime | 创建时间 | 系统生成 |

### 5.3 文章数据结构

| 字段名 | 类型 | 说明 | 来源 |
| :--- | :--- | :--- | :--- |
| id | int | 主键ID | 数据库自动生成 |
| theme_id | int | 关联主题ID | 外键关联 |
| title | str | 文章标题 | LLM生成 |
| content | str | 文章正文 | LLM生成 |
| summary | str | 文章摘要 | LLM生成 |
| keywords | json | SEO关键词列表 | LLM生成 |
| image_description | str | 配图描述 | LLM生成 |
| image_path | str | 配图路径 | 图片生成 |
| status | str | 状态（draft/published） | 系统状态 |
| created_at | datetime | 创建时间 | 系统生成 |

---

## 6. 配置说明

### 6.1 配置文件清单

| 配置文件 | 说明 | 状态 |
| :--- | :--- | :--- |
| `config/settings.yaml` | 全局配置（LLM、采集、生成、分发、监测） | 必需 |
| `config/news_sources.yaml` | 新闻源配置（名称、类型、URL、选择器） | 必需 |
| `config/platforms.yaml` | 发布平台配置（网站、微信公众号） | 必需 |
| `.env` | 环境变量（敏感信息：API密钥等） | 必需 |

### 6.2 行业配置

支持的行业列表（来自 `config/settings.yaml`）：
- 科技
- 财经
- 医疗健康
- 教育
- 体育
- 娱乐
- 社会
- 国际
- 人力资源服务

---

## 7. 使用场景

### 7.1 场景一：命令行模式执行完整流程

```bash
python main.py run --industry "科技" --topic "人工智能" --count 10 --auto-publish
```

### 7.2 场景二：启动Web管理后台

```bash
python main.py web --port 8080
```

### 7.3 场景三：定时任务自动运行

通过定时任务（如cron）定期执行，实现每日自动新闻更新。