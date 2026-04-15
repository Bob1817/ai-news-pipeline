"""
测试配置文件
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 测试数据库路径
TEST_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'test_news_pipeline.db'}"

# 测试配置
TEST_SETTINGS = {
    "app": {
        "name": "AI 新闻自动化系统 - 测试",
        "version": "1.0.0-test",
    },
    "llm": {
        "provider": "ollama",
        "model": "qwen2:7b",
        "api_url": "",
        "text_url": "/chat/completions",
        "api_key": "",
    },
    "collector": {
        "count_options": [10, 20, 30],
        "default_count": 10,
        "time_range_hours": 24,
        "timeout": 30,
        "retry_times": 3,
    },
    "generator": {
        "theme_options": [3, 5, 8],
        "default_theme_count": 3,
        "article_min_words": 800,
        "article_max_words": 1500,
        "auto_generate_image": True,
        "image_generation_method": "api",
    },
    "distributor": {
        "require_review": True,
        "publish_interval": 10,
    },
    "monitor": {
        "check_interval": 60,
        "data_retention_days": 90,
    },
    "distributors": {
        "website": {
            "url": "",
            "username": "",
            "password": "",
        },
        "wechat": {
            "app_id": "",
            "app_secret": "",
            "api_url": "https://api.weixin.qq.com",
            "access_token_expire": 7200,
        },
    },
    "industries": [
        {"name": "科技", "keywords": ["人工智能", "芯片", "5G"]},
        {"name": "财经", "keywords": ["股市", "基金", "央行"]},
    ],
}


@pytest.fixture
def temp_dir():
    """提供临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_response():
    """Mock LLM 返回结果"""
    def _mock(response_text="测试响应"):
        return response_text
    return _mock


@pytest.fixture
def sample_news_data():
    """提供测试用新闻样本数据"""
    return [
        {
            'id': 1,
            'title': '人工智能技术实现新突破，多家企业发布创新产品',
            'summary': '近日，多家科技企业宣布在人工智能领域取得重要进展...',
            'source': '新浪科技',
            'url': 'https://example.com/news1',
            'publish_time': '2024-01-15',
            'heat_score': 75.0
        },
        {
            'id': 2,
            'title': '芯片行业迎来重大变革，5G技术助力产业升级',
            'summary': '随着5G网络的普及，芯片行业正迎来新的发展机遇...',
            'source': '网易科技',
            'url': 'https://example.com/news2',
            'publish_time': '2024-01-14',
            'heat_score': 68.0
        },
        {
            'id': 3,
            'title': '最新报告显示AI市场持续高速增长',
            'summary': '行业研究机构发布最新报告，AI市场预计未来三年将保持30%以上的增速...',
            'source': '科技日报',
            'url': 'https://example.com/news3',
            'publish_time': '2024-01-13',
            'heat_score': 82.0
        },
    ]


@pytest.fixture
def sample_theme_data():
    """提供测试用主题样本数据"""
    return [
        {
            'id': 1,
            'theme': 'AI技术突破',
            'description': '人工智能领域的最新技术进展',
            'related_news_indices': [1, 3]
        },
        {
            'id': 2,
            'theme': '5G产业发展',
            'description': '5G技术及其对产业的影响',
            'related_news_indices': [2]
        }
    ]


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient"""
    with patch('src.collector.analyzer.LLMClient') as mock:
        mock_instance = MagicMock()
        mock_instance.chat.return_value = "测试响应"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_article_data():
    """提供测试用文章样本数据"""
    return {
        'theme': 'AI技术突破',
        'theme_id': 1,
        'title': 'AI技术实现新突破',
        'content': '这是一篇测试文章内容...',
        'keywords': ['AI', '技术突破'],
        'status': 'draft'
    }
