"""
统一日志配置（基于 loguru）。

仅输出到 stdout——容器时代 12-factor 标准（docker logs / kubectl logs 直读）。
生产环境不写文件：容器销毁即丢，运维历史由日志收集层负责。
"""

import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """初始化日志输出。"""
    is_dev = settings.APP_ENV == "dev"
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
        backtrace=is_dev,
        diagnose=is_dev,  # 生产不开 diagnose，避免泄漏变量值
    )


__all__ = ["logger", "setup_logging"]
