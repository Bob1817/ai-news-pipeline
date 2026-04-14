"""
定时任务调度器
支持使用 APScheduler 进行定时采集
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.collector.browser_collector import BrowserNewsCollector
from src.collector.analyzer import NewsAnalyzer
from src.generator.article_writer import ArticleWriter
from src.distributor.distributor import Distributor


class ScheduledTask:
    """定时任务管理器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._collector = None
        self._analyzer = None
        self._writer = None
        self._distributor = None

    def _get_collector(self):
        """获取采集器实例"""
        if self._collector is None:
            self._collector = BrowserNewsCollector()
        return self._collector

    def _get_analyzer(self):
        """获取分析器实例"""
        if self._analyzer is None:
            self._analyzer = NewsAnalyzer()
        return self._analyzer

    def _get_writer(self):
        """获取文章生成器实例"""
        if self._writer is None:
            self._writer = ArticleWriter()
        return self._writer

    def _get_distributor(self):
        """获取分发器实例"""
        if self._distributor is None:
            self._distributor = Distributor()
        return self._distributor

    def add_daily_task(
        self,
        industry: str,
        topic: str = "",
        hour: int = 9,
        minute: int = 0,
        auto_publish: bool = False
    ):
        """
        添加每日定时任务

        参数:
            industry: 行业
            topic: 主题关键词
            hour: 执行小时
            minute: 执行分钟
            auto_publish: 是否自动发布
        """
        def task_callback():
            logger.info(f"定时任务执行：{industry} {topic}")
            asyncio.run(self._run_pipeline(industry, topic, auto_publish))

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            task_callback,
            trigger,
            id=f"daily_{industry}_{topic}",
            name=f"每日采集：{industry} {topic}"
        )
        logger.info(f"已添加定时任务：每日 {hour:02d}:{minute:02d} 采集 {industry} {topic}")

    def add_weekly_task(
        self,
        industry: str,
        topic: str = "",
        day: int = 1,  # 周一
        hour: int = 9,
        minute: int = 0,
        auto_publish: bool = False
    ):
        """
        添加每周定时任务

        参数:
            industry: 行业
            topic: 主题关键词
            day: 星期几（0=周一，6=周日）
            hour: 执行小时
            minute: 执行分钟
            auto_publish: 是否自动发布
        """
        def task_callback():
            logger.info(f"周任务执行：{industry} {topic}")
            asyncio.run(self._run_pipeline(industry, topic, auto_publish))

        trigger = CronTrigger(day_of_week=day, hour=hour, minute=minute)
        self.scheduler.add_job(
            task_callback,
            trigger,
            id=f"weekly_{industry}_{topic}",
            name=f"每周采集：{industry} {topic}"
        )
        logger.info(f"已添加周任务：每周{day} {hour:02d}:{minute:02d} 采集 {industry} {topic}")

    async def _run_pipeline(
        self,
        industry: str,
        topic: str,
        auto_publish: bool = False
    ):
        """运行完整流程"""
        try:
            # 步骤 1: 采集
            logger.info("[1/4] 正在采集新闻...")
            collector = self._get_collector()
            news_list = await collector.collect(industry, topic, count=10)
            logger.info(f"采集完成：{len(news_list)} 条新闻")

            if not news_list:
                logger.warning("未采集到任何新闻，跳过后续步骤")
                return

            # 步骤 2: 分析
            logger.info("[2/4] 正在分析主题...")
            analyzer = self._get_analyzer()
            analyzed_news, themes = analyzer.full_analysis(news_list, theme_count=3)
            logger.info(f"提炼出 {len(themes)} 个主题")

            # 步骤 3: 生成
            logger.info("[3/4] 正在生成文章...")
            writer = self._get_writer()
            articles = writer.batch_generate(themes, analyzed_news)
            logger.info(f"生成完成：{len(articles)} 篇文章")

            # 步骤 4: 发布
            if auto_publish:
                logger.info("[4/4] 正在发布文章...")
                distributor = self._get_distributor()
                results = await distributor.batch_distribute(
                    articles,
                    platforms=['website']
                )
                logger.info(f"发布完成：{results}")
            else:
                logger.info("[4/4] 跳过自动发布")

        except Exception as e:
            logger.error(f"定时任务执行失败：{e}")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("定时任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")

    def list_tasks(self) -> List[Dict]:
        """列出所有任务"""
        tasks = []
        for job in self.scheduler.get_jobs():
            tasks.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time),
                'trigger': str(job.trigger)
            })
        return tasks


# ============ 便捷函数 ============

def create_scheduler() -> ScheduledTask:
    """创建调度器实例"""
    return ScheduledTask()


if __name__ == "__main__":
    # 测试
    scheduler = ScheduledTask()

    # 添加每日任务：每天早上 9 点采集科技新闻
    scheduler.add_daily_task(
        industry="科技",
        topic="人工智能",
        hour=9,
        minute=0,
        auto_publish=False
    )

    # 添加周任务：每周一早上 10 点采集财经新闻
    scheduler.add_weekly_task(
        industry="财经",
        topic="",
        day=1,  # 周一
        hour=10,
        minute=0,
        auto_publish=False
    )

    # 启动
    scheduler.start()

    # 保持运行
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
