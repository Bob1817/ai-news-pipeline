"""
测试 distributor.py 模块
包含: Distributor
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.distributor.distributor import Distributor


class TestDistributor:
    """测试 Distributor 类"""

    def test_init_creates_publishers(self):
        """应该初始化时创建所有发布者"""
        distributor = Distributor()
        assert 'website' in distributor.publishers
        assert 'wechat' in distributor.publishers

    @pytest.mark.asyncio
    async def test_distribute_to_single_platform(self):
        """应该向单个平台分发文章"""
        distributor = Distributor()
        
        # Mock publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish.return_value = {
            'platform': 'website',
            'success': True,
            'url': 'https://example.com/article'
        }
        mock_publisher.enabled = True
        distributor.publishers['website'] = mock_publisher
        
        article = {'title': '测试文章', 'content': '内容'}
        platforms = ['website']
        
        results = await distributor.distribute(article, platforms)
        
        assert len(results) == 1
        assert results[0]['success'] is True
        mock_publisher.publish.assert_called_once_with(article)

    @pytest.mark.asyncio
    async def test_distribute_to_multiple_platforms(self):
        """应该向多个平台分发文章"""
        distributor = Distributor()
        
        # Mock publishers
        mock_website = AsyncMock()
        mock_website.publish.return_value = {'platform': 'website', 'success': True}
        mock_website.enabled = True
        
        mock_wechat = AsyncMock()
        mock_wechat.publish.return_value = {'platform': 'wechat', 'success': True}
        mock_wechat.enabled = True
        
        distributor.publishers['website'] = mock_website
        distributor.publishers['wechat'] = mock_wechat
        
        article = {'title': '测试文章'}
        platforms = ['website', 'wechat']
        
        results = await distributor.distribute(article, platforms)
        
        assert len(results) == 2
        assert mock_website.publish.call_count == 1
        assert mock_wechat.publish.call_count == 1

    @pytest.mark.asyncio
    async def test_distribute_unknown_platform(self):
        """应该对未知平台返回失败"""
        distributor = Distributor()
        
        article = {'title': '测试文章'}
        platforms = ['unknown_platform']
        
        results = await distributor.distribute(article, platforms)
        
        assert len(results) == 1
        assert results[0]['success'] is False
        assert results[0]['error'] == '未知平台'

    @pytest.mark.asyncio
    async def test_distribute_disabled_platform(self):
        """应该对未启用的平台返回失败"""
        distributor = Distributor()
        
        # Mock publisher 为未启用状态
        mock_publisher = AsyncMock()
        mock_publisher.enabled = False
        distributor.publishers['website'] = mock_publisher
        
        article = {'title': '测试文章'}
        platforms = ['website']
        
        results = await distributor.distribute(article, platforms)
        
        assert len(results) == 1
        assert results[0]['success'] is False
        assert results[0]['error'] == '平台未启用'

    @pytest.mark.asyncio
    async def test_distribute_handles_publish_failure(self):
        """应该在发布失败时继续其他平台"""
        distributor = Distributor()
        
        mock_website = AsyncMock()
        mock_website.publish.return_value = {'platform': 'website', 'success': False, 'error': '错误'}
        mock_website.enabled = True
        
        mock_wechat = AsyncMock()
        mock_wechat.publish.return_value = {'platform': 'wechat', 'success': True}
        mock_wechat.enabled = True
        
        distributor.publishers['website'] = mock_website
        distributor.publishers['wechat'] = mock_wechat
        
        article = {'title': '测试文章'}
        platforms = ['website', 'wechat']
        
        results = await distributor.distribute(article, platforms)
        
        assert len(results) == 2
        # website 失败，wechat 成功
        assert results[0]['success'] is False
        assert results[1]['success'] is True

    @pytest.mark.asyncio
    async def test_batch_distribute_multiple_articles(self):
        """应该批量分发多篇文章"""
        distributor = Distributor()
        
        # Mock publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish.return_value = {'platform': 'website', 'success': True}
        mock_publisher.enabled = True
        distributor.publishers['website'] = mock_publisher
        
        articles = [
            {'title': '文章1'},
            {'title': '文章2'},
            {'title': '文章3'}
        ]
        platforms = ['website']
        
        results = await distributor.batch_distribute(articles, platforms)
        
        assert results['total_articles'] == 3
        assert results['total_platforms'] == 1
        assert results['success'] == 3
        assert results['failed'] == 0

    @pytest.mark.asyncio
    async def test_batch_distribute_tracks_failures(self):
        """应该追踪失败数量"""
        distributor = Distributor()
        
        call_count = [0]
        async def mock_publish(article):
            call_count[0] += 1
            # 第二篇失败
            if call_count[0] == 2:
                return {'platform': 'website', 'success': False, 'error': '错误'}
            return {'platform': 'website', 'success': True}
        
        mock_publisher = AsyncMock()
        mock_publisher.publish.side_effect = mock_publish
        mock_publisher.enabled = True
        distributor.publishers['website'] = mock_publisher
        
        articles = [
            {'title': '文章1'},
            {'title': '文章2'},
            {'title': '文章3'}
        ]
        platforms = ['website']
        
        results = await distributor.batch_distribute(articles, platforms)
        
        assert results['success'] == 2
        assert results['failed'] == 1

    @pytest.mark.asyncio
    async def test_batch_distribute_returns_details(self):
        """应该返回每篇文章的详细结果"""
        distributor = Distributor()
        
        mock_publisher = AsyncMock()
        mock_publisher.publish.return_value = {'platform': 'website', 'success': True}
        mock_publisher.enabled = True
        distributor.publishers['website'] = mock_publisher
        
        articles = [{'title': '文章1'}, {'title': '文章2'}]
        platforms = ['website']
        
        results = await distributor.batch_distribute(articles, platforms)
        
        assert 'details' in results
        assert len(results['details']) == 2
        assert results['details'][0]['title'] == '文章1'
        assert 'results' in results['details'][0]

    @pytest.mark.asyncio
    async def test_distribute_includes_sleep_interval(self):
        """应该在平台之间包含发布间隔"""
        distributor = Distributor()
        
        with patch('src.distributor.distributor.asyncio.sleep') as mock_sleep:
            mock_publisher = AsyncMock()
            mock_publisher.publish.return_value = {'success': True}
            mock_publisher.enabled = True
            distributor.publishers['website'] = mock_publisher
            distributor.publishers['wechat'] = mock_publisher
            
            article = {'title': '测试文章'}
            platforms = ['website', 'wechat']
            
            await distributor.distribute(article, platforms)
            
            # 应该调用 sleep （每个平台发布后）
            assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_batch_distribute_includes_article_interval(self):
        """应该在文章之间包含间隔"""
        distributor = Distributor()
        
        with patch('src.distributor.distributor.asyncio.sleep') as mock_sleep:
            mock_publisher = AsyncMock()
            mock_publisher.publish.return_value = {'success': True}
            mock_publisher.enabled = True
            distributor.publishers['website'] = mock_publisher
            
            articles = [{'title': '文章1'}, {'title': '文章2'}]
            platforms = ['website']
            
            await distributor.batch_distribute(articles, platforms)
            
            # 应该调用 sleep （发布间隔 + 文章间隔）
            assert mock_sleep.call_count >= 1
