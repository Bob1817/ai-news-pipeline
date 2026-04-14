"""
本地 SQLite 数据库管理
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def _resolve_database_url(database_url: str | None) -> str:
    """将 .env 中的相对 SQLite 路径解析到项目根目录"""
    if not database_url:
        return f"sqlite:///{(PROJECT_ROOT / 'data' / 'news_pipeline.db').as_posix()}"

    sqlite_prefix = "sqlite:///"
    if database_url.startswith(sqlite_prefix) and not database_url.startswith("sqlite:////"):
        raw_path = database_url[len(sqlite_prefix):]
        if raw_path and not Path(raw_path).is_absolute():
            return f"sqlite:///{(PROJECT_ROOT / raw_path).as_posix()}"

    return database_url


DATABASE_URL = _resolve_database_url(os.getenv("DATABASE_URL"))

# 确保 data 目录存在
os.makedirs(PROJECT_ROOT / "data", exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============ 数据模型定义 ============

class CollectedNews(Base):
    """采集到的原始新闻"""
    __tablename__ = "collected_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000))
    summary = Column(Text)
    content = Column(Text)
    source = Column(String(100))           # 来源网站
    industry = Column(String(50))          # 所属行业
    topic_keyword = Column(String(200))    # 搜索关键词
    publish_time = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.now)
    sentiment = Column(String(20))         # 情感倾向：正面/中性/负面
    heat_score = Column(Float, default=0)  # 热度评分


class GeneratedTheme(Base):
    """AI 提炼的主题"""
    __tablename__ = "generated_themes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_name = Column(String(200), nullable=False)
    industry = Column(String(50))
    source_news_ids = Column(Text)         # 关联的原始新闻 ID，逗号分隔
    created_at = Column(DateTime, default=datetime.now)


class GeneratedArticle(Base):
    """AI 生成的文章"""
    __tablename__ = "generated_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_id = Column(Integer)
    title = Column(String(500))
    content = Column(Text)
    keywords = Column(Text)                # JSON 格式存储
    image_path = Column(String(500))
    image_description = Column(Text)
    status = Column(String(20), default="draft")  # draft/published/archived
    created_at = Column(DateTime, default=datetime.now)
    published_at = Column(DateTime)


class PublishRecord(Base):
    """发布记录"""
    __tablename__ = "publish_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer)
    platform = Column(String(50))          # website / wechat / wordpress
    platform_url = Column(String(1000))    # 发布后的文章链接
    status = Column(String(20))            # success / failed / pending
    error_message = Column(Text)
    published_at = Column(DateTime, default=datetime.now)


class MonitorData(Base):
    """监测数据"""
    __tablename__ = "monitor_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer)
    platform = Column(String(50))
    article_url = Column(String(1000))
    page_views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    crawled_at = Column(DateTime, default=datetime.now)


# ============ 数据库操作函数 ============

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成。")


def get_session():
    """获取数据库会话"""
    return SessionLocal()


def save_collected_news(news_list: list) -> list:
    """批量保存采集的新闻，返回保存后的对象列表"""
    session = get_session()
    saved = []
    try:
        for news_data in news_list:
            news = CollectedNews(**news_data)
            saved.append(news)
        session.add_all(saved)
        session.commit()
        return saved
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_generated_article(article_data: dict) -> GeneratedArticle:
    """保存生成的文章"""
    session = get_session()
    try:
        article = GeneratedArticle(**article_data)
        session.add(article)
        session.commit()
        session.refresh(article)
        return article
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def replace_generated_themes(theme_data_list: list) -> list:
    """替换当前主题集合，避免后续生成文章使用到过期主题"""
    session = get_session()
    try:
        session.query(GeneratedTheme).delete()
        themes = [GeneratedTheme(**theme_data) for theme_data in theme_data_list]
        session.add_all(themes)
        session.commit()

        for theme in themes:
            session.refresh(theme)

        return themes
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_publish_record(record_data: dict) -> PublishRecord:
    """保存发布记录"""
    session = get_session()
    try:
        record = PublishRecord(**record_data)
        session.add(record)
        session.commit()
        return record
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# 程序启动时自动建表
init_db()
