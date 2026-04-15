"""
测试 analyzer.py 模块
包含: LLMCache, LLMClient, NewsAnalyzer
"""
import pytest
import json
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.collector.analyzer import LLMCache, LLMClient, NewsAnalyzer


class TestLLMCache:
    """测试 LLMCache 类"""

    def test_init_creates_cache_dir(self, temp_dir):
        """应该初始化时创建缓存目录"""
        cache = LLMCache(cache_dir=str(temp_dir / "cache"))
        assert (temp_dir / "cache").exists()

    def test_get_cache_key_generates_hash(self, temp_dir):
        """应该为相同的 prompts 生成相同的 hash key"""
        cache = LLMCache(cache_dir=str(temp_dir))
        key1 = cache._get_cache_key("system", "user")
        key2 = cache._get_cache_key("system", "user")
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash 长度

    def test_set_and_get_cache(self, temp_dir):
        """应该能设置和获取缓存"""
        cache = LLMCache(cache_dir=str(temp_dir))
        cache.set("system prompt", "user prompt", "test response")
        
        result = cache.get("system prompt", "user prompt")
        assert result == "test response"

    def test_get_returns_none_for_missing_key(self, temp_dir):
        """应该为不存在的 key 返回 None"""
        cache = LLMCache(cache_dir=str(temp_dir))
        result = cache.get("nonexistent", "key")
        assert result is None

    def test_cache_expires_after_ttl(self, temp_dir):
        """应该在 TTL 后过期"""
        cache = LLMCache(cache_dir=str(temp_dir))
        cache.ttl_hours = 0  # 设置 TTL 为 0 小时，立即过期
        
        cache.set("system", "user", "response")
        
        # 等待一小段时间
        time.sleep(0.1)
        # 写入一个过期的时间戳
        cache_key = cache._get_cache_key("system", "user")
        cache_file = cache.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['timestamp'] = time.time() - 3600  # 设置为 1 小时前
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        result = cache.get("system", "user")
        assert result is None

    def test_cache_file_format(self, temp_dir):
        """应该以正确的 JSON 格式保存缓存"""
        cache = LLMCache(cache_dir=str(temp_dir))
        cache.set("sys", "usr", "resp")
        
        cache_key = cache._get_cache_key("sys", "usr")
        cache_file = cache.cache_dir / f"{cache_key}.json"
        
        assert cache_file.exists()
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert 'response' in data
        assert data['response'] == "resp"
        assert isinstance(data['timestamp'], float)


class TestLLMClient:
    """测试 LLMClient 类"""

    @patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_BASE_URL": "http://test:11434"})
    def test_init_ollama_provider(self, temp_dir):
        """应该正确初始化 Ollama provider"""
        with patch('src.collector.analyzer.LLMCache'):
            client = LLMClient(use_cache=False)
            assert client.provider == "ollama"
            assert client.base_url == "http://test:11434"

    @patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
    def test_init_openai_provider(self, temp_dir):
        """应该正确初始化 OpenAI provider"""
        with patch('src.collector.analyzer.LLMCache'):
            client = LLMClient(use_cache=False)
            assert client.provider == "openai"
            assert client.api_key == "test-key"

    @patch('src.collector.analyzer.httpx.Client')
    @patch.dict(os.environ, {"LLM_PROVIDER": "ollama"})
    def test_chat_ollama_success(self, mock_env, mock_httpx, temp_dir):
        """应该成功调用 Ollama API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'message': {'content': 'AI response'}
        }
        mock_response.raise_for_status.return_value = None
        
        mock_httpx_instance = MagicMock()
        mock_httpx_instance.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_httpx_instance)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=None)
        
        with patch('src.collector.analyzer.LLMCache'):
            client = LLMClient(use_cache=False)
            response = client.chat("system", "user")
        
        assert response == 'AI response'
        mock_httpx_instance.post.assert_called_once()

    @patch('src.collector.analyzer.httpx.Client')
    @patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
    def test_chat_openai_success(self, mock_env, mock_httpx, temp_dir):
        """应该成功调用 OpenAI API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'OpenAI response'}}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_httpx_instance = MagicMock()
        mock_httpx_instance.post.return_value = mock_response
        mock_httpx.return_value.__enter__ = MagicMock(return_value=mock_httpx_instance)
        mock_httpx.return_value.__exit__ = MagicMock(return_value=None)
        
        with patch('src.collector.analyzer.LLMCache'):
            client = LLMClient(use_cache=False)
            response = client.chat("system", "user")
        
        assert response == 'OpenAI response'

    def test_chat_returns_empty_on_error(self, temp_dir):
        """应该在调用失败时返回空字符串"""
        with patch('src.collector.analyzer.httpx.Client') as mock_httpx:
            mock_httpx.side_effect = Exception("Network error")
            with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
                with patch('src.collector.analyzer.LLMCache'):
                    client = LLMClient(use_cache=False)
                    response = client.chat("system", "user")
        
        assert response == ""

    @patch('src.collector.analyzer.LLMCache')
    def test_chat_uses_cache(self, mock_cache_class, temp_dir):
        """应该使用缓存避免重复调用"""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = "cached response"
        mock_cache_class.return_value = mock_cache_instance
        
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            client = LLMClient(use_cache=True)
            response = client.chat("system", "user")
        
        assert response == "cached response"
        mock_cache_instance.get.assert_called_once()


class TestNewsAnalyzer:
    """测试 NewsAnalyzer 类"""

    def test_full_analysis_with_empty_news(self):
        """应该对空新闻列表返回空结果"""
        analyzer = NewsAnalyzer()
        with patch.object(analyzer, 'llm'):
            analyzed_news, themes = analyzer.full_analysis([], theme_count=3)
        
        assert analyzed_news == []
        assert themes == []

    def test_calculate_heat_score_basic(self):
        """应该计算基础热度分数"""
        analyzer = NewsAnalyzer()
        news = {
            'title': '测试新闻标题',
            'summary': '测试摘要'
        }
        score = analyzer._calculate_heat_score(news)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_calculate_heat_score_with_hot_keywords(self):
        """应该对包含热点关键词的新闻加分"""
        analyzer = NewsAnalyzer()
        news = {
            'title': '最新突破！重磅发布',
        }
        score = analyzer._calculate_heat_score(news)
        # 基础分 50 + 2个关键词各3分 = 56
        assert score >= 56

    def test_calculate_heat_score_title_length_bonus(self):
        """应该根据标题长度加分"""
        analyzer = NewsAnalyzer()
        # 20-50 字符的标题应该获得 +10
        news = {
            'title': '这是一个长度适中的新闻标题用于测试加分项'
        }
        score = analyzer._calculate_heat_score(news)
        assert score >= 60  # 50 + 10

    @patch.object(LLMClient, 'chat')
    def test_analyze_sentiment_positive(self, mock_chat):
        """应该识别正面情感"""
        mock_chat.return_value = "positive"
        analyzer = NewsAnalyzer()
        news = {'title': '重大突破', 'summary': '好消息'}
        
        sentiment = analyzer._analyze_sentiment(news)
        assert sentiment == 'positive'

    @patch.object(LLMClient, 'chat')
    def test_analyze_sentiment_negative(self, mock_chat):
        """应该识别负面情感"""
        mock_chat.return_value = "negative"
        analyzer = NewsAnalyzer()
        news = {'title': '市场下跌', 'summary': '坏消息'}
        
        sentiment = analyzer._analyze_sentiment(news)
        assert sentiment == 'negative'

    @patch.object(LLMClient, 'chat')
    def test_analyze_sentiment_chinese_response(self, mock_chat):
        """应该识别中文情感词"""
        mock_chat.return_value = "正面"
        analyzer = NewsAnalyzer()
        news = {'title': '好消息', 'summary': '正面新闻'}
        
        sentiment = analyzer._analyze_sentiment(news)
        assert sentiment == 'positive'

    @patch.object(LLMClient, 'chat')
    def test_analyze_sentiment_returns_neutral_on_error(self, mock_chat):
        """应该在 LLM 调用失败时返回中性"""
        mock_chat.return_value = ""
        analyzer = NewsAnalyzer()
        news = {'title': '新闻', 'summary': '摘要'}
        
        sentiment = analyzer._analyze_sentiment(news)
        assert sentiment == 'neutral'

    def test_extract_themes_with_empty_news(self):
        """应该对空新闻列表返回空主题"""
        analyzer = NewsAnalyzer()
        themes = analyzer._extract_themes([], theme_count=3)
        assert themes == []

    @patch.object(LLMClient, 'chat')
    def test_extract_themes_parses_json(self, mock_chat):
        """应该解析 LLM 返回的 JSON 主题"""
        mock_chat.return_value = '''[
            {
                "theme": "AI发展",
                "description": "人工智能领域的最新进展",
                "related_news_indices": [1, 2]
            }
        ]'''
        analyzer = NewsAnalyzer()
        analyzed_news = [{'title': '新闻1', 'source': '源1', 'heat_score': 70}]
        
        themes = analyzer._extract_themes(analyzed_news, theme_count=1)
        
        assert len(themes) == 1
        assert themes[0]['theme'] == 'AI发展'
        assert themes[0]['related_news_indices'] == [1, 2]

    @patch.object(LLMClient, 'chat')
    def test_extract_themes_uses_defaults_on_parse_failure(self, mock_chat):
        """应该在 JSON 解析失败时使用默认主题"""
        mock_chat.return_value = "无效的JSON响应"
        analyzer = NewsAnalyzer()
        analyzed_news = [
            {'title': '新闻1', 'source': '源1', 'heat_score': 70},
            {'title': '新闻2', 'source': '源2', 'heat_score': 65}
        ]
        
        themes = analyzer._extract_themes(analyzed_news, theme_count=2)
        
        assert len(themes) >= 1
        assert 'theme' in themes[0]

    def test_generate_default_themes(self):
        """应该能生成默认主题"""
        analyzer = NewsAnalyzer()
        themes = analyzer._generate_default_themes(3)
        
        assert len(themes) == 3
        assert all('theme' in t for t in themes)
        assert all('description' in t for t in themes)

    def test_get_theme_details(self):
        """应该获取主题的详细信息"""
        analyzer = NewsAnalyzer()
        theme = {
            'id': 1,
            'theme': '测试主题',
            'related_news_indices': [1, 2]
        }
        analyzed_news = [
            {'id': 1, 'title': '新闻1'},
            {'id': 2, 'title': '新闻2'},
            {'id': 3, 'title': '新闻3'}
        ]
        
        details = analyzer.get_theme_details(theme, analyzed_news)
        
        assert 'related_news' in details
        assert details['related_news_count'] == 2
        assert len(details['related_news']) == 2

    @patch.object(LLMClient, 'chat')
    def test_full_analysis_complete_flow(self, mock_chat):
        """应该完成完整的分析流程"""
        # Mock LLM 返回
        mock_chat.side_effect = [
            "positive",  # 第一条新闻情感
            "neutral",   # 第二条新闻情感
            '[{"theme": "技术发展", "description": "技术进展", "related_news_indices": [1, 2]}]'  # 主题
        ]
        
        analyzer = NewsAnalyzer()
        news_list = [
            {'id': 1, 'title': '技术突破', 'summary': '好消息', 'source': '源1'},
            {'id': 2, 'title': '市场动态', 'summary': '新闻2', 'source': '源2'}
        ]
        
        analyzed_news, themes = analyzer.full_analysis(news_list, theme_count=1)
        
        assert len(analyzed_news) == 2
        assert len(themes) == 1
        assert 'heat_score' in analyzed_news[0]
        assert 'sentiment' in analyzed_news[0]
