# 测试运行指南

## 快速开始

### 在 macOS/Linux 上运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_db.py -v
pytest tests/test_utils.py -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
open coverage/index.html
```

### 在 Windows 上运行测试

```batch
:: 激活虚拟环境
venv\Scripts\activate.bat

:: 运行所有测试
pytest tests/ -v

:: 查看覆盖率
pytest tests/ --cov=src --cov-report=html
start coverage/index.html
```

## 测试覆盖范围

| 测试文件 | 测试内容 | 状态 |
|---------|---------|------|
| `test_db.py` | 数据库操作测试 | ✅ 通过 |
| `test_utils.py` | 工具函数测试 | ✅ 通过 |

### 测试用例详情

#### test_db.py - 数据库测试

- `TestCollectedNews::test_save_collected_news` - 保存采集新闻
- `TestCollectedNews::test_query_collected_news` - 查询采集新闻
- `TestGeneratedArticle::test_save_generated_article` - 保存生成文章
- `TestGeneratedArticle::test_update_article_status` - 更新文章状态
- `TestDatabaseConnection::test_database_url_resolution` - 数据库 URL 解析
- `TestDatabaseConnection::test_init_db` - 数据库初始化

#### test_utils.py - 工具函数测试

- `TestLogger::test_logger_init` - 日志初始化
- `TestTimeParser::test_parse_relative_time` - 相对时间解析
- `TestTimeParser::test_parse_absolute_time` - 绝对时间解析
- `TestDeduplicate::test_deduplicate_news` - 新闻去重
- `TestConfigLoader::test_load_settings` - 配置加载

## 添加新测试

### 1. 创建测试文件

在 `tests/` 目录下创建新的测试文件，如 `test_collector.py`

### 2. 编写测试用例

```python
import pytest

class TestExample:
    def test_example(self):
        assert True
```

### 3. 运行测试

```bash
pytest tests/test_collector.py -v
```

## 测试配置

项目使用 `pytest.ini` 进行配置：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short -s
```

## 常见问题

### Q: 测试失败怎么办？

A: 检查错误信息，确认是测试问题还是代码问题。如果是代码问题，修复后重新运行测试。

### Q: 如何只运行失败的测试？

A: 使用 `--lf` 参数：
```bash
pytest tests/ --lf -v
```

### Q: 如何生成覆盖率报告？

A: 使用 `--cov` 参数：
```bash
pytest tests/ --cov=src --cov-report=html
```
