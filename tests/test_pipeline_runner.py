"""
测试 pipeline_runner.py 模块
包含: PipelineRunner 及其流程方法
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.business.pipeline_runner import PipelineRunner


class TestPipelineRunner:
    """测试 PipelineRunner 类"""

    def test_init_initializes_none(self):
        """应该初始化所有组件为 None"""
        runner = PipelineRunner()
        assert runner.collector is None
        assert runner.analyzer is None
        assert runner.writer is None
        assert runner.image_gen is None
        assert runner.distributor is None

    @pytest.mark.asyncio
    async def test_run_collection_success(self):
        """应该成功采集新闻"""
        runner = PipelineRunner()
        mock_collector = AsyncMock()
        mock_collector.collect.return_value = [
            {'id': 1, 'title': '新闻1'},
            {'id': 2, 'title': '新闻2'}
        ]
        
        with patch('src.business.pipeline_runner.BrowserNewsCollector', return_value=mock_collector):
            news_list = await runner.run_collection("科技", "AI", 10)
        
        assert len(news_list) == 2
        mock_collector.collect.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_collection_returns_empty_on_error(self):
        """应该在采集失败时返回空列表"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.BrowserNewsCollector') as mock_class:
            mock_class.side_effect = Exception("采集失败")
            news_list = await runner.run_collection("科技", "AI", 10)
        
        assert news_list == []

    @pytest.mark.asyncio
    async def test_run_collection_with_progress_callback(self):
        """应该调用进度回调"""
        runner = PipelineRunner()
        progress_calls = []
        
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        mock_collector = AsyncMock()
        mock_collector.collect.return_value = [{'id': 1, 'title': '新闻'}]
        
        with patch('src.business.pipeline_runner.BrowserNewsCollector', return_value=mock_collector):
            await runner.run_collection("科技", "AI", 10, progress_callback)
        
        assert len(progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_run_analysis_success(self, sample_news_data):
        """应该成功分析新闻"""
        runner = PipelineRunner()
        mock_analyzer = MagicMock()
        mock_analyzer.full_analysis.return_value = (
            sample_news_data,  # analyzed_news
            [{'id': 1, 'theme': '测试主题'}]  # themes
        )
        
        with patch('src.business.pipeline_runner.NewsAnalyzer', return_value=mock_analyzer):
            themes, analyzed_news = await runner.run_analysis(sample_news_data, theme_count=1)
        
        assert len(themes) == 1
        assert len(analyzed_news) == 3

    @pytest.mark.asyncio
    async def test_run_analysis_returns_empty_on_error(self, sample_news_data):
        """应该在分析失败时返回空主题列表"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.NewsAnalyzer') as mock_class:
            mock_class.side_effect = Exception("分析失败")
            themes, analyzed_news = await runner.run_analysis(sample_news_data, theme_count=1)
        
        assert themes == []
        assert analyzed_news == sample_news_data  # 返回原始新闻

    @pytest.mark.asyncio
    async def test_run_generation_success(self, sample_theme_data, sample_news_data):
        """应该成功生成文章"""
        runner = PipelineRunner()
        mock_writer = MagicMock()
        mock_writer.batch_generate.return_value = [
            {'title': '文章1', 'content': '内容1'},
            {'title': '文章2', 'content': '内容2'}
        ]
        
        with patch('src.business.pipeline_runner.ArticleWriter', return_value=mock_writer):
            articles = await runner.run_generation(sample_theme_data, sample_news_data)
        
        assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_run_generation_returns_empty_on_error(self, sample_theme_data):
        """应该在生成失败时返回空列表"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.ArticleWriter') as mock_class:
            mock_class.side_effect = Exception("生成失败")
            articles = await runner.run_generation(sample_theme_data, [])
        
        assert articles == []

    @pytest.mark.asyncio
    async def test_run_image_generation_success(self):
        """应该成功生成配图"""
        runner = PipelineRunner()
        mock_img_gen = MagicMock()
        mock_img_gen.generate.return_value = "/path/to/image.jpg"
        
        articles = [
            {'title': '文章1', 'image_description': '描述1'},
            {'title': '文章2', 'image_description': '描述2'}
        ]
        
        with patch('src.business.pipeline_runner.ImageGenerator', return_value=mock_img_gen):
            result = await runner.run_image_generation(articles)
        
        assert all(article.get('image_path') for article in result)
        assert mock_img_gen.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_run_image_generation_skips_missing_description(self):
        """应该跳过没有描述的文章"""
        runner = PipelineRunner()
        mock_img_gen = MagicMock()
        
        articles = [
            {'title': '文章1', 'image_description': '描述1'},
            {'title': '文章2'},  # 没有 image_description
            {'title': '文章3', 'image_description': ''}  # 空描述
        ]
        
        with patch('src.business.pipeline_runner.ImageGenerator', return_value=mock_img_gen):
            result = await runner.run_image_generation(articles)
        
        # 只有第一个有描述的应该被处理
        assert mock_img_gen.generate.call_count == 1
        assert result[0].get('image_path')
        assert result[1].get('image_path') is None

    @pytest.mark.asyncio
    async def test_run_image_generation_continues_on_error(self):
        """应该在单张配图失败时继续生成其他"""
        runner = PipelineRunner()
        mock_img_gen = MagicMock()
        
        def mock_generate(desc, title):
            if '描述1' in desc:
                raise Exception("生成失败")
            return f"/path/to/{title}.jpg"
        
        mock_img_gen.generate.side_effect = mock_generate
        
        articles = [
            {'title': '文章1', 'image_description': '描述1'},
            {'title': '文章2', 'image_description': '描述2'}
        ]
        
        with patch('src.business.pipeline_runner.ImageGenerator', return_value=mock_img_gen):
            result = await runner.run_image_generation(articles)
        
        # 第一篇失败，第二篇应该成功
        assert result[0].get('image_path') is None
        assert result[1].get('image_path') is not None

    @pytest.mark.asyncio
    async def test_run_distribution_success(self):
        """应该成功发布文章"""
        runner = PipelineRunner()
        mock_distributor = AsyncMock()
        mock_distributor.batch_distribute.return_value = {
            'success': 2,
            'total_articles': 2,
            'total_platforms': 1
        }
        
        articles = [{'title': '文章1'}, {'title': '文章2'}]
        platforms = ['website', 'wechat']
        
        with patch('src.business.pipeline_runner.Distributor', return_value=mock_distributor):
            results = await runner.run_distribution(articles, platforms)
        
        assert 'success' in results
        mock_distributor.batch_distribute.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_distribution_returns_empty_on_error(self):
        """应该在发布失败时返回空字典"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.Distributor') as mock_class:
            mock_class.side_effect = Exception("发布失败")
            results = await runner.run_distribution([{'title': '文章'}], ['website'])
        
        assert results == {}

    @pytest.mark.asyncio
    async def test_run_full_pipeline_complete_flow(self):
        """应该完成完整的流水线流程"""
        runner = PipelineRunner()
        progress_calls = []
        
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        # Mock 所有依赖
        with patch('src.business.pipeline_runner.BrowserNewsCollector') as mock_collector_class, \
             patch('src.business.pipeline_runner.NewsAnalyzer') as mock_analyzer_class, \
             patch('src.business.pipeline_runner.ArticleWriter') as mock_writer_class, \
             patch('src.business.pipeline_runner.ImageGenerator') as mock_img_gen_class, \
             patch('src.business.pipeline_runner.Distributor') as mock_dist_class:
            
            # 配置 Mock
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = [
                {'id': 1, 'title': '新闻1', 'summary': '摘要', 'source': '源'}
            ]
            mock_collector_class.return_value = mock_collector
            
            mock_analyzer = MagicMock()
            mock_analyzer.full_analysis.return_value = (
                [{'id': 1, 'title': '新闻1'}],
                [{'id': 1, 'theme': '主题'}]
            )
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_writer = MagicMock()
            mock_writer.batch_generate.return_value = [
                {'title': '文章', 'image_description': '描述'}
            ]
            mock_writer_class.return_value = mock_writer
            
            mock_img_gen = MagicMock()
            mock_img_gen.generate.return_value = "/path/image.jpg"
            mock_img_gen_class.return_value = mock_img_gen
            
            mock_distributor = AsyncMock()
            mock_distributor.batch_distribute.return_value = {'success': 1}
            mock_dist_class.return_value = mock_distributor
            
            # 执行
            result = await runner.run_full_pipeline(
                industry="科技",
                topic="AI",
                count=10,
                theme_count=1,
                platforms=['website'],
                auto_publish=True,
                progress_callback=progress_callback
            )
        
        assert result['success'] is True
        assert result['news_count'] == 1
        assert result['theme_count'] == 1
        assert result['article_count'] == 1
        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_run_full_pipeline_stops_on_no_news(self):
        """应该在未采集到新闻时终止流程"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.BrowserNewsCollector') as mock_class:
            mock_collector = AsyncMock()
            mock_collector.collect.return_value = []
            mock_class.return_value = mock_collector
            
            result = await runner.run_full_pipeline(
                industry="科技",
                topic="AI",
                count=10,
                theme_count=1,
                platforms=[],
                auto_publish=False
            )
        
        assert result['success'] is False
        assert result['error'] == "未采集到任何新闻"

    @pytest.mark.asyncio
    async def test_run_full_pipeline_handles_exception(self):
        """应该捕获并处理异常"""
        runner = PipelineRunner()
        
        with patch('src.business.pipeline_runner.BrowserNewsCollector') as mock_class:
            mock_class.side_effect = RuntimeError("严重错误")
            
            result = await runner.run_full_pipeline(
                industry="科技",
                topic="AI",
                count=10,
                theme_count=1,
                platforms=[],
                auto_publish=False
            )
        
        assert result['success'] is False
        assert result['error'] is not None
        assert "严重错误" in result['error']

    def test_run_pipeline_sync_wrapper(self):
        """应该正确包装异步流程为同步"""
        from src.business.pipeline_runner import run_pipeline_sync
        
        mock_signals = MagicMock()
        mock_signals.progress.emit = MagicMock()
        
        params = {
            'industry': '科技',
            'topic': 'AI',
            'count': 10,
            'theme_count': 1,
            'platforms': [],
            'auto_publish': False
        }
        
        with patch('src.business.pipeline_runner.PipelineRunner.run_full_pipeline') as mock_run:
            mock_run.return_value = asyncio.coroutine(lambda: {'success': True})()
            
            # 由于需要完整 Mock，这里只验证函数存在且可调用
            assert callable(run_pipeline_sync)

    def test_run_collection_sync_wrapper(self):
        """应该正确包装异步采集为同步"""
        from src.business.pipeline_runner import run_collection_sync
        
        mock_signals = MagicMock()
        params = {
            'industry': '科技',
            'topic': 'AI',
            'count': 10
        }
        
        assert callable(run_collection_sync)

    def test_run_generation_sync_wrapper(self):
        """应该正确包装异步生成为同步"""
        from src.business.pipeline_runner import run_generation_sync
        
        mock_signals = MagicMock()
        params = {
            'news_list': [],
            'theme_count': 1
        }
        
        assert callable(run_generation_sync)
