"""
自有网站后台发布器
使用Playwright模拟浏览器操作完成文章发布
"""
import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
import yaml

from src.utils.db import save_publish_record

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class WebsitePublisher:
    """网站后台自动发布器"""

    def __init__(self, config_path: str = "config/platforms.yaml"):
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = PROJECT_ROOT / config_file

        with open(config_file, 'r', encoding='utf-8') as f:
            platforms = yaml.safe_load(f)['platforms']

        self.config = platforms.get('website', {})
        if not self.config.get('enabled'):
            logger.warning("网站发布平台未启用")
            self.enabled = False
        else:
            self.enabled = True

    def _validate_config(self) -> str | None:
        """检查站点发布配置是否可用，避免占位值导致长时间超时"""
        admin_url = str(self.config.get('admin_url', '')).strip()
        publish_flow = self.config.get('publish_flow', {})
        new_article_url = str(publish_flow.get('new_article_url', '')).strip()
        username = os.getenv('WEBSITE_ADMIN_USER', '').strip()
        password = os.getenv('WEBSITE_ADMIN_PASS', '').strip()

        if not admin_url:
            return '未配置网站后台登录地址'
        if 'your-website.com' in admin_url:
            return '网站后台地址仍为示例占位值，请先在 config/platforms.yaml 中配置真实地址'
        if new_article_url and 'your-website.com' in new_article_url:
            return '文章发布地址仍为示例占位值，请先在 config/platforms.yaml 中配置真实地址'
        if not username or not password:
            return '未配置 WEBSITE_ADMIN_USER / WEBSITE_ADMIN_PASS 环境变量'

        return None

    async def publish(self, article: Dict) -> Dict:
        """
        发布文章到网站后台

        参数:
            article: 文章数据字典

        返回: 发布结果
        """
        if not self.enabled:
            return {'success': False, 'error': '平台未启用'}

        config_error = self._validate_config()
        if config_error:
            logger.warning(f"网站发布已跳过：{config_error}")
            return {
                'platform': 'website',
                'article_title': article.get('title', ''),
                'success': False,
                'url': '',
                'error': config_error,
                'published_at': datetime.now()
            }

        from playwright.async_api import async_playwright

        result = {
            'platform': 'website',
            'article_title': article.get('title', ''),
            'success': False,
            'url': '',
            'error': '',
            'published_at': datetime.now()
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox']
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN'
                )
                page = await context.new_page()

                # ========== 第1步：登录 ==========
                logger.info("正在登录网站后台...")
                await page.goto(self.config['admin_url'], timeout=30000)
                await page.wait_for_load_state('networkidle')

                login_selectors = self.config.get('login_selectors', {})
                await page.fill(
                    login_selectors.get('username_input', '#username'),
                    os.getenv('WEBSITE_ADMIN_USER', '')
                )
                await page.fill(
                    login_selectors.get('password_input', '#password'),
                    os.getenv('WEBSITE_ADMIN_PASS', '')
                )
                await page.click(login_selectors.get('submit_button', '#login-btn'))
                await page.wait_for_timeout(3000)
                logger.info("登录成功")

                # ========== 第2步：进入发布页面 ==========
                publish_flow = self.config.get('publish_flow', {})
                new_article_url = publish_flow.get('new_article_url', '')
                if new_article_url:
                    await page.goto(new_article_url, timeout=30000)
                else:
                    # 点击"新建文章"按钮
                    await page.click('text=新建文章')
                await page.wait_for_load_state('networkidle')
                logger.info("已进入文章编辑页面")

                selectors = publish_flow.get('selectors', {})

                # ========== 第3步：填写标题 ==========
                title_input = selectors.get('title_input', '#title')
                await page.fill(title_input, article.get('title', ''))
                logger.info(f"已填写标题: {article.get('title')}")

                # ========== 第4步：填写内容 ==========
                content_editor = selectors.get('content_editor', '#content')
                content_iframe = selectors.get('content_iframe', '')

                if content_iframe:
                    # 如果编辑器在iframe中
                    frame = page.frame_locator(content_iframe)
                    editor = frame.locator('body')
                    await editor.fill('')
                    await editor.fill(article.get('content', ''))
                else:
                    # 尝试直接操作富文本编辑器
                    # 常见的富文本编辑器：TinyMCE, CKEditor, Quill
                                    await page.evaluate(f'''(content) => {{
                    if (typeof tinymce !== 'undefined') {{
                        tinymce.activeEditor.setContent(content);
                        return;
                    }}
                    if (typeof CKEDITOR !== 'undefined') {{
                        CKEDITOR.instances['{content_editor.lstrip("#")}'].setData(content);
                        return;
                    }}
                    const editor = document.querySelector('{content_editor}');
                    if (editor) {{
                        editor.innerHTML = content;
                        return;
                    }}
                    const textarea = document.querySelector('textarea{{name="content"}}');
                    if (textarea) {{
                        textarea.value = content;
                    }}
                }}''', article.get('content', ''))


                logger.info("已填写文章内容")

                # ========== 第5步：上传配图 ==========
                image_path = article.get('image_path', '')
                if image_path:
                    image_upload = selectors.get('image_upload', '')
                    if image_upload:
                        try:
                            await page.set_input_files(image_upload, image_path)
                            logger.info(f"已上传配图: {image_path}")
                        except Exception as e:
                            logger.warning(f"配图上传失败: {e}")

                # ========== 第6步：填写关键词 ==========
                keywords_input = selectors.get('keywords_input', '')
                if keywords_input:
                    keywords = article.get('keywords', [])
                    if isinstance(keywords, list):
                        keywords_str = ','.join(keywords)
                    else:
                        keywords_str = str(keywords)
                    await page.fill(keywords_input, keywords_str)
                    logger.info("已填写关键词")

                # ========== 第7步：发布或保存草稿 ==========
                # 根据配置决定直接发布还是保存草稿
                require_review = True  # 默认需要审核
                try:
                    with open(PROJECT_ROOT / 'config' / 'settings.yaml', 'r', encoding='utf-8') as f:
                        settings = yaml.safe_load(f)
                        require_review = settings.get('distributor', {}).get('require_review', True)
                except Exception:
                    pass

                if require_review:
                    save_btn = selectors.get('save_draft_button', '#save-draft-btn')
                    await page.click(save_btn)
                    logger.info("文章已保存为草稿（需要人工审核）")
                else:
                    publish_btn = selectors.get('publish_button', '#publish-btn')
                    await page.click(publish_btn)
                    logger.info("文章已直接发布")

                await page.wait_for_timeout(3000)

                # 获取发布后的URL（如果有的话）
                try:
                    current_url = page.url
                    result['url'] = current_url
                except Exception:
                    pass

                result['success'] = True
                await browser.close()

        except Exception as e:
            logger.error(f"网站发布失败: {e}")
            result['error'] = str(e)

        # 保存发布记录
        save_publish_record({
            'article_id': article.get('id'),
            'platform': 'website',
            'platform_url': result.get('url', ''),
            'status': 'success' if result['success'] else 'failed',
            'error_message': result.get('error', ''),
            'published_at': datetime.now()
        })

        return result
