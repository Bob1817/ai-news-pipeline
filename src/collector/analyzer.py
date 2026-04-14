"""
新闻分析模块：对采集到的新闻进行主题提炼、情感分析等
"""
import json
import os
import hashlib
from typing import List, Dict, Tuple
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class LLMCache:
    """LLM 响应缓存 - 基于文件缓存"""

    def __init__(self, cache_dir: str = "data/llm_cache"):
        cache_path = Path(cache_dir)
        if not cache_path.is_absolute():
            cache_path = PROJECT_ROOT / cache_path
        self.cache_dir = cache_path
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # 缓存有效期（小时）
        self.ttl_hours = int(os.getenv("LLM_CACHE_TTL", "24"))

    def _get_cache_key(self, system_prompt: str, user_prompt: str) -> str:
        """生成缓存键"""
        content = f"{system_prompt}|{user_prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, system_prompt: str, user_prompt: str) -> str | None:
        """从缓存获取结果"""
        cache_key = self._get_cache_key(system_prompt, user_prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            import time
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查缓存是否过期
            if time.time() - data['timestamp'] > self.ttl_hours * 3600:
                cache_file.unlink()
                return None

            return data['response']
        except Exception as e:
            logger.warning(f"读取缓存失败：{e}")
            return None

    def set(self, system_prompt: str, user_prompt: str, response: str):
        """保存结果到缓存"""
        cache_key = self._get_cache_key(system_prompt, user_prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            import time
            data = {
                'timestamp': time.time(),
                'response': response
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"写入缓存失败：{e}")


class LLMClient:
    """LLM 调用客户端（支持本地 Ollama 和 OpenAI 兼容 API）"""

    def __init__(self, use_cache: bool = True):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")

        if self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = os.getenv("OLLAMA_MODEL", "qwen2:7b")
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        # 初始化缓存
        if use_cache:
            self.cache = LLMCache()
        else:
            self.cache = None

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 进行对话"""
        # 检查缓存
        if self.cache:
            cached = self.cache.get(system_prompt, user_prompt)
            if cached:
                logger.info("使用 LLM 缓存结果")
                return cached

        import httpx

        if self.provider == "ollama":
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.7}
            }
        else:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

        try:
            with httpx.Client(timeout=120) as client:
                if self.provider == "ollama":
                    resp = client.post(url, json=payload)
                else:
                    resp = client.post(url, json=payload, headers=headers)

                resp.raise_for_status()
                data = resp.json()

                if self.provider == "ollama":
                    response = data['message']['content']
                else:
                    response = data['choices'][0]['message']['content']

                # 保存到缓存
                if self.cache:
                    self.cache.set(system_prompt, user_prompt, response)

                return response

        except Exception as e:
            logger.error(f"LLM 调用失败：{e}")
            return ""


class NewsAnalyzer:
    """新闻分析器"""

    def __init__(self):
        self.llm = LLMClient()

    def full_analysis(
        self,
        news_list: List[Dict],
        theme_count: int = 3
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        完整分析流程：分析每条新闻 + 提炼主题

        参数:
            news_list: 新闻列表，每条新闻应包含 id, title, summary, source 等字段
            theme_count: 要提炼的主题数量

        返回:
            Tuple[分析后的新闻列表，主题列表]
        """
        if not news_list:
            logger.warning("新闻列表为空，无法分析")
            return [], []

        logger.info(f"开始分析 {len(news_list)} 条新闻，提炼 {theme_count} 个主题")

        # 1. 分析每条新闻（情感、热度等）
        analyzed_news = self._analyze_news_list(news_list)

        # 2. 提炼主题
        themes = self._extract_themes(analyzed_news, theme_count)

        logger.info(f"分析完成：提炼出 {len(themes)} 个主题")
        return analyzed_news, themes

    def _analyze_news_list(self, news_list: List[Dict]) -> List[Dict]:
        """分析新闻列表，为每条新闻添加分析结果"""
        analyzed = []

        for news in news_list:
            analyzed_news = news.copy()

            # 计算热度分数（基于标题长度、关键词等简单规则）
            analyzed_news['heat_score'] = self._calculate_heat_score(news)

            # 情感分析（可选，使用 LLM）
            try:
                sentiment = self._analyze_sentiment(news)
                analyzed_news['sentiment'] = sentiment
            except Exception as e:
                logger.warning(f"情感分析失败：{e}")
                analyzed_news['sentiment'] = 'neutral'

            analyzed.append(analyzed_news)

        return analyzed

    def _calculate_heat_score(self, news: Dict) -> float:
        """计算新闻热度分数（0-100）"""
        score = 50  # 基础分

        # 标题长度影响（适中最好）
        title_len = len(news.get('title', ''))
        if 20 <= title_len <= 50:
            score += 10
        elif title_len > 50:
            score += 5

        # 包含热点关键词加分
        hot_keywords = ['发布', '亮相', '突破', '重磅', '最新', '首次']
        title = news.get('title', '')
        for kw in hot_keywords:
            if kw in title:
                score += 3

        return min(score, 100)

    def _analyze_sentiment(self, news: Dict) -> str:
        """分析新闻情感倾向"""
        system_prompt = "你是一位新闻情感分析专家。请判断新闻的情感倾向，只返回：positive（正面）、neutral（中性）、negative（负面）。"
        user_prompt = f"新闻标题：{news.get('title', '')}\n摘要：{news.get('summary', '')}"

        response = self.llm.chat(system_prompt, user_prompt)
        response = response.strip().lower()

        if 'positive' in response or '正面' in response:
            return 'positive'
        elif 'negative' in response or '负面' in response:
            return 'negative'
        return 'neutral'

    def _extract_themes(
        self,
        analyzed_news: List[Dict],
        theme_count: int
    ) -> List[Dict]:
        """从分析后的新闻中提取主题"""
        if not analyzed_news:
            return []

        # 准备提示词
        news_summary = []
        for i, news in enumerate(analyzed_news[:20], 1):  # 最多分析 20 条
            news_summary.append(
                f"[{i}] {news.get('title', '')} (来源：{news.get('source', '')}, 热度：{news.get('heat_score', 0)})"
            )

        facts_text = '\n'.join(news_summary)

        system_prompt = """你是一位资深的新闻编辑，擅长从大量新闻中提炼出有价值的主题。
请分析提供的新闻列表，提炼出最具代表性和讨论价值的主题。"""

        user_prompt = f"""请分析以下新闻列表，提炼出 {theme_count} 个主题。

新闻列表：
{facts_text}

请按以下 JSON 格式返回主题（不要包含其他内容）：
[
  {{
    "id": 1,
    "theme": "主题名称",
    "description": "主题描述（50-100 字）",
    "related_news_indices": [1, 3, 5]
  }},
  ...
]

要求：
1. 主题名称简洁明了（10 字以内）
2. 描述要概括主题的核心内容
3. related_news_indices 指向相关新闻的索引（从 1 开始）"""

        response = self.llm.chat(system_prompt, user_prompt)

        # 解析响应
        themes = self._parse_themes_response(response, theme_count)

        # 为每个主题分配 ID
        for i, theme in enumerate(themes, 1):
            theme['id'] = i

        return themes

    def _parse_themes_response(self, response: str, expected_count: int) -> List[Dict]:
        """解析 LLM 返回的主题响应"""
        try:
            # 尝试提取 JSON
            json_start = response.find('[')
            json_end = response.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                themes = json.loads(json_str)

                # 验证结构
                valid_themes = []
                for theme in themes:
                    if isinstance(theme, dict) and 'theme' in theme:
                        valid_themes.append(theme)

                if valid_themes:
                    return valid_themes[:expected_count]

        except Exception as e:
            logger.warning(f"解析主题响应失败：{e}")

        # 使用默认主题
        logger.info("使用默认主题生成策略")
        return self._generate_default_themes(expected_count)

    def _generate_default_themes(self, count: int) -> List[Dict]:
        """生成默认主题（当 LLM 解析失败时）"""
        themes = []
        default_themes = [
            {"theme": "行业动态", "description": "相关行业的最新发展和动态", "related_news_indices": []},
            {"theme": "技术创新", "description": "技术突破和创新应用", "related_news_indices": []},
            {"theme": "市场趋势", "description": "市场变化和趋势分析", "related_news_indices": []},
            {"theme": "政策解读", "description": "政策变化和行业影响", "related_news_indices": []},
            {"theme": "企业动态", "description": "企业重要活动和公告", "related_news_indices": []},
        ]

        for i, theme in enumerate(default_themes[:count]):
            # 简单分配新闻索引
            theme['related_news_indices'] = list(range(1, min(count * 2 + 1, 21)))
            themes.append(theme)

        return themes

    def get_theme_details(self, theme: Dict, analyzed_news: List[Dict]) -> Dict:
        """获取主题的详细信息"""
        related_indices = theme.get('related_news_indices', [])
        related_news = [
            news for i, news in enumerate(analyzed_news, 1)
            if i in related_indices
        ]

        return {
            **theme,
            'related_news': related_news,
            'related_news_count': len(related_news)
        }
