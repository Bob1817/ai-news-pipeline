"""
基于 API/RSS 的新闻采集器（作为浏览器采集的备用方案）
"""
import asyncio
import httpx
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger
import yaml

from src.utils.db import save_collected_news

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ApiNewsCollector:
    """API/RSS 新闻采集器"""

    def __init__(self, config_path: str = "config/news_sources.yaml"):
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = PROJECT_ROOT / config_file

        with open(config_file, 'r', encoding='utf-8') as f:
            self.sources_config = yaml.safe_load(f)['sources']

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }

    def collect_from_rss(self, source: dict, keyword: str, count: int) -> List[Dict]:
        """从 RSS 源采集"""
        news_list = []
        try:
            logger.info(f"从 RSS 源 [{source['name']}] 采集...")
            feed = feedparser.parse(source['url'])

            for entry in feed.entries[:count * 2]:  # 多取一些用于筛选
                title = entry.get('title', '')
                # 简单关键词过滤
                if keyword and keyword.lower() not in title.lower():
                    # 也检查摘要
                    summary = entry.get('summary', '')
                    if keyword.lower() not in summary.lower():
                        continue

                # 解析发布时间
                publish_time = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        publish_time = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pass

                news_list.append({
                    'title': title[:500],
                    'url': entry.get('link', '')[:1000],
                    'summary': BeautifulSoup(
                        entry.get('summary', ''), 'lxml'
                    ).get_text(strip=True)[:2000],
                    'source': source['name'],
                    'publish_time': publish_time,
                    'collected_at': datetime.now()
                })

            logger.info(f"从 [{source['name']}] 采集到 {len(news_list)} 条")

        except Exception as e:
            logger.error(f"RSS 采集失败 [{source['name']}]: {e}")

        return news_list[:count]

    def collect_from_search_api(
        self,
        keyword: str,
        count: int = 10
    ) -> List[Dict]:
        """
        使用搜索引擎 API 采集（示例：使用 Serper 或 Bing News API）
        您需要自行申请 API Key
        """
        news_list = []
        # 示例：使用 Serper.dev 的 Google News API
        # API_KEY = os.getenv("SERPER_API_KEY")
        # url = "https://google.serper.dev/news"
        # payload = {"q": keyword, "num": count, "hl": "zh-cn"}
        # headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
        # response = httpx.post(url, json=payload, headers=headers)
        # data = response.json()
        # for item in data.get("news", []):
        #     news_list.append({...})

        logger.info("搜索 API 采集器已就绪（需配置 API Key）")
        return news_list

    async def collect_async(
        self,
        industry: str,
        topic: str = "",
        count: int = 10,
        time_range_hours: int = 24
    ) -> List[Dict]:
        """异步主采集方法"""
        keyword = f"{industry} {topic}".strip() if topic else industry

        all_news = []

        # 采集 RSS 源（并发）
        rss_sources = [s for s in self.sources_config if s.get('type') == 'rss']

        async def collect_rss(source):
            return self.collect_from_rss(source, keyword, count)

        # 并发采集所有 RSS 源
        tasks = [collect_rss(src) for src in rss_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            else:
                logger.warning(f"RSS 采集异常：{result}")

        # 时间过滤
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        all_news = [
            n for n in all_news
            if n.get('publish_time') and n['publish_time'] >= cutoff_time
        ]

        # 设置行业
        for n in all_news:
            n['industry'] = industry
            n['topic_keyword'] = keyword

        # 排序取前 N
        all_news.sort(key=lambda x: x.get('publish_time', datetime.min), reverse=True)
        all_news = all_news[:count]

        # 保存
        if all_news:
            save_collected_news(all_news)

        return all_news

    def collect(
        self,
        industry: str,
        topic: str = "",
        count: int = 10,
        time_range_hours: int = 24
    ) -> List[Dict]:
        """主采集方法（同步）"""
        import asyncio
        return asyncio.run(self.collect_async(
            industry=industry,
            topic=topic,
            count=count,
            time_range_hours=time_range_hours
        ))
