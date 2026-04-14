#!/usr/bin/env python3
"""
AI新闻自动化系统 - 桌面端主入口
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger

logger.add(
    PROJECT_ROOT / "logs" / "desktop_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

def main():
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        from src.business.task_manager import TaskManager
        from src.business.config_manager import ConfigManager
        
        app = QApplication(sys.argv)
        
        style_file = PROJECT_ROOT / "resources" / "styles" / "main.qss"
        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
        
        config_manager = ConfigManager()
        config_manager.initialize()
        
        task_manager = TaskManager()
        task_manager.initialize()
        
        window = MainWindow()
        window.set_config_manager(config_manager)
        window.set_task_manager(task_manager)
        
        window.show()
        
        return app.exec()
    
    except ModuleNotFoundError as e:
        missing_module = getattr(e, "name", "unknown")
        print(f"缺少 Python 依赖模块：{missing_module}", file=sys.stderr)
        print("", file=sys.stderr)
        print("请先安装依赖：", file=sys.stderr)
        print("pip install pyqt6 python-dotenv pyyaml loguru beautifulsoup4", file=sys.stderr)
        return 1
    
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        print(f"应用启动失败: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())