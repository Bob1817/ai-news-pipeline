"""
测试配置文件
"""
import os
from pathlib import Path

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
