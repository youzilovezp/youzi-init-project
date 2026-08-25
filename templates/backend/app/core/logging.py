"""
统一日志配置（基于 loguru）。

仅输出到 stdout——容器时代 12-factor 标准（docker logs / kubectl logs 直读）。
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
        ),
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )


__all__ = ["logger", "setup_logging"]
