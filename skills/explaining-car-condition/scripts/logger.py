#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Description: 统一日志配置，各脚本导入后即可使用
# @Author   : liyandan  
# @Date     : 2026-03-09
# 统一日志配置，各脚本导入后即可使用
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

# 项目根 logger 名称
LOGGER_NAME = "car_explanation"
# 是否已初始化（避免重复添加 handler）
_initialized = False


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    format_str: Optional[str] = None,
) -> logging.Logger:
    """
    初始化统一 logger 配置。
    脚本首次调用 get_logger 时会自动执行，也可手动调用以覆盖默认配置。

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 日志文件路径，为 None 则仅输出到控制台
        max_bytes: 单日志文件最大字节数
        backup_count: 保留的备份文件数
        format_str: 日志格式，默认简洁格式
    """
    global _initialized

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if format_str is None:
        format_str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")

    if not _initialized:
        logger.handlers.clear()
        logger.propagate = False  # 避免传播到 root 导致重复输出

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件输出（可选）
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        _initialized = True

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例。各脚本在文件开头调用即可。

    示例:
        from config.logger import get_logger
        logger = get_logger(__name__)
        logger.info("程序启动")
    """
    try:
        from config.settings import get_settings

        settings = get_settings()
        setup_logger(
            level=settings.log_level,
            log_file=settings.log_file_path,
            max_bytes=settings.log_file_max_size,
            backup_count=settings.log_file_backup_count,
        )
    except Exception:
        # 若 settings 加载失败（如缺少依赖），使用默认配置
        setup_logger()

    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)
