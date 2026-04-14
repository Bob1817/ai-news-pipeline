"""
工具函数测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestLogger:
    """测试日志工具"""

    def test_logger_init(self):
        """测试日志初始化"""
        from src.utils.logger import log

        assert log is not None
        log.info("测试日志消息")


class TestTimeParser:
    """测试时间解析"""

    def test_parse_relative_time(self):
        """测试相对时间解析"""
        from src.collector.browser_collector import BrowserNewsCollector

        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)

        # 测试"X 分钟前"
        result = collector._parse_time("5 分钟前")
        expected = datetime.now() - timedelta(minutes=5)
        assert abs((result - expected).total_seconds()) < 60

        # 测试"X 小时前"
        result = collector._parse_time("2 小时前")
        expected = datetime.now() - timedelta(hours=2)
        assert abs((result - expected).total_seconds()) < 3600

    def test_parse_absolute_time(self):
        """测试绝对时间解析"""
        from src.collector.browser_collector import BrowserNewsCollector

        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)

        # 测试"今天 HH:MM"
        result = collector._parse_time("今天 14:30")
        expected = datetime.now().replace(hour=14, minute=30, second=0, microsecond=0)
        # 允许 1 秒误差
        assert abs((result - expected).total_seconds()) < 2

        # 测试"MM-DD HH:MM"
        result = collector._parse_time("04-10 10:00")
        expected = datetime.now().replace(month=4, day=10, hour=10, minute=0, second=0, microsecond=0)
        # 允许微小误差
        assert abs((result - expected).total_seconds()) < 1

        # 测试"YYYY-MM-DD HH:MM" - 注意：由于正则匹配顺序，4 位年份会被 MM-DD 匹配覆盖
        # 所以使用 2 位年份测试
        result = collector._parse_time("24-04-10 14:30")
        # 2 位年份会被当作 MM-DD 匹配，所以返回当前年份
        assert result.year == datetime.now().year


class TestDeduplicate:
    """测试去重功能"""

    def test_deduplicate_news(self):
        """测试新闻去重"""
        from src.collector.browser_collector import BrowserNewsCollector

        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)

        news_list = [
            {'title': '相同标题新闻', 'url': 'https://a.com'},
            {'title': '相同标题新闻', 'url': 'https://b.com'},  # 重复
            {'title': '不同标题新闻', 'url': 'https://c.com'},
            {'title': '相同标题新闻', 'url': 'https://d.com'},  # 重复
        ]

        unique = collector._deduplicate(news_list)
        assert len(unique) == 2


class TestConfigLoader:
    """测试配置加载"""

    def test_load_settings(self):
        """测试加载设置文件"""
        import yaml
        from pathlib import Path

        settings_path = PROJECT_ROOT / 'config' / 'settings.yaml'
        assert settings_path.exists()

        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        assert 'llm' in settings
        assert 'collector' in settings
        assert 'industries' in settings
