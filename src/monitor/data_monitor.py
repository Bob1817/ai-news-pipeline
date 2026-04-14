"""
数据监测模块：定期抓取已发布文章的阅读量、点赞等数据
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger
import yaml
import pandas as pd

from src.utils.db import get_session, MonitorData, PublishRecord, GeneratedArticle

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class DataMonitor:
    """数据监测器"""

    def __init__(self, config_path: str = "config/platforms.yaml"):
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = PROJECT_ROOT / config_file

        with open(config_file, 'r', encoding='utf-8') as f:
            self.platforms_config = yaml.safe_load(f)['platforms']

    async def monitor_website(self, article_url: str) -> Dict:
        """监测官网文章数据"""
        from playwright.async_api import async_playwright

        stats = {
            'article_url': article_url,
            'platform': 'website',
            'page_views': 0,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'crawled_at': datetime.now()
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(article_url, timeout=30000)
                await page.wait_for_load_state('networkidle')

                # 尝试多种常见的数据展示选择器
                selectors_map = {
                    'page_views': [
                        '.view-count', '.read-count', '.pv',
                        '[data-views]', '.article-views',
                        '.statistics-views'
                    ],
                    'likes': [
                        '.like-count', '.praise-count', '.likes',
                        '[data-likes]', '.article-likes'
                    ],
                    'comments': [
                        '.comment-count', '.comments-count',
                        '[data-comments]', '.article-comments'
                    ]
                }

                for stat_name, selectors in selectors_map.items():
                    for selector in selectors:
                        try:
                            elem = await page.query_selector(selector)
                            if elem:
                                text = await elem.text_content()
                                number = self._extract_number(text)
                                if number is not None:
                                    stats[stat_name] = number
                                    break
                        except Exception:
                            continue

                await browser.close()

        except Exception as e:
            logger.error(f"监测网站数据失败 [{article_url}]: {e}")

        return stats

    def _extract_number(self, text: str) -> Optional[int]:
        """从文本中提取数字"""
        if not text:
            return None
        import re
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            return int(numbers[0])
        return None

    async def collect_all_stats(self, days_back: int = 7) -> List[Dict]:
        """
        采集所有近期发布文章的数据

        参数:
            days_back: 回溯天数
        """
        session = get_session()
        all_stats = []

        try:
            # 查询最近N天的发布记录
            cutoff = datetime.now() - timedelta(days=days_back)
            records = session.query(PublishRecord).filter(
                PublishRecord.published_at >= cutoff,
                PublishRecord.status == 'success'
            ).all()

            for record in records:
                if record.platform_url and 'mp.weixin.qq.com' not in record.platform_url:
                    stats = await self.monitor_website(record.platform_url)
                    stats['article_id'] = record.article_id
                    all_stats.append(stats)

                    # 保存到数据库
                    monitor_record = MonitorData(**stats)
                    session.add(monitor_record)

            session.commit()
            logger.info(f"采集了 {len(all_stats)} 篇文章的数据")

        except Exception as e:
            session.rollback()
            logger.error(f"数据采集失败: {e}")
        finally:
            session.close()

        return all_stats

    def generate_report(self, days_back: int = 30) -> Dict:
        """
        生成数据报告

        返回: 包含统计数据和分析结论的字典
        """
        session = get_session()

        try:
            cutoff = datetime.now() - timedelta(days=days_back)

            # 查询监测数据
            monitor_records = session.query(MonitorData).filter(
                MonitorData.crawled_at >= cutoff
            ).all()

            if not monitor_records:
                logger.info("暂无监测数据")
                return {'message': '暂无数据', 'period_days': days_back}

            # 转为DataFrame进行分析
            df = pd.DataFrame([{
                'article_id': r.article_id,
                'platform': r.platform,
                'page_views': r.page_views or 0,
                'likes': r.likes or 0,
                'comments': r.comments or 0,
                'shares': r.shares or 0,
                'crawled_at': r.crawled_at
            } for r in monitor_records])

            # 计算汇总统计
            report = {
                'period_days': days_back,
                'total_articles_monitored': df['article_id'].nunique(),
                'total_data_points': len(df),
                'summary': {
                    'total_page_views': int(df['page_views'].sum()),
                    'avg_page_views': round(df['page_views'].mean(), 1),
                    'max_page_views': int(df['page_views'].max()),
                    'total_likes': int(df['likes'].sum()),
                    'avg_likes': round(df['likes'].mean(), 1),
                    'total_comments': int(df['comments'].sum()),
                },
                'by_platform': {},
                'top_articles': [],
                'trend': []
            }

            # 按平台分组统计
            for platform, group in df.groupby('platform'):
                report['by_platform'][platform] = {
                    'articles': int(group['article_id'].nunique()),
                    'total_views': int(group['page_views'].sum()),
                    'avg_views': round(group['page_views'].mean(), 1),
                    'total_likes': int(group['likes'].sum())
                }

            # Top文章（按浏览量排序）
            top = df.groupby('article_id').agg({
                'page_views': 'max',
                'likes': 'max',
                'comments': 'max'
            }).sort_values('page_views', ascending=False).head(10)

            for article_id, row in top.iterrows():
                # 获取文章标题
                article = session.query(GeneratedArticle).filter(
                    GeneratedArticle.id == article_id
                ).first()
                report['top_articles'].append({
                    'article_id': article_id,
                    'title': article.title if article else '未知',
                    'page_views': int(row['page_views']),
                    'likes': int(row['likes']),
                    'comments': int(row['comments'])
                })

            # 生成可视化
            self._create_visualizations(df, report)

            logger.info(f"报告生成完成：监测了{report['total_articles_monitored']}篇文章")
            return report

        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return {'error': str(e)}
        finally:
            session.close()

    def _create_visualizations(self, df: pd.DataFrame, report: Dict):
        """生成可视化图表"""
        try:
            # 生成HTML报告
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>新闻数据监测报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; padding: 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .stat-item {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px; }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #2196F3; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>新闻自动化系统 — 数据监测报告</h1>
    <p>统计周期：最近 {report.get('period_days', 30)} 天</p>

    <div class="card">
        <h2>总览</h2>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{report.get('summary', {}).get('total_page_views', 0)}</div>
                <div class="stat-label">总浏览量</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{report.get('summary', {}).get('total_likes', 0)}</div>
                <div class="stat-label">总点赞数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{report.get('summary', {}).get('total_comments', 0)}</div>
                <div class="stat-label">总评论数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{report.get('total_articles_monitored', 0)}</div>
                <div class="stat-label">监测文章数</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Top 文章排行</h2>
        <table>
            <tr><th>排名</th><th>标题</th><th>浏览量</th><th>点赞</th><th>评论</th></tr>
            {''.join(f"<tr><td>{i+1}</td><td>{a['title']}</td><td>{a['page_views']}</td><td>{a['likes']}</td><td>{a['comments']}</td></tr>" for i, a in enumerate(report.get('top_articles', [])))}
        </table>
    </div>

    <div class="card">
        <h2>平台分布</h2>
        <div id="platform-chart" style="height: 400px;"></div>
    </div>

    <script>
        var chart = echarts.init(document.getElementById('platform-chart'));
        var platformData = {str(report.get('by_platform', {})).replace("'", '"')};
        var names = Object.keys(platformData);
        var views = names.map(n => platformData[n].total_views || 0);
        chart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: names }},
            yAxis: {{ type: 'value', name: '浏览量' }},
            series: [{{ type: 'bar', data: views, itemStyle: {{ color: '#4CAF50' }} }}]
        }});
    </script>
</body>
</html>"""

            report_path = "data/report.html"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"可视化报告已生成: {report_path}")

        except Exception as e:
            logger.warning(f"可视化生成失败: {e}")
