"""
基于 Playwright 浏览器自动化的新闻采集器
模拟真实用户在新闻网站搜索并抓取结果
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncContextManager
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger
import yaml

from src.utils.db import save_collected_news

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class BrowserPool:
    """浏览器连接池 - 复用浏览器实例提升性能"""

    _instance = None
    _browser = None
    _context = None
    _pw = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        """获取浏览器池单例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._init()
        return cls._instance

    @classmethod
    async def _init(cls):
        """初始化浏览器"""
        from playwright.async_api import async_playwright

        try:
            cls._pw = await async_playwright().start()
            cls._browser = await cls._pw.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            cls._context = await cls._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                locale='zh-CN'
            )
            logger.info("浏览器池初始化完成")
        except Exception as e:
            logger.error(f"浏览器池初始化失败：{e}")
            raise

    @classmethod
    async def close(cls):
        """关闭浏览器池"""
        if cls._context:
            await cls._context.close()
        if cls._browser:
            await cls._browser.close()
        if cls._pw:
            await cls._pw.stop()
        logger.info("浏览器池已关闭")

    @classmethod
    async def get_context(cls) -> AsyncContextManager:
        """获取浏览器上下文"""
        if cls._context is None:
            await cls._init()
        return cls._context

    @classmethod
    async def new_page(cls):
        """创建新页面"""
        context = await cls.get_context()
        return await context.new_page()


class BrowserNewsCollector:
    """浏览器自动化新闻采集器"""

    def __init__(self, config_path: str = "config/news_sources.yaml"):
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = PROJECT_ROOT / config_file

        with open(config_file, 'r', encoding='utf-8') as f:
            self.sources_config = yaml.safe_load(f)['sources']

    async def _search_on_source(
        self,
        source: dict,
        keyword: str,
        count: int
    ) -> List[Dict]:
        """在单个新闻源上搜索并采集"""
        news_list = []

        try:
            # 使用浏览器池创建页面
            page = await BrowserPool.new_page()

            # 构建搜索 URL
            search_url = source['search_url'].format(keyword=keyword)
            logger.info(f"正在从 [{source['name']}] 搜索：{search_url}")

            await page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)  # 等待动态内容加载

            # 获取页面 HTML
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'lxml')

            # 使用配置的选择器解析
            selectors = source.get('selectors', {})
            items = soup.select(selectors.get('list', '.result'))

            for item in items[:count]:
                try:
                    news = self._parse_news_item(item, selectors, source['name'])
                    if news and news.get('title'):
                        news['industry'] = ''  # 由上层填充
                        news['topic_keyword'] = keyword
                        news_list.append(news)
                except Exception as e:
                    logger.warning(f"解析单条新闻失败：{e}")
                    continue

            logger.info(f"从 [{source['name']}] 成功采集 {len(news_list)} 条新闻")

        except Exception as e:
            logger.error(f"从 [{source['name']}] 采集失败：{e}")
        finally:
            # 页面由上下文管理，不需要单独关闭
            pass

        return news_list

    def _parse_news_item(
        self,
        item,
        selectors: dict,
        source_name: str
    ) -> Optional[Dict]:
        """解析单条新闻元素"""
        # 标题
        title_elem = item.select_one(selectors.get('title', 'a'))
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        link = title_elem.get('href', '')

        # 如果是相对链接，补充完整
        if link and not link.startswith('http'):
            link = f"https:{link}" if link.startswith('//') else f"https://{link}"

        # 摘要
        summary_elem = item.select_one(selectors.get('summary', ''))
        summary = summary_elem.get_text(strip=True) if summary_elem else ''

        # 时间
        time_elem = item.select_one(selectors.get('time', ''))
        time_text = time_elem.get_text(strip=True) if time_elem else ''

        return {
            'title': title[:500],  # 截断过长标题
            'url': link[:1000],
            'summary': summary[:2000],
            'source': source_name,
            'publish_time': self._parse_time(time_text),
            'collected_at': datetime.now()
        }

    def _parse_time(self, time_text: str) -> datetime:
        """智能解析各种时间格式"""
        now = datetime.now()

        if not time_text:
            return now

        # "X 分钟前" / "X 小时前"
        minute_match = re.search(r'(\d+)\s*分钟前', time_text)
        if minute_match:
            return now - timedelta(minutes=int(minute_match.group(1)))

        hour_match = re.search(r'(\d+)\s*小时前', time_text)
        if hour_match:
            return now - timedelta(hours=int(hour_match.group(1)))

        # "今天 HH:MM"
        today_match = re.search(r'今天\s*(\d{1,2}):(\d{2})', time_text)
        if today_match:
            return now.replace(
                hour=int(today_match.group(1)),
                minute=int(today_match.group(2)),
                second=0
            )

        # "MM-DD HH:MM"
        md_match = re.search(r'(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{2})', time_text)
        if md_match:
            return now.replace(
                month=int(md_match.group(1)),
                day=int(md_match.group(2)),
                hour=int(md_match.group(3)),
                minute=int(md_match.group(4)),
                second=0
            )

        # "YYYY-MM-DD HH:MM:SS"
        full_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{2})', time_text)
        if full_match:
            return datetime(
                year=int(full_match.group(1)),
                month=int(full_match.group(2)),
                day=int(full_match.group(3)),
                hour=int(full_match.group(4)),
                minute=int(full_match.group(5))
            )

        return now

    async def collect(
        self,
        industry: str,
        topic: str = "",
        count: int = 10,
        time_range_hours: int = 24,
        headless: bool = True
    ) -> List[Dict]:
        """
        主采集方法

        参数:
            industry: 行业（必选）
            topic: 主题关键词（可选）
            count: 采集数量（10 或 20）
            time_range_hours: 时间范围（小时）
            headless: 是否无头模式
        """
        # 组合搜索关键词
        keyword = f"{industry} {topic}".strip() if topic else industry

        # 使用浏览器池
        await BrowserPool.get_instance()

        all_news = []
        # 遍历所有浏览器类型的新闻源
        browser_sources = [
            s for s in self.sources_config
            if s.get('type') == 'browser'
        ]

        # 并发采集（限制并发数）
        semaphore = asyncio.Semaphore(3)  # 最多同时 3 个源

        async def collect_with_limit(source):
            async with semaphore:
                return await self._search_on_source(source, keyword, count)

        tasks = [collect_with_limit(src) for src in browser_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            else:
                logger.warning(f"某个源采集异常：{result}")

        # 不再关闭浏览器，由浏览器池管理

        # 按时间过滤（只保留指定时间范围内的）
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        filtered_news = [
            n for n in all_news
            if n.get('publish_time') and n['publish_time'] >= cutoff_time
        ]

        # 去重（基于标题相似度）
        filtered_news = self._deduplicate(filtered_news)

        # 设置行业
        for n in filtered_news:
            n['industry'] = industry

        # 按时间排序，取前 count 条
        filtered_news.sort(key=lambda x: x.get('publish_time', datetime.min), reverse=True)
        filtered_news = filtered_news[:count]

        # 保存到数据库
        if filtered_news:
            save_collected_news(filtered_news)
            logger.info(f"共采集 {len(filtered_news)} 条有效新闻并保存至数据库")

        return filtered_news

    def _deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """基于标题的简单去重"""
        seen_titles = set()
        unique_news = []
        for news in news_list:
            title = news.get('title', '').strip()
            # 简化标题用于比较
            simplified = re.sub(r'[\s\W]', '', title)
            if simplified not in seen_titles and len(simplified) > 5:
                seen_titles.add(simplified)
                unique_news.append(news)
        return unique_news


# ============ 便捷调用函数 ============

async def run_collection(
    industry: str,
    topic: str = "",
    count: int = 10,
    time_range_hours: int = 24
) -> List[Dict]:
    """运行新闻采集"""
    collector = BrowserNewsCollector()
    return await collector.collect(
        industry=industry,
        topic=topic,
        count=count,
        time_range_hours=time_range_hours
    )


if __name__ == "__main__":
    # 测试采集
    async def main():
        result = await run_collection(
            industry="科技",
            topic="人工智能",
            count=10
        )
        for i, news in enumerate(result, 1):
            print(f"{i}. {news['title']}")

        # 关闭浏览器池
        await BrowserPool.close()

    asyncio.run(main())
