import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self):
        if self._initialized:
            return
        self.settings = {}
        self.news_sources = {}
        self.platforms = {}
        self.env_vars = {}
        self.load_env()
        self.load_settings()
        self.load_news_sources()
        self.load_platforms()
        self._initialized = True
    
    def load_env(self):
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            self.env_vars = {k: v for k, v in os.environ.items() if k.startswith('AI_')}
            logger.info("环境变量加载完成")
    
    def load_settings(self):
        settings_file = PROJECT_ROOT / "config" / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f)
            logger.info("全局设置加载完成")
        else:
            logger.warning(f"配置文件不存在: {settings_file}")
    
    def load_news_sources(self):
        sources_file = PROJECT_ROOT / "config" / "news_sources.yaml"
        if sources_file.exists():
            with open(sources_file, 'r', encoding='utf-8') as f:
                self.news_sources = yaml.safe_load(f)
            logger.info("新闻源配置加载完成")
        else:
            logger.warning(f"配置文件不存在: {sources_file}")
    
    def load_platforms(self):
        platforms_file = PROJECT_ROOT / "config" / "platforms.yaml"
        if platforms_file.exists():
            with open(platforms_file, 'r', encoding='utf-8') as f:
                self.platforms = yaml.safe_load(f)
            logger.info("发布平台配置加载完成")
        else:
            logger.warning(f"配置文件不存在: {platforms_file}")
    
    def save_settings(self, settings):
        settings_file = PROJECT_ROOT / "config" / "settings.yaml"
        with open(settings_file, 'w', encoding='utf-8') as f:
            yaml.dump(settings, f, default_flow_style=False, allow_unicode=True)
        self.settings = settings
        logger.info("设置已保存")
    
    def get_industries(self):
        if 'industries' in self.settings:
            return [(item['name'], item['keywords']) for item in self.settings['industries']]
        return []
    
    def get_industry_names(self):
        return [item['name'] for item in self.settings.get('industries', [])]
    
    def get_platforms(self):
        if 'platforms' in self.platforms:
            return [(name, info.get('name', name)) for name, info in self.platforms['platforms'].items()]
        return []
    
    def get_platform_enabled(self, platform_name):
        if 'platforms' in self.platforms:
            return self.platforms['platforms'].get(platform_name, {}).get('enabled', False)
        return False
    
    def get_setting(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set_setting(self, key_path, value):
        keys = key_path.split('.')
        settings = self.settings
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
        settings[keys[-1]] = value
    
    def get_env_var(self, key, default=None):
        return os.environ.get(key, default)