"""
分发调度器：统一管理多平台发布
"""
import asyncio
from typing import List, Dict
from loguru import logger

from src.distributor.website_publisher import WebsitePublisher
from src.distributor.wechat_publisher import WechatPublisher


class Distributor:
    """内容分发调度器"""

    def __init__(self):
        self.publishers = {
            'website': WebsitePublisher(),
            'wechat': WechatPublisher()
        }

    async def distribute(
        self,
        article: Dict,
        platforms: List[str]
    ) -> List[Dict]:
        """
        将文章分发到指定平台

        参数:
            article: 文章数据
            platforms: 目标平台列表 ['website', 'wechat']

        返回: 各平台发布结果列表
        """
        results = []

        for platform in platforms:
            publisher = self.publishers.get(platform)
            if not publisher:
                logger.warning(f"未知平台: {platform}")
                results.append({
                    'platform': platform,
                    'success': False,
                    'error': '未知平台'
                })
                continue

            if not publisher.enabled:
                logger.warning(f"平台 [{platform}] 未启用")
                results.append({
                    'platform': platform,
                    'success': False,
                    'error': '平台未启用'
                })
                continue

            logger.info(f"开始向 [{platform}] 发布文章: 《{article.get('title', '')}》")
            result = await publisher.publish(article)
            results.append(result)

            # 发布间隔
            await asyncio.sleep(5)

        # 汇总结果
        success_count = sum(1 for r in results if r.get('success'))
        logger.info(f"分发完成: {success_count}/{len(results)} 个平台成功")

        return results

    async def batch_distribute(
        self,
        articles: List[Dict],
        platforms: List[str]
    ) -> Dict:
        """
        批量分发多篇文章

        返回: 统计结果
        """
        total_results = {
            'total_articles': len(articles),
            'total_platforms': len(platforms),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for article in articles:
            results = await self.distribute(article, platforms)
            for r in results:
                if r.get('success'):
                    total_results['success'] += 1
                else:
                    total_results['failed'] += 1
            total_results['details'].append({
                'title': article.get('title', ''),
                'results': results
            })

            # 文章之间的发布间隔
            await asyncio.sleep(10)

        return total_results
