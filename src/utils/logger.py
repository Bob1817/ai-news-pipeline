"""
统一日志管理模块
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_level: str = "INFO"):
    """配置全局日志"""
    # 移除默认处理器
    logger.remove()

    # 控制台输出（带颜色）
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )

    # 文件输出（按天轮转）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "pipeline_{time:YYYY-MM-DD}.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",       # 每天零点创建新文件
        retention="30 days",    # 保留30天
        encoding="utf-8",
        enqueue=True            # 线程安全
    )

    return logger


# 模块级导出
log = setup_logger()
