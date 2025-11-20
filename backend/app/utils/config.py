# config.py
import os
from dotenv import load_dotenv

# 自动加载 .env 文件（仅本地开发有效）
load_dotenv()

class Config:
    """Global configuration manager"""
    APP_NAME = os.getenv("APP_NAME", "myapp")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", 8000))

    # Database
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "app")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_NAME", "erex")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT = os.getenv("LOG_FORMAT", "plain")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"

    @classmethod
    def summary(cls):
        """Print summary (for debugging)"""
        return {
            "env": cls.APP_ENV,
            "debug": cls.DEBUG,
            "db": f"{cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}",
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "log_to_file": cls.LOG_TO_FILE,
        }


# 使用方式
# from app.utils.config import Config
# print(Config.summary())
