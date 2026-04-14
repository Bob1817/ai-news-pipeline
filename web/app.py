"""
Web 管理后台
提供可视化的操作界面，管理整个自动化流程
"""
import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from loguru import logger
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collector.browser_collector import BrowserNewsCollector
from src.collector.api_collector import ApiNewsCollector
from src.collector.analyzer import NewsAnalyzer
from src.generator.article_writer import ArticleWriter
from src.generator.image_generator import ImageGenerator
from src.generator.seo_optimizer import SEOOptimizer
from src.distributor.distributor import Distributor
from src.monitor.data_monitor import DataMonitor
from src.utils.db import (
    get_session, CollectedNews, GeneratedTheme,
    GeneratedArticle, PublishRecord, MonitorData, replace_generated_themes
)
from src.utils.exporter import DataExporter

app = Flask(__name__)
CORS(app)

# 基于项目根目录解析配置路径，避免从其他 cwd 启动时报错
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, 'config', 'settings.yaml')

# 加载配置
import yaml
with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
    settings = yaml.safe_load(f)

# ==================== 全局组件实例（启动时初始化） ====================

# 创建单例组件实例，避免每次请求重新初始化
_collector = None
_analyzer = None
_writer = None
_img_gen = None
_distributor = None
_monitor = None


def get_collector():
    """获取浏览器采集器实例"""
    global _collector
    if _collector is None:
        _collector = BrowserNewsCollector()
    return _collector


def get_analyzer():
    """获取新闻分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = NewsAnalyzer()
    return _analyzer


def get_writer():
    """获取文章生成器实例"""
    global _writer
    if _writer is None:
        _writer = ArticleWriter()
    return _writer


def get_image_generator():
    """获取图片生成器实例"""
    global _img_gen
    if _img_gen is None:
        _img_gen = ImageGenerator()
    return _img_gen


def get_distributor():
    """获取分发器实例"""
    global _distributor
    if _distributor is None:
        _distributor = Distributor()
    return _distributor


def get_monitor():
    """获取数据监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = DataMonitor()
    return _monitor


# ==================== 页面路由 ====================

@app.after_request
def add_no_cache_header(response):
    """禁止浏览器缓存 HTML 页面"""
    if request.path == '/':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.route('/')
def index():
    """主页"""
    return render_template('index.html', settings=settings)


# ==================== API 路由 ====================

@app.route('/api/industries', methods=['GET'])
def get_industries():
    """获取行业列表"""
    industries = settings.get('industries', [])
    return jsonify({'code': 0, 'data': industries})


@app.route('/api/collect', methods=['POST'])
def collect_news():
    """
    采集新闻 API

    请求体:
    {
        "industry": "科技",
        "topic": "人工智能",
        "count": 10,
        "time_range_hours": 24
    }
    """
    data = request.json
    industry = data.get('industry', '')
    topic = data.get('topic', '')
    count = int(data.get('count', 10))
    time_range = int(data.get('time_range_hours', 24))

    if not industry:
        return jsonify({'code': 400, 'msg': '行业为必选项'})

    try:
        # 使用浏览器采集器
        collector = get_collector()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        news_list = loop.run_until_complete(
            collector.collect(industry, topic, count, time_range)
        )
        loop.close()

        return jsonify({
            'code': 0,
            'msg': f'成功采集 {len(news_list)} 条新闻',
            'data': [
                {
                    'title': n.get('title'),
                    'source': n.get('source'),
                    'summary': n.get('summary', '')[:200],
                    'url': n.get('url'),
                    'publish_time': str(n.get('publish_time', '')),
                    'heat_score': n.get('heat_score', 0)
                }
                for n in news_list
            ]
        })
    except Exception as e:
        logger.error(f"采集失败：{e}")
        return jsonify({'code': 500, 'msg': f'采集失败：{str(e)}'})


@app.route('/api/analyze', methods=['POST'])
def analyze_news():
    """
    分析新闻并提炼主题

    请求体:
    {
        "news_indices": [0, 1, 2, ...],  // 选中的新闻索引
        "theme_count": 3
    }
    """
    data = request.json or {}
    theme_count = int(data.get('theme_count', 3))

    try:
        # 从数据库获取最近采集的新闻
        session = get_session()
        recent_news = session.query(CollectedNews).order_by(
            CollectedNews.collected_at.desc()
        ).limit(20).all()
        news_id_by_index = {
            index: news.id for index, news in enumerate(recent_news, 1)
        }
        session.close()

        news_list = [{
            'id': n.id,
            'title': n.title,
            'url': n.url,
            'summary': n.summary,
            'source': n.source,
            'industry': n.industry,
            'publish_time': n.publish_time,
            'heat_score': n.heat_score
        } for n in recent_news]

        # 分析
        analyzer = get_analyzer()
        analyzed_news, themes = analyzer.full_analysis(news_list, theme_count)
        saved_themes = replace_generated_themes([
            {
                'theme_name': theme.get('theme', f'主题{index}'),
                'industry': recent_news[0].industry if recent_news else '',
                'source_news_ids': ','.join(
                    str(news_id_by_index[idx])
                    for idx in theme.get('related_news_indices', [])
                    if idx in news_id_by_index
                ),
            }
            for index, theme in enumerate(themes, 1)
        ])

        for theme, saved_theme in zip(themes, saved_themes):
            related_news_ids = [
                int(x) for x in (saved_theme.source_news_ids or '').split(',')
                if x
            ]
            theme['id'] = saved_theme.id
            theme['related_news_ids'] = related_news_ids

        return jsonify({
            'code': 0,
            'msg': f'分析完成，提炼出 {len(themes)} 个主题',
            'data': {
                'themes': themes,
                'analyzed_news_count': len(analyzed_news)
            }
        })
    except Exception as e:
        logger.error(f"分析失败：{e}")
        return jsonify({'code': 500, 'msg': f'分析失败：{str(e)}'})


@app.route('/api/generate', methods=['POST'])
def generate_articles():
    """
    根据主题生成文章

    请求体:
    {
        "theme_indices": [0, 1, 2],  // 选择的主题索引
        "min_words": 800,
        "max_words": 1500
    }
    """
    data = request.json or {}
    min_words = int(data.get('min_words', 800))
    max_words = int(data.get('max_words', 1500))

    try:
        # 获取主题和新闻
        session = get_session()
        themes = session.query(GeneratedTheme).order_by(
            GeneratedTheme.created_at.desc()
        ).limit(5).all()
        recent_news = session.query(CollectedNews).order_by(
            CollectedNews.collected_at.desc()
        ).limit(20).all()
        session.close()

        theme_list = [{
            'id': t.id,
            'theme': t.theme_name,
            'description': '',
            'related_news_ids': [
                int(x) for x in t.source_news_ids.split(',')
            ] if t.source_news_ids else []
        } for t in themes]

        news_list = [{
            'id': n.id,
            'title': n.title,
            'url': n.url,
            'summary': n.summary,
            'source': n.source,
            'heat_score': n.heat_score
        } for n in recent_news]

        # 生成文章
        writer = get_writer()
        articles = writer.batch_generate(theme_list, news_list, min_words, max_words)

        # 生成配图
        img_gen = get_image_generator()
        for article in articles:
            if article.get('image_description'):
                img_path = img_gen.generate(
                    article['image_description'],
                    article.get('title', '')
                )
                article['image_path'] = img_path

        return jsonify({
            'code': 0,
            'msg': f'成功生成 {len(articles)} 篇文章',
            'data': [{
                'title': a.get('title'),
                'theme': a.get('theme'),
                'word_count': a.get('word_count'),
                'keywords': a.get('keywords', [])[:10],
                'image_path': a.get('image_path'),
                'content_preview': a.get('content', '')[:500]
            } for a in articles]
        })
    except Exception as e:
        logger.error(f"生成失败：{e}")
        return jsonify({'code': 500, 'msg': f'生成失败：{str(e)}'})


@app.route('/api/publish', methods=['POST'])
def publish_articles():
    """
    发布文章到指定平台

    请求体:
    {
        "article_ids": [1, 2, 3],
        "platforms": ["website", "wechat"]
    }
    """
    data = request.json
    platforms = data.get('platforms', ['website'])

    try:
        # 获取文章数据
        session = get_session()
        articles = session.query(GeneratedArticle).filter(
            GeneratedArticle.status == 'draft'
        ).order_by(GeneratedArticle.created_at.desc()).limit(5).all()
        session.close()

        article_list = [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'keywords': json.loads(a.keywords) if a.keywords else [],
            'image_path': a.image_path or '',
            'image_description': a.image_description or ''
        } for a in articles]

        # 分发
        distributor = get_distributor()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            distributor.batch_distribute(article_list, platforms)
        )
        loop.close()

        return jsonify({
            'code': 0,
            'msg': '发布流程完成',
            'data': results
        })
    except Exception as e:
        logger.error(f"发布失败：{e}")
        return jsonify({'code': 500, 'msg': f'发布失败：{str(e)}'})


@app.route('/api/monitor', methods=['GET'])
def monitor_data():
    """获取监测数据报告"""
    try:
        days = int(request.args.get('days', 7))
        monitor = get_monitor()
        report = monitor.generate_report(days)
        return jsonify({'code': 0, 'data': report})
    except Exception as e:
        logger.error(f"监测数据获取失败：{e}")
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/articles', methods=['GET'])
def list_articles():
    """获取已生成的文章列表"""
    try:
        session = get_session()
        articles = session.query(GeneratedArticle).order_by(
            GeneratedArticle.created_at.desc()
        ).limit(50).all()
        session.close()

        return jsonify({
            'code': 0,
            'data': [{
                'id': a.id,
                'title': a.title,
                'status': a.status,
                'created_at': str(a.created_at) if a.created_at else '',
                'published_at': str(a.published_at) if a.published_at else ''
            } for a in articles]
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/history', methods=['GET'])
def publish_history():
    """获取发布历史"""
    try:
        session = get_session()
        records = session.query(PublishRecord).order_by(
            PublishRecord.published_at.desc()
        ).limit(50).all()
        session.close()

        return jsonify({
            'code': 0,
            'data': [{
                'id': r.id,
                'platform': r.platform,
                'status': r.status,
                'platform_url': r.platform_url,
                'error_message': r.error_message,
                'published_at': str(r.published_at) if r.published_at else ''
            } for r in records]
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/article/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """获取单篇文章详情（用于预览和编辑）"""
    try:
        session = get_session()
        article = session.query(GeneratedArticle).filter_by(id=article_id).first()
        session.close()

        if not article:
            return jsonify({'code': 404, 'msg': '文章不存在'})

        return jsonify({
            'code': 0,
            'data': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'keywords': json.loads(article.keywords) if article.keywords else [],
                'image_description': article.image_description or '',
                'status': article.status,
                'created_at': str(article.created_at) if article.created_at else ''
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/article/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """编辑文章"""
    data = request.json
    try:
        session = get_session()
        article = session.query(GeneratedArticle).filter_by(id=article_id).first()

        if not article:
            session.close()
            return jsonify({'code': 404, 'msg': '文章不存在'})

        # 更新字段
        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'keywords' in data:
            article.keywords = json.dumps(data['keywords'], ensure_ascii=False)
        if 'status' in data:
            article.status = data['status']

        session.commit()
        session.close()

        return jsonify({'code': 0, 'msg': '文章已更新'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/article/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """删除文章"""
    try:
        session = get_session()
        article = session.query(GeneratedArticle).filter_by(id=article_id).first()

        if not article:
            session.close()
            return jsonify({'code': 404, 'msg': '文章不存在'})

        session.delete(article)
        session.commit()
        session.close()

        return jsonify({'code': 0, 'msg': '文章已删除'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/article/<int:article_id>/download', methods=['GET'])
def download_article(article_id):
    """下载文章为 Markdown 文件"""
    try:
        session = get_session()
        article = session.query(GeneratedArticle).filter_by(id=article_id).first()
        session.close()

        if not article:
            return jsonify({'code': 404, 'msg': '文章不存在'}), 404

        # 生成 Markdown 内容
        md_content = f"""# {article.title}

**关键词**: {', '.join(json.loads(article.keywords) if article.keywords else [])}

**创建时间**: {article.created_at}

---

{article.content}
"""

        # 返回文件下载
        from flask import Response
        filename = f"{article_id}_{article.title[:20].replace('/', '_')}.md"
        return Response(
            md_content.encode('utf-8'),
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/export/markdown', methods=['POST'])
def export_markdown():
    """批量导出文章为 Markdown"""
    try:
        data = request.json or {}
        article_ids = data.get('article_ids')
        status = data.get('status')

        exporter = DataExporter()
        export_path = exporter.export_articles_to_markdown(article_ids, status)

        return jsonify({
            'code': 0,
            'msg': f'导出完成：{export_path}',
            'data': {'path': export_path}
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/export/json', methods=['POST'])
def export_json():
    """批量导出文章为 JSON"""
    try:
        data = request.json or {}
        article_ids = data.get('article_ids')
        status = data.get('status')

        exporter = DataExporter()
        filepath = exporter.export_articles_to_json(article_ids, status)

        return jsonify({
            'code': 0,
            'msg': f'导出完成：{filepath}',
            'data': {'path': filepath}
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/export/all', methods=['GET'])
def export_all():
    """导出所有数据"""
    try:
        exporter = DataExporter()
        result = exporter.export_all_data()

        return jsonify({
            'code': 0,
            'msg': '全量数据导出完成',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


# ==================== 系统设置 API ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """获取系统设置"""
    try:
        import yaml
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        # 添加 LLM 和分发器配置
        return jsonify({
            'code': 0,
            'data': settings
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """保存系统设置"""
    try:
        data = request.json
        import yaml

        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)

        # 保存 LLM 配置
        if 'llm' in data:
            settings['llm'] = data['llm']

        # 保存分发器配置
        if 'distributors' in data:
            settings['distributors'] = data['distributors']

        # 写回配置文件
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(settings, f, ensure_ascii=False, allow_unicode=True)

        return jsonify({
            'code': 0,
            'msg': '设置已保存'
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
