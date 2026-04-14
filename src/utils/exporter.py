"""
数据导出模块
支持将文章导出为 Markdown、JSON 等格式
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from loguru import logger

from src.utils.db import get_session, GeneratedArticle


class DataExporter:
    """数据导出器"""

    def __init__(self, export_dir: str = "data/export"):
        export_path = Path(export_dir)
        if not export_path.is_absolute():
            export_path = Path(__file__).resolve().parent.parent.parent / export_path
        self.export_dir = export_path
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_articles_to_markdown(
        self,
        article_ids: List[int] = None,
        status: str = None
    ) -> str:
        """
        导出文章为 Markdown 文件

        参数:
            article_ids: 文章 ID 列表，None 表示所有
            status: 文章状态（draft/published）

        返回：导出目录路径
        """
        session = get_session()
        try:
            query = session.query(GeneratedArticle)
            if article_ids:
                query = query.filter(GeneratedArticle.id.in_(article_ids))
            if status:
                query = query.filter(GeneratedArticle.status == status)

            articles = query.all()

            # 创建日期子目录
            date_dir = self.export_dir / datetime.now().strftime("%Y%m%d")
            date_dir.mkdir(exist_ok=True)

            exported_files = []
            for article in articles:
                md_content = self._article_to_markdown(article)
                filename = f"{article.id}_{article.title[:30].replace('/', '_')}.md"
                filepath = date_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                exported_files.append(str(filepath))
                logger.info(f"已导出：{filename}")

            logger.info(f"共导出 {len(exported_files)} 篇文章")
            return str(date_dir)

        finally:
            session.close()

    def _article_to_markdown(self, article: GeneratedArticle) -> str:
        """将文章转换为 Markdown 格式"""
        # 解析关键词
        keywords = []
        if article.keywords:
            try:
                keywords = json.loads(article.keywords)
            except Exception:
                keywords = article.keywords.split(',')

        md = f"""# {article.title}

**关键词**: {', '.join(keywords)}

**创建时间**: {article.created_at}

**状态**: {article.status}

---

{article.content}

---

*本文由 AI News Pipeline 自动生成*
"""
        return md

    def export_articles_to_json(
        self,
        article_ids: List[int] = None,
        status: str = None
    ) -> str:
        """
        导出文章为 JSON 文件

        参数:
            article_ids: 文章 ID 列表
            status: 文章状态

        返回：导出的 JSON 文件路径
        """
        session = get_session()
        try:
            query = session.query(GeneratedArticle)
            if article_ids:
                query = query.filter(GeneratedArticle.id.in_(article_ids))
            if status:
                query = query.filter(GeneratedArticle.status == status)

            articles = query.all()

            # 转换为字典列表
            data = []
            for article in articles:
                article_dict = {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'keywords': json.loads(article.keywords) if article.keywords else [],
                    'status': article.status,
                    'created_at': str(article.created_at),
                    'published_at': str(article.published_at) if article.published_at else None
                }
                data.append(article_dict)

            # 保存为 JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.export_dir / f"articles_{timestamp}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 JSON: {filepath}")
            return str(filepath)

        finally:
            session.close()

    def export_all_data(self) -> Dict:
        """
        导出所有数据（文章 + 发布记录 + 监测数据）

        返回：导出文件路径字典
        """
        from src.utils.db import PublishRecord, MonitorData

        session = get_session()
        try:
            result = {}

            # 导出文章
            articles = session.query(GeneratedArticle).all()
            article_data = []
            for a in articles:
                article_data.append({
                    'id': a.id,
                    'title': a.title,
                    'content': a.content,
                    'keywords': a.keywords,
                    'status': a.status,
                    'created_at': str(a.created_at)
                })
            articles_file = self.export_dir / "articles_all.json"
            with open(articles_file, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            result['articles'] = str(articles_file)

            # 导出发布记录
            records = session.query(PublishRecord).all()
            record_data = [{
                'id': r.id,
                'platform': r.platform,
                'status': r.status,
                'platform_url': r.platform_url,
                'error_message': r.error_message,
                'published_at': str(r.published_at)
            } for r in records]
            records_file = self.export_dir / "publish_records_all.json"
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(record_data, f, ensure_ascii=False, indent=2)
            result['publish_records'] = str(records_file)

            # 导出监测数据
            monitor_data = session.query(MonitorData).all()
            monitor_list = [{
                'id': m.id,
                'article_id': m.article_id,
                'platform': m.platform,
                'page_views': m.page_views,
                'likes': m.likes,
                'comments': m.comments,
                'shares': m.shares,
                'crawled_at': str(m.crawled_at)
            } for m in monitor_data]
            monitor_file = self.export_dir / "monitor_data_all.json"
            with open(monitor_file, 'w', encoding='utf-8') as f:
                json.dump(monitor_list, f, ensure_ascii=False, indent=2)
            result['monitor_data'] = str(monitor_file)

            logger.info(f"全量数据导出完成")
            return result

        finally:
            session.close()


# ============ 便捷函数 ============

def export_to_markdown(article_ids: List[int] = None) -> str:
    """导出文章为 Markdown"""
    exporter = DataExporter()
    return exporter.export_articles_to_markdown(article_ids)


def export_to_json(article_ids: List[int] = None) -> str:
    """导出文章为 JSON"""
    exporter = DataExporter()
    return exporter.export_articles_to_json(article_ids)


if __name__ == "__main__":
    # 测试
    exporter = DataExporter()

    # 导出所有文章为 JSON
    filepath = exporter.export_articles_to_json()
    print(f"已导出：{filepath}")

    # 导出所有数据
    all_data = exporter.export_all_data()
    print(f"全量导出：{all_data}")
