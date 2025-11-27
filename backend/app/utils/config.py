# config.py
import json
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


def _default_line_filter_config_path() -> str:
    return str(PROJECT_ROOT / "backend" / "config" / "line_filter.json")


def _default_semantic_templates_path() -> str:
    return str(PROJECT_ROOT / "backend" / "config" / "semantic_job_templates.json")


def _default_keywords_path() -> str:
    return str(PROJECT_ROOT / "backend" / "config" / "keywords_tech.json")


def _load_json(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


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

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Semantic (template-based) extraction
    SEMANTIC_MODEL = os.getenv("SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", 0.55))
    SEMANTIC_DEVICE = os.getenv("SEMANTIC_DEVICE", "cpu")
    SEMANTIC_BATCH_SIZE = int(os.getenv("SEMANTIC_BATCH_SIZE", 64))
    SEMANTIC_SHOW_PROGRESS = os.getenv("SEMANTIC_SHOW_PROGRESS", "false").lower() == "true"
    SEMANTIC_TEMPLATES_PATH = os.getenv("SEMANTIC_TEMPLATES_PATH", _default_semantic_templates_path())
    _SEMANTIC_TEMPLATES = _load_json(SEMANTIC_TEMPLATES_PATH)
    SEMANTIC_CONTEXT_RADIUS = int(
        os.getenv("SEMANTIC_CONTEXT_RADIUS", _SEMANTIC_TEMPLATES.get("context_radius", 1))
    )
    SEMANTIC_JOB_GLOBAL_THRESHOLD = float(
        os.getenv("SEMANTIC_JOB_GLOBAL_THRESHOLD", _SEMANTIC_TEMPLATES.get("global_threshold", 0.55))
    )
    SEMANTIC_JOB_FIELD_THRESHOLD = float(
        os.getenv("SEMANTIC_JOB_FIELD_THRESHOLD", _SEMANTIC_TEMPLATES.get("field_threshold", 0.4))
    )

    # Keyword extractor
    KEYWORDS_TECH_PATH = os.getenv("KEYWORDS_TECH_PATH", _default_keywords_path())
    _KEYWORDS_TECH = _load_json(KEYWORDS_TECH_PATH)

    # Classifier configs (can be extended)
    CLASSIFIER_FOREIGNER_PATH = os.getenv(
        "CLASSIFIER_FOREIGNER_PATH", str(PROJECT_ROOT / "backend" / "config" / "classifiers" / "foreigner.json")
    )

    # Splitter (multi-block detection)
    SPLITTER_SKIP_LINES = int(os.getenv("SPLITTER_SKIP_LINES", 5))
    SPLITTER_MARKER_PATTERNS = [
        r"^[\s\W]*案件名[\s\W]*$",
        r"^[\s\W]*案件[\s\W]*$",
    ]

    # Pipeline orchestration
    PIPELINE_STEPS = (
        os.getenv(
            "PIPELINE_STEPS",
            "cleaner,line_filter,semantic,splitter,extractor,classifier,aggregator",
        )
        .strip()
        .split(",")
    )

    # Lightweight line filter (between cleaner and semantic)
    ENABLE_LINE_FILTER = os.getenv("ENABLE_LINE_FILTER", "true").lower() == "true"
    LINE_FILTER_CONFIG_PATH = os.getenv("LINE_FILTER_CONFIG_PATH", _default_line_filter_config_path())
    _LINE_FILTER_SETTINGS = _load_json(LINE_FILTER_CONFIG_PATH)
    LINE_FILTER_DECORATION_CHARS = _LINE_FILTER_SETTINGS.get("decoration_chars", "")
    LINE_FILTER_GREETING_PATTERNS = _LINE_FILTER_SETTINGS.get("greeting_patterns", [])
    LINE_FILTER_CLOSING_PATTERNS = _LINE_FILTER_SETTINGS.get("closing_patterns", [])
    LINE_FILTER_SIGNATURE_COMPANY_PREFIX = _LINE_FILTER_SETTINGS.get("signature_company_prefix", [])
    LINE_FILTER_SIGNATURE_KEYWORDS = _LINE_FILTER_SETTINGS.get("signature_keywords", [])
    LINE_FILTER_FOOTER_PATTERNS = _LINE_FILTER_SETTINGS.get("footer_patterns", [])
    LINE_FILTER_JOB_KEYWORDS = _LINE_FILTER_SETTINGS.get("job_keywords", [])
    LINE_FILTER_FORCE_DELETE_PATTERNS = _LINE_FILTER_SETTINGS.get("force_delete_patterns", [])

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
            "openai_model": cls.OPENAI_MODEL,
            "semantic_model": cls.SEMANTIC_MODEL,
            "semantic_threshold": cls.SEMANTIC_THRESHOLD,
            "semantic_device": cls.SEMANTIC_DEVICE,
            "semantic_show_progress": cls.SEMANTIC_SHOW_PROGRESS,
            "semantic_templates_path": cls.SEMANTIC_TEMPLATES_PATH,
            "semantic_context_radius": cls.SEMANTIC_CONTEXT_RADIUS,
            "semantic_global_threshold": cls.SEMANTIC_JOB_GLOBAL_THRESHOLD,
            "semantic_field_threshold": cls.SEMANTIC_JOB_FIELD_THRESHOLD,
            "keywords_tech_path": cls.KEYWORDS_TECH_PATH,
            "line_filter_enabled": cls.ENABLE_LINE_FILTER,
            "line_filter_config_path": cls.LINE_FILTER_CONFIG_PATH,
            "line_filter_job_keywords": len(cls.LINE_FILTER_JOB_KEYWORDS),
            "line_filter_greeting_patterns": len(cls.LINE_FILTER_GREETING_PATTERNS),
            "index_rule_source": cls.INDEX_RULE_SOURCE,
            "index_rules_path": cls.INDEX_RULES_PATH,
            "index_rule_table": cls.INDEX_RULE_TABLE,
        }

    @classmethod
    def semantic_global_templates(cls) -> list[str]:
        data = cls._SEMANTIC_TEMPLATES.get("global", [])
        return list(data) if isinstance(data, list) else []

    @classmethod
    def semantic_field_templates(cls) -> dict[str, list[str]]:
        fields = cls._SEMANTIC_TEMPLATES.get("fields", {})
        output: dict[str, list[str]] = {}
        if isinstance(fields, dict):
            for key, value in fields.items():
                if isinstance(value, list):
                    output[str(key)] = [str(v) for v in value]
        return output

    @classmethod
    def keywords_tech(cls) -> dict[str, list[str]]:
        output: dict[str, list[str]] = {}
        if isinstance(cls._KEYWORDS_TECH, dict):
            for key, values in cls._KEYWORDS_TECH.items():
                if isinstance(values, list):
                    output[str(key)] = [str(v) for v in values]
        return output


# 使用方式
# from app.utils.config import Config
# print(Config.summary())
