#!/usr/bin/env python3
"""
AI新闻自动化系统 — 主入口
支持命令行模式和Web服务模式
"""
import argparse
import asyncio
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"


def _print_missing_dependency_help(error: ModuleNotFoundError):
    """输出更友好的依赖缺失提示，避免直接抛出难读的堆栈"""
    missing_module = getattr(error, "name", "unknown")
    print(f"缺少 Python 依赖模块：{missing_module}", file=sys.stderr)
    print("", file=sys.stderr)
    print("可选修复方式：", file=sys.stderr)
    if VENV_PYTHON.exists():
        print(
            f"1. 使用项目虚拟环境启动：{VENV_PYTHON} main.py web --port 8080",
            file=sys.stderr
        )
        print(
            f"2. 先安装依赖：{VENV_PYTHON} -m pip install -r requirements.txt",
            file=sys.stderr
        )
    print(
        "3. 或者在当前 Python 环境安装依赖：python3 -m pip install -r requirements.txt",
        file=sys.stderr
    )


# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from loguru import logger
    from dotenv import load_dotenv
except ModuleNotFoundError as e:
    _print_missing_dependency_help(e)
    raise SystemExit(1) from e

load_dotenv()


def run_web_server(port: int = 8080):
    """启动Web管理后台"""
    try:
        from web.app import app
    except ModuleNotFoundError as e:
        _print_missing_dependency_help(e)
        raise SystemExit(1) from e
    logger.info(f"Web管理后台启动: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)


async def run_pipeline(
    industry: str,
    topic: str = "",
    count: int = 10,
    theme_count: int = 3,
    platforms: list = None,
    auto_publish: bool = False
):
    """命令行模式执行完整流程"""
    try:
        from src.collector.browser_collector import BrowserNewsCollector
        from src.collector.analyzer import NewsAnalyzer
        from src.generator.article_writer import ArticleWriter
        from src.generator.image_generator import ImageGenerator
        from src.distributor.distributor import Distributor
    except ModuleNotFoundError as e:
        _print_missing_dependency_help(e)
        raise SystemExit(1) from e

    if platforms is None:
        platforms = ['website']

    logger.info("=" * 60)
    logger.info("AI新闻自动化流程启动")
    logger.info(f"行业: {industry}, 主题: {topic or '无'}, 数量: {count}")
    logger.info("=" * 60)

    # ===== 第1步：采集 =====
    logger.info("[1/4] 正在采集新闻...")
    collector = BrowserNewsCollector()
    news_list = await collector.collect(industry, topic, count)
    logger.info(f"采集完成: {len(news_list)} 条新闻")

    if not news_list:
        logger.error("未采集到任何新闻，流程终止")
        return

    # ===== 第2步：分析 =====
    logger.info("[2/4] 正在分析主题...")
    analyzer = NewsAnalyzer()
    analyzed_news, themes = analyzer.full_analysis(news_list, theme_count)
    logger.info(f"提炼出 {len(themes)} 个主题:")
    for t in themes:
        logger.info(f"  - {t['theme']}")

    # ===== 第3步：生成 =====
    logger.info("[3/4] 正在生成文章...")
    writer = ArticleWriter()
    articles = writer.batch_generate(themes, analyzed_news)

    # 生成配图
    img_gen = ImageGenerator()
    for article in articles:
        if article.get('image_description'):
            img_path = img_gen.generate(
                article['image_description'],
                article.get('title', '')
            )
            article['image_path'] = img_path

    logger.info(f"生成完成: {len(articles)} 篇文章")
    for a in articles:
        logger.info(f"  - 《{a['title']}》({a.get('word_count', 0)}字)")

    # ===== 第4步：分发 =====
    if auto_publish:
        logger.info("[4/4] 正在分发文章...")
        distributor = Distributor()
        results = await distributor.batch_distribute(articles, platforms)
        logger.info(f"分发完成: {results}")
    else:
        logger.info("[4/4] 跳过自动发布（使用 --auto-publish 启用）")
        logger.info("生成的文章已保存到数据库，可通过Web界面发布")

    logger.info("=" * 60)
    logger.info("全流程执行完毕！")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='AI新闻自动化系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动Web管理后台
  python main.py web --port 8080

  # 命令行执行完整流程
  python main.py run --industry "科技" --topic "人工智能" --count 10

  # 自动发布到指定平台
  python main.py run --industry "财经" --count 20 --themes 5 --auto-publish --platforms website wechat
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='运行模式')

    # Web模式
    web_parser = subparsers.add_parser('web', help='启动Web管理后台')
    web_parser.add_argument('--port', type=int, default=8080, help='服务端口 (默认: 8080)')

    # 命令行模式
    run_parser = subparsers.add_parser('run', help='命令行执行自动化流程')
    run_parser.add_argument('--industry', required=True, help='行业 (必选)')
    run_parser.add_argument('--topic', default='', help='主题关键词 (选填)')
    run_parser.add_argument('--count', type=int, default=10, help='采集数量 (默认: 10)')
    run_parser.add_argument('--themes', type=int, default=3, help='提炼主题数 (默认: 3)')
    run_parser.add_argument('--auto-publish', action='store_true', help='自动发布')
    run_parser.add_argument('--platforms', nargs='+', default=['website'],
                            choices=['website', 'wechat'],
                            help='发布平台')

    args = parser.parse_args()

    if args.command == 'web':
        run_web_server(args.port)
    elif args.command == 'run':
        asyncio.run(run_pipeline(
            industry=args.industry,
            topic=args.topic,
            count=args.count,
            theme_count=args.themes,
            platforms=args.platforms,
            auto_publish=args.auto_publish
        ))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
