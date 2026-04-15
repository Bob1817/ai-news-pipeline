"""
测试 article_writer.py 模块
包含: ArticleWriter
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.generator.article_writer import ArticleWriter


class TestArticleWriter:
    """测试 ArticleWriter 类"""

    def test_prepare_facts_formats_news(self):
        """应该正确格式化新闻素材"""
        writer = ArticleWriter()
        news_list = [
            {
                'title': '新闻标题1',
                'source': '新浪科技',
                'publish_time': '2024-01-15',
                'summary': '新闻摘要1'
            },
            {
                'title': '新闻标题2',
                'source': '网易科技',
                'publish_time': '2024-01-14',
                'summary': '新闻摘要2'
            }
        ]
        
        facts_text = writer._prepare_facts(news_list)
        
        assert '【素材1】' in facts_text
        assert '新闻标题1' in facts_text
        assert '新浪科技' in facts_text
        assert '【素材2】' in facts_text

    def test_prepare_facts_handles_missing_fields(self):
        """应该能处理缺少字段的新闻"""
        writer = ArticleWriter()
        news_list = [{}]
        
        facts_text = writer._prepare_facts(news_list)
        
        assert '【素材1】' in facts_text
        assert '无标题' in facts_text
        assert '未知' in facts_text

    def test_generate_keywords_basic(self):
        """应该能从主题和新闻中生成关键词"""
        writer = ArticleWriter()
        theme_name = "人工智能"
        related_news = [
            {'title': '人工智能技术实现新突破'},
            {'title': 'AI产业迎来新机遇'}
        ]
        
        keywords = writer._generate_keywords(theme_name, related_news)
        
        assert isinstance(keywords, list)
        assert '人工智能' in keywords
        assert len(keywords) > 0

    def test_generate_keywords_extracts_from_titles(self):
        """应该能从新闻标题中提取中文词汇"""
        writer = ArticleWriter()
        theme_name = "科技创新"
        related_news = [
            {'title': '芯片技术重大突破'},
            {'title': '5G网络覆盖全国'}
        ]
        
        keywords = writer._generate_keywords(theme_name, related_news)
        
        # 应该包含从标题中提取的词
        assert any('芯片' in kw or '技术' in kw or '突破' in kw for kw in keywords)

    def test_generate_keywords_deduplicates(self):
        """应该去重关键词"""
        writer = ArticleWriter()
        theme_name = "AI"
        related_news = [
            {'title': 'AI技术发展'},
            {'title': 'AI技术突破'},
            {'title': 'AI产业前景'}
        ]
        
        keywords = writer._generate_keywords(theme_name, related_news)
        
        # 去重后不应有重复项
        assert len(keywords) == len(set(keywords))

    def test_generate_keywords_limits_to_15(self):
        """应该限制关键词数量不超过15个"""
        writer = ArticleWriter()
        theme_name = "测试"
        # 创建大量新闻以生成很多关键词
        related_news = [
            {'title': f'新闻标题{i}关于测试的内容'}
            for i in range(20)
        ]
        
        keywords = writer._generate_keywords(theme_name, related_news)
        
        assert len(keywords) <= 15

    def test_extract_title_from_first_line(self):
        """应该从第一行提取标题"""
        writer = ArticleWriter()
        content = "这是一篇新闻的标题\n\n这是正文内容..."
        
        title = writer._extract_title(content)
        
        assert title == "这是一篇新闻的标题"

    def test_extract_title_removes_prefixes(self):
        """应该移除标题前缀标记"""
        writer = ArticleWriter()
        
        # 测试不同前缀
        test_cases = [
            ("标题：实际标题", "实际标题"),
            ("# 带井号的标题", "带井号的标题"),
            ("**加粗的标题**", "加粗的标题"),
        ]
        
        for content, expected in test_cases:
            title = writer._extract_title(content)
            assert title == expected

    def test_extract_title_handles_empty_content(self):
        """应该对空内容返回默认标题"""
        writer = ArticleWriter()
        
        title = writer._extract_title("")
        
        assert title == "未命名文章"

    def test_extract_title_limits_length(self):
        """应该限制标题长度不超过100字符"""
        writer = ArticleWriter()
        long_title = "x" * 150
        
        title = writer._extract_title(long_title)
        
        assert len(title) <= 100

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_summary_calls_llm(self):
        """应该调用 LLM 生成摘要"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = "这是一篇摘要"
        
        summary = writer._generate_summary("这是一篇很长的文章内容" * 100)
        
        writer.llm.chat.assert_called_once()
        assert "摘要" in summary

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_summary_truncates_to_200(self):
        """应该限制摘要长度不超过200字符"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = "x" * 300
        
        summary = writer._generate_summary("测试内容")
        
        assert len(summary) <= 200

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_summary_returns_content_fallback(self):
        """应该在 LLM 返回空时使用内容作为摘要"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = ""
        
        content = "这是一篇测试文章内容"
        summary = writer._generate_summary(content)
        
        assert summary == content[:200]

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_image_description_calls_llm(self):
        """应该调用 LLM 生成配图描述"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = "A professional news photo..."
        
        desc = writer._generate_image_description("测试标题", "测试内容")
        
        writer.llm.chat.assert_called_once()
        assert isinstance(desc, str)

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_image_description_returns_default(self):
        """应该在 LLM 返回空时返回默认描述"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = ""
        
        desc = writer._generate_image_description("Test Title", "content")
        
        assert "Test Title" in desc

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    @patch('src.generator.article_writer.save_generated_article')
    @patch('src.generator.article_writer.get_session')
    def test_generate_article_success(self, mock_get_session, mock_save, temp_dir):
        """应该成功生成文章"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.side_effect = [
            "这是一篇完整的新闻稿件内容，包含标题和正文。",  # 文章生成
            "摘要内容",  # 摘要生成
            "A news photo description"  # 配图描述
        ]
        
        theme = {
            'id': 1,
            'theme': '测试主题',
            'description': '测试主题描述',
            'related_news_ids': [1, 2, 3]
        }
        source_news = [
            {'id': 1, 'title': '新闻1', 'source': '源1', 'summary': '摘要1'},
            {'id': 2, 'title': '新闻2', 'source': '源2', 'summary': '摘要2'},
            {'id': 3, 'title': '新闻3', 'source': '源3', 'summary': '摘要3'},
        ]
        
        result = writer.generate_article(theme, source_news)
        
        assert result is not None
        assert 'title' in result
        assert 'content' in result
        assert 'keywords' in result
        assert 'theme' in result
        assert result['theme'] == '测试主题'
        assert 'word_count' in result

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    def test_generate_article_returns_none_on_llm_failure(self):
        """应该在 LLM 调用失败时返回 None"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.return_value = ""  # LLM 返回空
        
        theme = {'id': 1, 'theme': '测试'}
        source_news = [{'id': 1, 'title': '新闻'}]
        
        result = writer.generate_article(theme, source_news)
        
        assert result is None

    @patch.object(ArticleWriter, '__init__', lambda self: None)
    @patch('src.generator.article_writer.save_generated_article')
    def test_generate_article_continues_on_db_error(self, mock_save, temp_dir):
        """应该在数据库保存失败时继续返回文章数据"""
        writer = ArticleWriter()
        writer.llm = MagicMock()
        writer.llm.chat.side_effect = [
            "测试文章内容",
            "摘要",
            "配图描述"
        ]
        mock_save.side_effect = Exception("数据库错误")
        
        theme = {'id': 1, 'theme': '测试主题'}
        source_news = [{'id': 1, 'title': '新闻'}]
        
        # 不应抛出异常
        result = writer.generate_article(theme, source_news)
        
        assert result is not None
        assert 'title' in result

    def test_batch_generate_multiple_themes(self):
        """应该批量生成多个主题文章"""
        with patch.object(ArticleWriter, 'generate_article') as mock_generate:
            mock_generate.return_value = {
                'title': '测试文章',
                'content': '内容'
            }
            
            writer = ArticleWriter()
            themes = [
                {'id': 1, 'theme': '主题1'},
                {'id': 2, 'theme': '主题2'},
                {'id': 3, 'theme': '主题3'}
            ]
            source_news = [{'id': 1, 'title': '新闻'}]
            
            articles = writer.batch_generate(themes, source_news)
            
            assert len(articles) == 3
            assert mock_generate.call_count == 3

    def test_batch_generate_skips_failed_articles(self):
        """应该跳过生成失败的文章"""
        def mock_generate(theme, *args, **kwargs):
            if theme['id'] == 2:
                return None
            return {'title': f"文章{theme['id']}"}
        
        with patch.object(ArticleWriter, 'generate_article', side_effect=mock_generate):
            writer = ArticleWriter()
            themes = [
                {'id': 1, 'theme': '主题1'},
                {'id': 2, 'theme': '主题2'},
                {'id': 3, 'theme': '主题3'}
            ]
            source_news = []
            
            articles = writer.batch_generate(themes, source_news)
            
            assert len(articles) == 2  # 只有 2 篇成功
