"""
SEO关键词优化模块
借鉴关键词矩阵挖掘方法(citation:7)，为文章生成最优关键词组合
"""
from typing import List, Dict
from collections import Counter
import re
from loguru import logger

from src.collector.analyzer import LLMClient


class SEOOptimizer:
    """SEO关键词优化器"""

    def __init__(self):
        self.llm = LLMClient()

    def generate_keyword_matrix(
        self,
        theme: str,
        industry: str,
        related_news: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        生成关键词矩阵(citation:7)

        返回包含以下类别的关键词:
        - core: 核心关键词
        - long_tail: 长尾关键词
        - semantic: 语义关联词
        - trending: 热搜/趋势词
        """
        # 1. 从相关新闻中提取高频词
        all_text = ' '.join([
            f"{n.get('title', '')} {n.get('summary', '')}"
            for n in related_news
        ])
        high_freq_words = self._extract_high_freq_words(all_text)

        # 2. 使用LLM拓展关键词
        system_prompt = "你是一位SEO优化专家，精通中文搜索引擎优化。"
        user_prompt = f"""基于以下信息，为一篇关于「{theme}」的{industry}类新闻文章生成SEO关键词矩阵。

高频词参考：{', '.join(high_freq_words[:10])}

请按以下分类生成关键词（每类5-8个）：

1. 核心关键词（与主题直接相关的2-4字短词）
2. 长尾关键词（5-10字的搜索短语）
3. 语义关联词（与主题相关但不直接包含主题词的词汇）
4. 趋势热词（当前流行的表达方式）

请以JSON格式返回：
{{
  "core": ["关键词1", "关键词2"],
  "long_tail": ["长尾词1", "长尾词2"],
  "semantic": ["关联词1", "关联词2"],
  "trending": ["热词1", "热词2"]
}}"""

        response = self.llm.chat(system_prompt, user_prompt)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1:
                import json
                matrix = json.loads(response[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except Exception:
            # 使用默认矩阵
            matrix = {
                'core': [theme, industry] + high_freq_words[:3],
                'long_tail': [
                    f"{theme}最新消息",
                    f"{theme}深度分析",
                    f"{industry}{theme}",
                    f"{theme}发展趋势"
                ],
                'semantic': high_freq_words[3:8] if len(high_freq_words) > 3 else [],
                'trending': [f"{theme}2025", f"{theme}热点"]
            }

        logger.info(f"关键词矩阵生成完成: {sum(len(v) for v in matrix.values())} 个关键词")
        return matrix

    def optimize_article_keywords(
        self,
        article_content: str,
        keyword_matrix: Dict[str, List[str]]
    ) -> List[str]:
        """
        从关键词矩阵中选出最适合文章的关键词

        返回: 优化后的关键词列表（按优先级排序）
        """
        selected = []

        # 核心关键词必须包含
        selected.extend(keyword_matrix.get('core', []))

        # 检查长尾关键词在文章中的出现情况
        content_lower = article_content.lower()
        for kw in keyword_matrix.get('long_tail', []):
            if kw.lower() in content_lower:
                selected.append(kw)

        # 添加语义关联词中出现频率高的
        for kw in keyword_matrix.get('semantic', []):
            if kw.lower() in content_lower:
                selected.append(kw)

        # 添加趋势词
        selected.extend(keyword_matrix.get('trending', [])[:2])

        # 去重
        seen = set()
        unique = []
        for kw in selected:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)

        return unique[:15]  # 最多15个关键词

    def _extract_high_freq_words(self, text: str, top_n: int = 20) -> List[str]:
        """提取高频词（简易中文分词）"""
        # 提取2-4字的中文词组
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)

        # 过滤常见停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '它', '们', '那', '些', '什么', '这个', '那个', '可以', '已经',
            '因为', '所以', '但是', '而且', '或者', '如果', '虽然', '这样'
        }
        filtered = [w for w in words if w not in stopwords and len(w) >= 2]

        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]
