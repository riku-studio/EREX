# logging.py
import json
import logging
import sys

from app.utils.config import Config

def setup_logger():
    """Initialize global logger according to Config"""
    logger = logging.getLogger(Config.APP_NAME)
    logger.setLevel(Config.LOG_LEVEL)

    # --- 1️⃣ 定义输出格式 ---
    if Config.LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    # --- 2️⃣ 标准输出处理器（stdout） ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- 3️⃣ 可选：文件输出（开发调试时用） ---
    if Config.LOG_TO_FILE:
        file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # --- 4️⃣ 避免重复日志（尤其在 Flask / FastAPI 中）---
    logger.propagate = False

    return logger

# --- 5️⃣ 可选：结构化 JSON 格式 ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(data, ensure_ascii=False)

# 实例化全局 logger
logger = setup_logger()


# 示例用法
# from logging import logger
# logger.debug("这是调试信息")
# logger.info("应用程序已启动")
# logger.warning("这是一个警告")
# logger.error("发生了一个错误")
# logger.critical("严重错误，应用程序将退出")
