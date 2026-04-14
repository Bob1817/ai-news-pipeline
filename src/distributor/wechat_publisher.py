"""
微信公众号发布器
注意：微信公众号发布流程需要人工扫码确认，无法完全自动化
本模块实现：自动填写内容 -> 保存草稿 -> 提示人工操作
"""
import asyncio
from typing import Dict
from datetime import datetime
from pathlib import Path
from loguru import logger
import yaml

from src.utils.db import save_publish_record

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class WechatPublisher:
    """微信公众号发布器"""

    def __init__(self, config_path: str = "config/platforms.yaml"):
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = PROJECT_ROOT / config_file

        with open(config_file, 'r', encoding='utf-8') as f:
            platforms = yaml.safe_load(f)['platforms']

        self.config = platforms.get('wechat', {})
        self.enabled = self.config.get('enabled', False)

    def _validate_config(self) -> str | None:
        admin_url = str(self.config.get('admin_url', '')).strip()
        if not admin_url:
            return '未配置微信公众号后台地址'
        return None

    async def publish(self, article: Dict) -> Dict:
        """
        发布文章到微信公众号（保存为草稿）

        参数:
            article: 文章数据字典

        返回: 发布结果
        """
        if not self.enabled:
            return {'success': False, 'error': '平台未启用'}

        config_error = self._validate_config()
        if config_error:
            logger.warning(f"微信公众号发布已跳过：{config_error}")
            return {
                'platform': 'wechat',
                'article_title': article.get('title', ''),
                'success': False,
                'url': '',
                'error': config_error,
                'published_at': datetime.now()
            }

        from playwright.async_api import async_playwright

        result = {
            'platform': 'wechat',
            'article_title': article.get('title', ''),
            'success': False,
            'url': '',
            'error': '',
            'published_at': datetime.now()
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # 微信需要扫码，不能无头
                    args=['--no-sandbox']
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN'
                )
                page = await context.new_page()

                # ========== 第1步：打开微信公众号后台 ==========
                logger.info("正在打开微信公众号后台...")
                await page.goto(self.config.get('admin_url', 'https://mp.weixin.qq.com/'), timeout=30000)

                # ========== 第2步：等待人工扫码 ==========
                logger.info("=" * 50)
                logger.info("请在30秒内使用微信扫码登录公众号后台！")
                logger.info("=" * 50)

                # 等待登录成功（检测页面跳转）
                try:
                    await page.wait_for_url(
                        '**/cgi-bin/home**',
                        timeout=60000  # 给60秒扫码时间
                    )
                    logger.info("扫码登录成功！")
                except Exception:
                    logger.error("扫码超时，发布中止")
                    result['error'] = '扫码超时'
                    await browser.close()
                    return result

                # ========== 第3步：进入图文编辑 ==========
                await page.wait_for_timeout(2000)

                # 点击"新的创作"
                try:
                    await page.click('text=图文消息', timeout=10000)
                except Exception:
                    # 尝试其他入口
                    await page.click('text=创作', timeout=10000)
                    await page.click('text=图文消息', timeout=10000)

                await page.wait_for_timeout(3000)

                # 切换到新标签页（公众号编辑器通常打开新标签）
                pages = context.pages
                if len(pages) > 1:
                    page = pages[-1]  # 切换到最新的标签页

                logger.info("已进入图文编辑页面")

                # ========== 第4步：填写标题 ==========
                title_input = self.config.get('publish_flow', {}).get(
                    'selectors', {}
                ).get('title_input', '#title')

                await page.fill(title_input, article.get('title', ''))
                logger.info(f"已填写标题: {article.get('title')}")

                # ========== 第5步：填写正文 ==========
                content_editor = self.config.get('publish_flow', {}).get(
                    'selectors', {}
                ).get('content_editor', '.ql-editor')

                content = article.get('content', '')
                # 将换行转为HTML段落
                html_content = ''.join(
                    f'<p>{line}</p>' if line.strip() else '<p><br></p>'
                    for line in content.split('\n')
                )

                await page.evaluate(f'''(html) => {{
                    const editor = document.querySelector('{content_editor}');
                    if (editor) {{
                        editor.innerHTML = html;
                        // 触发输入事件
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}''', html_content)
                logger.info("已填写正文内容")

                # ========== 第6步：填写作者（可选） ==========
                author_input = self.config.get('publish_flow', {}).get(
                    'selectors', {}
                ).get('author_input', '')
                if author_input:
                    try:
                        await page.fill(author_input, 'AI新闻助手')
                    except Exception:
                        pass

                # ========== 第7步：保存草稿 ==========
                await page.wait_for_timeout(2000)

                # 点击保存按钮
                try:
                    # 微信公众号的保存按钮可能有多种形态
                    await page.click('button:has-text("保存")', timeout=5000)
                except Exception:
                    try:
                        await page.click('text=保存为草稿', timeout=5000)
                    except Exception:
                        # 使用快捷键 Ctrl+S
                        await page.keyboard.press('Control+s')

                await page.wait_for_timeout(3000)

                logger.info("=" * 50)
                logger.info("文章已保存至微信公众号草稿箱！")
                logger.info("请在浏览器中手动完成以下操作：")
                logger.info("  1. 检查文章内容和格式")
                logger.info("  2. 设置封面图")
                logger.info("  3. 选择是否声明原创")
                logger.info("  4. 点击「群发」完成发布")
                logger.info("=" * 50)

                result['success'] = True
                result['url'] = 'mp.weixin.qq.com (草稿已保存)'

                # 不自动关闭浏览器，留给用户手动操作
                logger.info("浏览器将保持打开状态，请手动操作完成发布...")

        except Exception as e:
            logger.error(f"微信公众号发布失败: {e}")
            result['error'] = str(e)

        # 保存发布记录
        save_publish_record({
            'article_id': article.get('id'),
            'platform': 'wechat',
            'platform_url': result.get('url', ''),
            'status': 'draft' if result['success'] else 'failed',
            'error_message': result.get('error', ''),
            'published_at': datetime.now()
        })

        return result
