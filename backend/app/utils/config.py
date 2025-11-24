# config.py
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# 自动加载 .env 文件（仅本地开发有效；缺少依赖时静默跳过）
load_dotenv()


# 当前项目根目录（backend/app/utils/../../.. -> repo 根）
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _default_index_rules_path() -> str:
    """Choose a default path for index rules loaded from config files."""

    candidates = [
        PROJECT_ROOT / "backend" / "config" / "index_rules.json",
        PROJECT_ROOT / "config" / "index_rules.json",
        BACKEND_ROOT / "config" / "index_rules.json",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return str(candidates[0])

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

    # Semantic (template-based) extraction
    SEMANTIC_MODEL = os.getenv("SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", 0.55))
    SEMANTIC_DEVICE = os.getenv("SEMANTIC_DEVICE", "cpu")

    # Index rule source
    INDEX_RULE_SOURCE = os.getenv("INDEX_RULE_SOURCE", "file").lower()
    INDEX_RULES_PATH = os.getenv("INDEX_RULES_PATH", _default_index_rules_path())
    INDEX_RULE_TABLE = os.getenv("INDEX_RULE_TABLE", "index_rules")

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
            "semantic_model": cls.SEMANTIC_MODEL,
            "semantic_threshold": cls.SEMANTIC_THRESHOLD,
            "semantic_device": cls.SEMANTIC_DEVICE,
            "index_rule_source": cls.INDEX_RULE_SOURCE,
            "index_rules_path": cls.INDEX_RULES_PATH,
            "index_rule_table": cls.INDEX_RULE_TABLE,
        }


# 使用方式
# from app.utils.config import Config
# print(Config.summary())
