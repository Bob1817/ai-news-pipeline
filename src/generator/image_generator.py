"""
配图自动生成模块
支持本地 Stable Diffusion 和云端 API 两种方式
"""
import os
import base64
import hashlib
import httpx
from pathlib import Path
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ImageGenerator:
    """配图生成器"""

    def __init__(self, method: str = "api"):
        """
        参数:
            method: "local" 使用本地 Stable Diffusion WebUI
                    "api" 使用云端 API（如 Stability AI）
        """
        self.method = method
        self.output_dir = PROJECT_ROOT / "data/images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 图片缓存目录
        self.cache_dir = PROJECT_ROOT / "data/image_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        prompt: str,
        article_title: str = "",
        width: int = 1024,
        height: int = 576
    ) -> str:
        """
        生成配图

        参数:
            prompt: 图片描述提示词
            article_title: 文章标题（用于文件命名）
            width: 图片宽度
            height: 图片高度

        返回：生成的图片文件路径
        """
        # 检查缓存
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        cached_file = self.cache_dir / f"{cache_key}.png"

        if cached_file.exists():
            logger.info(f"使用图片缓存：{cached_file}")
            # 复制缓存图片到输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c for c in article_title[:20] if c.isalnum() or c in (' ', '-', '_')
            ).strip()
            filename = f"{timestamp}_{safe_title}.png"
            filepath = self.output_dir / filename
            import shutil
            shutil.copy(cached_file, filepath)
            return str(filepath)

        # 生成文件名
        safe_title = "".join(
            c for c in article_title[:20] if c.isalnum() or c in (' ', '-', '_')
        ).strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_title}.png"
        filepath = self.output_dir / filename

        if self.method == "local":
            result_path = self._generate_local(prompt, filepath, width, height)
        else:
            result_path = self._generate_api(prompt, filepath, width, height)

        # 保存到缓存
        if result_path and Path(result_path).exists():
            try:
                import shutil
                shutil.copy(result_path, cached_file)
            except Exception as e:
                logger.warning(f"保存图片缓存失败：{e}")

        return result_path

    def _generate_local(
        self,
        prompt: str,
        filepath: Path,
        width: int,
        height: int
    ) -> str:
        """调用本地 Stable Diffusion WebUI API"""
        try:
            # SD WebUI 默认运行在 http://127.0.0.1:7860
            sd_url = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860")

            payload = {
                "prompt": f"{prompt}, best quality, masterpiece, high resolution, news photo",
                "negative_prompt": "low quality, blurry, watermark, text, deformed",
                "width": width,
                "height": height,
                "steps": 20,
                "cfg_scale": 7,
                "batch_size": 1
            }

            with httpx.Client(timeout=300) as client:
                response = client.post(
                    f"{sd_url}/sdapi/v1/txt2img",
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                image_data = base64.b64decode(result['images'][0])

                with open(filepath, 'wb') as f:
                    f.write(image_data)

                logger.info(f"本地生成配图成功：{filepath}")
                return str(filepath)

        except Exception as e:
            logger.error(f"本地图片生成失败：{e}")
            return self._create_placeholder(filepath, "本地生成失败")

    def _generate_api(
        self,
        prompt: str,
        filepath: Path,
        width: int,
        height: int
    ) -> str:
        """调用云端文生图 API"""
        try:
            # 示例：使用 SiliconFlow 的免费 API（或其他服务）
            api_key = os.getenv("IMAGE_API_KEY", "")
            api_url = os.getenv(
                "IMAGE_API_URL",
                "https://api.siliconflow.cn/v1/images/generations"
            )

            if not api_key:
                logger.warning("未配置图片生成 API Key，使用占位图")
                return self._create_placeholder(filepath, prompt[:30])

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "stabilityai/stable-diffusion-xl-base-1.0",
                "prompt": prompt,
                "image_size": f"{width}x{height}",
                "batch_size": 1,
                "num_inference_steps": 20,
                "guidance_scale": 7.5
            }

            with httpx.Client(timeout=120) as client:
                response = client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                # 根据 API 返回格式调整
                if 'data' in data and data['data']:
                    image_url = data['data'][0].get('url', '')
                    if image_url:
                        # 下载图片
                        img_resp = client.get(image_url)
                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)
                        logger.info(f"API 生成配图成功：{filepath}")
                        return str(filepath)

            return self._create_placeholder(filepath, prompt[:30])

        except Exception as e:
            logger.error(f"API 图片生成失败：{e}")
            return self._create_placeholder(filepath, "API 调用失败")

    def _create_placeholder(self, filepath: Path, text: str) -> str:
        """创建占位图"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new('RGB', (1024, 576), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)

            # 绘制占位文字
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
            except OSError:
                font = ImageFont.load_default()

            text_to_draw = f"配图：{text}"
            bbox = draw.textbbox((0, 0), text_to_draw, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (1024 - text_width) // 2
            y = (576 - text_height) // 2
            draw.text((x, y), text_to_draw, fill=(120, 120, 120), font=font)

            img.save(str(filepath))
            logger.info(f"已创建占位图：{filepath}")
            return str(filepath)

        except ImportError:
            # 如果没有 Pillow，创建一个空文件
            filepath.touch()
            return str(filepath)
