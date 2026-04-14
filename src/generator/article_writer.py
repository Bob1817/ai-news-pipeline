"""
新闻文章自动生成模块
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from src.collector.analyzer import LLMClient
from src.utils.db import save_generated_article, get_session, GeneratedTheme


class ArticleWriter:
    """新闻文章自动生成器"""

    def __init__(self):
        self.llm = LLMClient()

    def generate_article(
        self,
        theme: Dict,
        source_news: List[Dict],
        min_words: int = 800,
        max_words: int = 1500
    ) -> Dict:
        """
        根据主题和源新闻生成一篇文章

        参数:
            theme: 主题信息 {"theme": "...", "description": "...", "related_news_ids": [...]}
            source_news: 源新闻列表
            min_words: 最少字数
            max_words: 最多字数

        返回: 生成的文章数据
        """
        theme_name = theme.get('theme', '未命名主题')
        logger.info(f"正在为主题 [{theme_name}] 生成文章...")

        # 1. 筛选与主题相关的源新闻作为事实素材
        related_news = []
        related_ids = set(theme.get('related_news_ids', []) or [])
        if related_ids:
            related_news = [
                news for news in source_news
                if news.get('id') in related_ids
            ]

        if not related_news:
            related_indices = theme.get('related_news_indices', [])
            for idx in related_indices:
                if 0 < idx <= len(source_news):
                    related_news.append(source_news[idx - 1])

        # 如果没有明确关联，取热度最高的几条
        if not related_news:
            related_news = sorted(
                source_news,
                key=lambda x: x.get('heat_score', 0),
                reverse=True
            )[:5]

        # 2. 准备事实素材
        facts_text = self._prepare_facts(related_news)

        # 3. 生成SEO关键词
        keywords = self._generate_keywords(theme_name, related_news)

        # 4. 构建写作提示词
        system_prompt = """你是一位拥有10年经验的资深新闻记者，擅长撰写客观、深入、可读性强的新闻报道。
你的文章结构清晰，语言精炼，善于用数据和事实说话。"""

        user_prompt = f"""请基于以下事实素材，撰写一篇关于「{theme_name}」的新闻报道。

**事实素材**：
{facts_text}

**写作要求**：
1. **格式规范**：
   - 标题：简洁有力，不超过30字，能概括核心内容
   - 导语：第一段用2-3句话概括最重要的事实
   - 正文：分3-5个段落，每段有明确的小主题，逻辑递进
   - 结尾：总结展望或点明意义

2. **内容要求**：
   - 严格基于提供的事实素材，不编造虚假信息
   - 可以合理补充背景知识和行业上下文
   - 自然融入以下关键词：{', '.join(keywords[:8])}
   - 文章总字数控制在{min_words}-{max_words}字

3. **风格要求**：
   - 客观中立，不带主观情感偏向
   - 语言简洁明了，适合大众阅读
   - 适当使用数据增强说服力

请直接输出完整的新闻稿件（包含标题和正文），不要添加额外说明。"""

        # 5. 调用LLM生成文章
        article_content = self.llm.chat(system_prompt, user_prompt)

        if not article_content:
            logger.error(f"主题 [{theme_name}] 文章生成失败")
            return None

        # 6. 提取标题
        title = self._extract_title(article_content)

        # 7. 生成配图描述
        image_desc = self._generate_image_description(title, article_content)

        # 8. 生成文章摘要
        summary = self._generate_summary(article_content)

        result = {
            'theme': theme_name,
            'theme_id': theme.get('id'),
            'title': title,
            'content': article_content,
            'summary': summary,
            'keywords': keywords,
            'image_description': image_desc,
            'image_path': '',
            'source_references': [n.get('url', '') for n in related_news],
            'word_count': len(article_content),
            'status': 'draft',
            'created_at': datetime.now().isoformat()
        }

        # 9. 保存到数据库
        try:
            save_generated_article({
                'theme_id': theme.get('id'),
                'title': title,
                'content': article_content,
                'keywords': json.dumps(keywords, ensure_ascii=False),
                'image_description': image_desc,
                'status': 'draft',
                'created_at': datetime.now()
            })
        except Exception as e:
            logger.warning(f"保存文章到数据库失败: {e}")

        logger.info(f"文章生成完成: 《{title}》({len(article_content)}字)")
        return result

    def _prepare_facts(self, news_list: List[Dict]) -> str:
        """将新闻列表格式化为事实素材文本"""
        facts = []
        for i, news in enumerate(news_list, 1):
            fact = f"""【素材{i}】
标题：{news.get('title', '无标题')}
来源：{news.get('source', '未知')}
时间：{news.get('publish_time', '未知')}
摘要：{news.get('summary', '无摘要')}
---"""
            facts.append(fact)
        return '\n'.join(facts)

    def _generate_keywords(
        self,
        theme_name: str,
        related_news: List[Dict]
    ) -> List[str]:
        """生成SEO关键词"""
        keywords = [theme_name]

        # 从相关新闻标题中提取高频词
        import re
        from collections import Counter

        all_words = []
        for news in related_news:
            title = news.get('title', '')
            # 简单分词（实际项目可使用jieba）
            words = re.findall(r'[\u4e00-\u9fff]{2,}', title)
            all_words.extend(words)

        # 统计词频
        word_freq = Counter(all_words)
        top_words = [word for word, _ in word_freq.most_common(10)]
        keywords.extend(top_words)

        # 添加长尾关键词
        keywords.extend([
            f"{theme_name}最新动态",
            f"{theme_name}深度分析",
            f"{theme_name}趋势解读",
            "行业热点"
        ])

        # 去重并限制数量
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen and len(kw) >= 2:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:15]

    def _extract_title(self, article_content: str) -> str:
        """从文章内容中提取标题"""
        lines = article_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # 清理可能的标记
                for prefix in ['标题：', '标题:', '#', '**']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                # 去除可能的粗体标记
                line = line.strip('*').strip()
                return line[:100]
        return "未命名文章"

    def _generate_summary(self, article_content: str) -> str:
        """生成文章摘要"""
        system_prompt = "你是一个文本摘要专家。"
        user_prompt = f"""请为以下新闻写一段50-100字的摘要：

{article_content[:2000]}

只返回摘要内容，不要添加其他说明。"""

        summary = self.llm.chat(system_prompt, user_prompt)
        return summary.strip()[:200] if summary else article_content[:200]

    def _generate_image_description(
        self,
        title: str,
        content: str
    ) -> str:
        """生成配图描述（用于文生图）"""
        system_prompt = "你是一位AI绘图提示词专家。"
        user_prompt = f"""请为以下新闻生成一段英文的AI绘图描述（用于Stable Diffusion等工具生成配图）。

新闻标题：{title}
新闻内容前200字：{content[:200]}

要求：
1. 描述一个与新闻主题相关的场景或画面
2. 风格：新闻摄影风格，专业，高质量
3. 用英文写，50-100词
4. 只返回描述，不要添加其他内容"""

        desc = self.llm.chat(system_prompt, user_prompt)
        return desc.strip() if desc else f"Professional news photo about {title}"

    def batch_generate(
        self,
        themes: List[Dict],
        source_news: List[Dict],
        min_words: int = 800,
        max_words: int = 1500
    ) -> List[Dict]:
        """批量生成文章"""
        articles = []
        for theme in themes:
            article = self.generate_article(theme, source_news, min_words, max_words)
            if article:
                articles.append(article)
        logger.info(f"批量生成完成：{len(articles)}/{len(themes)} 篇文章")
        return articles
