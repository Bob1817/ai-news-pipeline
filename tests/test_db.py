"""
数据库模块测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.conftest import TEST_DATABASE_URL


@pytest.fixture(scope="module")
def test_db_engine():
    """创建测试数据库引擎"""
    from sqlalchemy import create_engine
    from src.utils.db import Base

    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    # 清理测试数据库文件
    db_file = Path(TEST_DATABASE_URL.replace("sqlite:///", ""))
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(scope="function")
def test_session(test_db_engine):
    """创建测试数据库会话"""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.close()


class TestCollectedNews:
    """测试采集新闻模型"""

    def test_save_collected_news(self, test_session):
        """测试保存采集新闻"""
        from src.utils.db import CollectedNews

        news_data = {
            'title': '测试新闻标题',
            'url': 'https://example.com/news/1',
            'summary': '这是测试新闻的摘要',
            'source': '测试来源',
            'industry': '科技',
            'topic_keyword': '人工智能',
            'publish_time': None,
            'collected_at': None,
            'heat_score': 85.5
        }

        news = CollectedNews(**news_data)
        test_session.add(news)
        test_session.commit()
        test_session.refresh(news)

        assert news.title == '测试新闻标题'
        assert news.industry == '科技'

    def test_query_collected_news(self, test_session):
        """测试查询采集新闻"""
        from src.utils.db import CollectedNews

        # 先清理该测试来源的旧数据
        test_session.query(CollectedNews).filter(
            CollectedNews.source == '测试来源'
        ).delete()
        test_session.commit()

        # 保存测试数据
        news_list = []
        for i in range(3):
            news = CollectedNews(
                title=f'测试新闻{i}',
                url=f'https://example.com/news/{i}',
                summary=f'摘要{i}',
                source='测试来源',
                industry='科技',
                topic_keyword='测试',
            )
            test_session.add(news)
            news_list.append(news)

        test_session.commit()

        # 查询
        count = test_session.query(CollectedNews).filter(
            CollectedNews.source == '测试来源'
        ).count()
        assert count == 3


class TestGeneratedArticle:
    """测试生成文章模型"""

    def test_save_generated_article(self, test_session):
        """测试保存生成文章"""
        from src.utils.db import GeneratedArticle

        article_data = {
            'title': 'AI 生成测试文章',
            'content': '这是测试文章内容',
            'keywords': '["AI", "测试"]',
            'status': 'draft',
            'image_description': '测试图片描述'
        }

        article = GeneratedArticle(**article_data)
        test_session.add(article)
        test_session.commit()
        test_session.refresh(article)

        assert article.title == 'AI 生成测试文章'
        assert article.status == 'draft'

    def test_update_article_status(self, test_session):
        """测试更新文章状态"""
        from src.utils.db import GeneratedArticle

        # 创建文章
        article_data = {
            'title': '待发布文章',
            'content': '内容',
            'keywords': '[]',
            'status': 'draft'
        }
        article = GeneratedArticle(**article_data)
        test_session.add(article)
        test_session.commit()

        # 更新状态
        article.status = 'published'
        test_session.commit()
        test_session.refresh(article)

        # 验证
        assert article.status == 'published'


class TestDatabaseConnection:
    """测试数据库连接"""

    def test_database_url_resolution(self):
        """测试数据库 URL 解析"""
        from src.utils.db import DATABASE_URL
        assert DATABASE_URL.startswith('sqlite:///')

    def test_init_db(self, test_db_engine):
        """测试数据库初始化"""
        from src.utils.db import Base
        # 如果测试通过，说明表创建成功
        tables = Base.metadata.tables.keys()
        assert 'collected_news' in tables
        assert 'generated_articles' in tables
