"""
测试 browser_collector.py 模块
包含: BrowserPool, BrowserNewsCollector
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from src.collector.browser_collector import BrowserPool, BrowserNewsCollector


class TestBrowserPool:
    """测试 BrowserPool 类"""

    @pytest.mark.asyncio
    async def test_get_instance_creates_singleton(self):
        """应该创建单例实例"""
        # 清除已有实例
        BrowserPool._instance = None
        BrowserPool._browser = None
        BrowserPool._context = None
        BrowserPool._pw = None
        
        with patch('playwright.async_api.async_playwright') as mock_pw:
            mock_playwright = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            instance1 = await BrowserPool.get_instance()
            instance2 = await BrowserPool.get_instance()
            
            assert instance1 is instance2
            
            # 清理
            await BrowserPool.close()

    @pytest.mark.asyncio
    async def test_close_cleans_resources(self):
        """应该正确清理资源"""
        BrowserPool._instance = None
        
        with patch('playwright.async_api.async_playwright') as mock_pw:
            mock_playwright = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            await BrowserPool.get_instance()
            await BrowserPool.close()
            
            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()

    def test_new_page_is_coroutine(self):
        """new_page 应该返回协程"""
        assert asyncio.iscoroutinefunction(BrowserPool.new_page)


class TestBrowserNewsCollector:
    """测试 BrowserNewsCollector 类"""

    def test_parse_time_minutes_ago(self):
        """应该解析 'X分钟前' 格式"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        now = datetime.now()
        result = collector._parse_time("10分钟前")
        
        # 应该在 10 分钟前
        assert (now - result).total_seconds() < 61

    def test_parse_time_hours_ago(self):
        """应该解析 'X小时前' 格式"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        now = datetime.now()
        result = collector._parse_time("2小时前")
        
        # 应该在 2 小时左右
        diff = now - result
        assert 1.9 * 3600 < diff.total_seconds() < 2.1 * 3600

    def test_parse_time_today(self):
        """应该解析 '今天 HH:MM' 格式"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        result = collector._parse_time("今天 14:30")
        
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_time_month_day(self):
        """应该解析 'MM-DD HH:MM' 格式"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        result = collector._parse_time("01-15 10:30")
        
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_time_full_format(self):
        """应该解析 'YYYY-MM-DD HH:MM:SS' 格式"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        result = collector._parse_time("2024-01-15 14:30:00")
        
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_time_empty_string(self):
        """应该对空字符串返回当前时间"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        now = datetime.now()
        result = collector._parse_time("")
        
        # 应该接近当前时间
        assert (now - result).total_seconds() < 1

    def test_parse_time_none(self):
        """应该对 None 返回当前时间"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        now = datetime.now()
        result = collector._parse_time(None)
        
        assert (now - result).total_seconds() < 1

    def test_parse_time_invalid_format(self):
        """应该对无效格式返回当前时间"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        now = datetime.now()
        result = collector._parse_time("无效时间格式")
        
        assert (now - result).total_seconds() < 1

    def test_deduplicate_removes_similar_titles(self):
        """应该去除相似标题"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        news_list = [
            {'title': '人工智能技术实现新突破', 'url': 'url1'},
            {'title': '人工智能技术 实现新突破！', 'url': 'url2'},  # 相似
            {'title': '5G网络覆盖全国', 'url': 'url3'}
        ]
        
        result = collector._deduplicate(news_list)
        
        # 应该只保留 2 条（第一条和第三条）
        assert len(result) == 2

    def test_deduplicate_skips_short_titles(self):
        """应该跳过过短标题（少于5字符）"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        news_list = [
            {'title': '短', 'url': 'url1'},
            {'title': '这是一条正常的新闻标题', 'url': 'url2'}
        ]
        
        result = collector._deduplicate(news_list)
        
        assert len(result) == 1
        assert result[0]['title'] == '这是一条正常的新闻标题'

    def test_deduplicate_handles_empty_title(self):
        """应该处理空标题"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        news_list = [
            {'title': '', 'url': 'url1'},
            {'title': '正常新闻', 'url': 'url2'}
        ]
        
        result = collector._deduplicate(news_list)
        
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_parse_news_item_basic(self):
        """应该正确解析新闻元素"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        # Mock BeautifulSoup 元素
        mock_item = MagicMock()
        mock_title = MagicMock()
        mock_title.get_text.return_value = "测试新闻标题"
        mock_title.get.return_value = "https://example.com/news"
        mock_item.select_one.return_value = mock_title
        
        selectors = {
            'title': 'a',
            'summary': '.summary',
            'time': '.time'
        }
        
        result = collector._parse_news_item(mock_item, selectors, "测试源")
        
        assert result is not None
        assert result['title'] == "测试新闻标题"
        assert result['source'] == "测试源"

    @pytest.mark.asyncio
    async def test_parse_news_item_missing_title(self):
        """应该对缺少标题的元素返回 None"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        mock_item = MagicMock()
        mock_item.select_one.return_value = None
        
        selectors = {'title': 'a'}
        
        result = collector._parse_news_item(mock_item, selectors, "测试源")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_news_item_truncates_long_title(self):
        """应该截断过长标题"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        mock_item = MagicMock()
        mock_title = MagicMock()
        mock_title.get_text.return_value = "x" * 600
        mock_title.get.return_value = "https://example.com"
        mock_item.select_one.return_value = mock_title
        
        selectors = {'title': 'a'}
        
        result = collector._parse_news_item(mock_item, selectors, "测试源")
        
        assert len(result['title']) <= 500

    @pytest.mark.asyncio
    async def test_parse_news_item_handles_relative_url(self):
        """应该处理相对路径 URL"""
        collector = BrowserNewsCollector.__new__(BrowserNewsCollector)
        
        mock_item = MagicMock()
        mock_title = MagicMock()
        mock_title.get_text.return_value = "测试新闻"
        mock_title.get.return_value = "//example.com/path"
        mock_item.select_one.return_value = mock_title
        
        selectors = {'title': 'a'}
        
        result = collector._parse_news_item(mock_item, selectors, "测试源")
        
        assert result['url'].startswith('https:')

    def test_init_loads_config(self):
        """应该加载配置文件"""
        with patch('builtins.open'), \
             patch('pathlib.Path.is_absolute', return_value=True), \
             patch('yaml.safe_load') as mock_yaml:
            
            mock_yaml.return_value = {
                'sources': [
                    {'name': '测试源', 'type': 'browser', 'search_url': 'http://test.com'}
                ]
            }
            
            collector = BrowserNewsCollector(config_path="/fake/path.yaml")
            
            assert len(collector.sources_config) == 1
