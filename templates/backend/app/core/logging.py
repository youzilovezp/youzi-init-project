"""
统一日志配置（基于 loguru）。
"""

import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """初始化日志输出。"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        if settings.LOG_FORMAT == "text"
        else '{"ts":"{time:YYYY-MM-DD HH:mm:ss}","level":"{level}","msg":"{message}"}',
        backtrace=True,
        diagnose=settings.DEBUG,
    )
    logger.add(
        "logs/{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        level=settings.LOG_LEVEL,
    )


__all__ = ["logger", "setup_logging"]
