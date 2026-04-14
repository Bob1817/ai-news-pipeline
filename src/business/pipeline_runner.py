import asyncio
from loguru import logger

class PipelineRunner:
    def __init__(self):
        self.collector = None
        self.analyzer = None
        self.writer = None
        self.image_gen = None
        self.distributor = None
    
    async def run_full_pipeline(self, industry, topic, count, theme_count, platforms, auto_publish, progress_callback=None):
        result = {
            'success': False,
            'news_count': 0,
            'theme_count': 0,
            'article_count': 0,
            'publish_results': {},
            'error': None
        }
        
        try:
            if progress_callback:
                progress_callback(5, "开始执行自动化流程")
            
            news_list = await self.run_collection(industry, topic, count, progress_callback)
            result['news_count'] = len(news_list)
            
            if not news_list:
                if progress_callback:
                    progress_callback(10, "未采集到任何新闻，流程终止")
                result['error'] = "未采集到任何新闻"
                return result
            
            themes, analyzed_news = await self.run_analysis(news_list, theme_count, progress_callback)
            result['theme_count'] = len(themes)
            
            articles = await self.run_generation(themes, analyzed_news, progress_callback)
            result['article_count'] = len(articles)
            
            if result['article_count'] > 0:
                articles = await self.run_image_generation(articles, progress_callback)
            
            if auto_publish and platforms:
                publish_result = await self.run_distribution(articles, platforms, progress_callback)
                result['publish_results'] = publish_result
            
            result['success'] = True
            
            if progress_callback:
                progress_callback(100, "流程执行完成")
            
        except Exception as e:
            logger.error(f"流程执行失败: {e}")
            if progress_callback:
                progress_callback(0, f"流程执行失败: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    async def run_collection(self, industry, topic, count, progress_callback=None):
        if progress_callback:
            progress_callback(10, f"开始采集[{industry}]新闻...")
        
        from src.collector.browser_collector import BrowserNewsCollector
        
        try:
            collector = BrowserNewsCollector()
            news_list = await collector.collect(
                industry=industry,
                topic=topic,
                count=count,
                headless=True
            )
            
            if progress_callback:
                progress_callback(25, f"采集完成，共{len(news_list)}条新闻")
            
            return news_list
        except Exception as e:
            logger.error(f"采集失败: {e}")
            if progress_callback:
                progress_callback(25, f"采集失败: {str(e)}")
            return []
    
    async def run_analysis(self, news_list, theme_count, progress_callback=None):
        if progress_callback:
            progress_callback(30, "开始分析新闻主题...")
        
        from src.collector.analyzer import NewsAnalyzer
        
        try:
            analyzer = NewsAnalyzer()
            analyzed_news, themes = analyzer.full_analysis(news_list, theme_count)
            
            if progress_callback:
                progress_callback(45, f"分析完成，提炼出{len(themes)}个主题")
            
            return themes, analyzed_news
        except Exception as e:
            logger.error(f"分析失败: {e}")
            if progress_callback:
                progress_callback(45, f"分析失败: {str(e)}")
            return [], news_list
    
    async def run_generation(self, themes, news_list, progress_callback=None):
        if progress_callback:
            progress_callback(50, "开始生成文章...")
        
        from src.generator.article_writer import ArticleWriter
        
        try:
            writer = ArticleWriter()
            articles = writer.batch_generate(themes, news_list)
            
            if progress_callback:
                progress_callback(70, f"文章生成完成，共{len(articles)}篇")
            
            return articles
        except Exception as e:
            logger.error(f"文章生成失败: {e}")
            if progress_callback:
                progress_callback(70, f"文章生成失败: {str(e)}")
            return []
    
    async def run_image_generation(self, articles, progress_callback=None):
        if progress_callback:
            progress_callback(75, "开始生成配图...")
        
        from src.generator.image_generator import ImageGenerator
        
        try:
            img_gen = ImageGenerator()
            generated_count = 0
            
            for article in articles:
                if article.get('image_description'):
                    try:
                        img_path = img_gen.generate(
                            article['image_description'],
                            article.get('title', '')
                        )
                        article['image_path'] = img_path
                        generated_count += 1
                    except Exception as e:
                        logger.warning(f"配图生成失败: {e}")
            
            if progress_callback:
                progress_callback(85, f"配图生成完成，共{generated_count}张")
            
            return articles
        except Exception as e:
            logger.error(f"配图生成失败: {e}")
            if progress_callback:
                progress_callback(85, f"配图生成失败: {str(e)}")
            return articles
    
    async def run_distribution(self, articles, platforms, progress_callback=None):
        if progress_callback:
            progress_callback(90, "开始发布文章...")
        
        from src.distributor.distributor import Distributor
        
        try:
            distributor = Distributor()
            results = await distributor.batch_distribute(articles, platforms)
            
            if progress_callback:
                success_count = results.get('success', 0)
                total = results.get('total_articles', 0) * results.get('total_platforms', 1)
                progress_callback(98, f"发布完成: {success_count}/{total}")
            
            return results
        except Exception as e:
            logger.error(f"发布失败: {e}")
            if progress_callback:
                progress_callback(98, f"发布失败: {str(e)}")
            return {}

def run_pipeline_sync(task_id, params, signals):
    def progress_callback(progress, message):
        signals.progress.emit(progress, message)
    
    industry = params.get('industry', '')
    topic = params.get('topic', '')
    count = params.get('count', 10)
    theme_count = params.get('theme_count', 3)
    platforms = params.get('platforms', [])
    auto_publish = params.get('auto_publish', False)
    
    runner = PipelineRunner()
    result = asyncio.run(runner.run_full_pipeline(
        industry=industry,
        topic=topic,
        count=count,
        theme_count=theme_count,
        platforms=platforms,
        auto_publish=auto_publish,
        progress_callback=progress_callback
    ))
    
    return result

def run_collection_sync(task_id, params, signals):
    def progress_callback(progress, message):
        signals.progress.emit(progress, message)
    
    industry = params.get('industry', '')
    topic = params.get('topic', '')
    count = params.get('count', 10)
    
    runner = PipelineRunner()
    result = asyncio.run(runner.run_collection(
        industry=industry,
        topic=topic,
        count=count,
        progress_callback=progress_callback
    ))
    
    return {'news': result}

def run_generation_sync(task_id, params, signals):
    def progress_callback(progress, message):
        signals.progress.emit(progress, message)
    
    news_list = params.get('news_list', [])
    theme_count = params.get('theme_count', 3)
    
    runner = PipelineRunner()
    themes, analyzed = asyncio.run(runner.run_analysis(news_list, theme_count, progress_callback))
    articles = asyncio.run(runner.run_generation(themes, analyzed, progress_callback))
    
    return {'articles': articles, 'themes': themes}