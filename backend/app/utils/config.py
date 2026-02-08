# config.py
import json
import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# 自动加载 .env 文件（仅本地开发有效；缺少依赖时静默跳过）
load_dotenv()


# 当前项目根目录（兼容容器路径 /app/app/utils 与本地路径 backend/app/utils）
def _detect_project_root() -> Path:
    base = Path(__file__).resolve()
    for candidate in base.parents:
        # 本地开发：repo 根包含 backend 目录
        if (candidate / "backend").exists():
            return candidate
        # 容器内：/app 下有 config 目录
        if (candidate / "config").exists() and (candidate / "app").exists():
            return candidate
    return base.parents[2]


PROJECT_ROOT = _detect_project_root()
BACKEND_ROOT = PROJECT_ROOT / "backend" if (PROJECT_ROOT / "backend").exists() else PROJECT_ROOT
CONFIG_ROOT = (
    PROJECT_ROOT / "backend" / "config" if (PROJECT_ROOT / "backend" / "config").exists() else PROJECT_ROOT / "config"
)


def _default_index_rules_path() -> str:
    """Choose a default path for index rules loaded from config files."""

    candidates = [
        CONFIG_ROOT / "index_rules.json",
        BACKEND_ROOT / "config" / "index_rules.json",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return str(candidates[0])


def _default_line_filter_config_path() -> str:
    return str(CONFIG_ROOT / "line_filter.json")


def _default_semantic_templates_path() -> str:
    return str(CONFIG_ROOT / "semantic_job_templates.json")


def _default_semantic_pos_templates_path() -> str:
    return str(CONFIG_ROOT / "semantic_pos_templates.json")


def _default_semantic_neg_templates_path() -> str:
    return str(CONFIG_ROOT / "semantic_neg_templates.json")


def _default_keywords_path() -> str:
    return str(CONFIG_ROOT / "keywords_tech.json")


def _load_json(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_json_array(path: str) -> list:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        # Fallback for template files that contain raw newlines in "text" values.
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except Exception:
            return []
        items = []
        for idx, match in enumerate(re.finditer(r'"text"\s*:\s*"([\s\S]*?)"\s*(?:,|\})', raw), start=1):
            items.append({"id": f"fallback_{idx}", "text": match.group(1)})
        return items


class Config:
    """Global configuration manager"""

    CONFIG_SOURCE = "file"
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
    DB_BOOTSTRAP = os.getenv("DB_BOOTSTRAP", "true").lower() == "true"
    DB_BOOTSTRAP_DB = os.getenv("DB_BOOTSTRAP_DB", "postgres")

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
    SEMANTIC_ACCELERATOR = os.getenv("SEMANTIC_ACCELERATOR", "cpu").strip().lower()
    SEMANTIC_DEVICE = os.getenv("SEMANTIC_DEVICE", "").strip()
    SEMANTIC_BATCH_SIZE = int(os.getenv("SEMANTIC_BATCH_SIZE", 64))
    SEMANTIC_SHOW_PROGRESS = os.getenv("SEMANTIC_SHOW_PROGRESS", "false").lower() == "true"
    SEMANTIC_TEMPLATES_PATH = os.getenv("SEMANTIC_TEMPLATES_PATH", _default_semantic_templates_path())
    SEMANTIC_POS_TEMPLATES_PATH = os.getenv("SEMANTIC_POS_TEMPLATES_PATH", _default_semantic_pos_templates_path())
    SEMANTIC_NEG_TEMPLATES_PATH = os.getenv("SEMANTIC_NEG_TEMPLATES_PATH", _default_semantic_neg_templates_path())
    _SEMANTIC_TEMPLATES = _load_json(SEMANTIC_TEMPLATES_PATH)
    _SEMANTIC_POS_TEMPLATES = _load_json_array(SEMANTIC_POS_TEMPLATES_PATH)
    _SEMANTIC_NEG_TEMPLATES = _load_json_array(SEMANTIC_NEG_TEMPLATES_PATH)
    SEMANTIC_CONTEXT_RADIUS = int(
        os.getenv("SEMANTIC_CONTEXT_RADIUS", _SEMANTIC_TEMPLATES.get("context_radius", 1))
    )
    SEMANTIC_JOB_GLOBAL_THRESHOLD = float(
        os.getenv("SEMANTIC_JOB_GLOBAL_THRESHOLD", _SEMANTIC_TEMPLATES.get("global_threshold", 0.55))
    )
    SEMANTIC_JOB_FIELD_THRESHOLD = float(
        os.getenv("SEMANTIC_JOB_FIELD_THRESHOLD", _SEMANTIC_TEMPLATES.get("field_threshold", 0.4))
    )
    _SEMANTIC_SEARCH = _SEMANTIC_TEMPLATES.get("search", {}) if isinstance(_SEMANTIC_TEMPLATES, dict) else {}
    SEMANTIC_POS_TOP_K = int(os.getenv("SEMANTIC_POS_TOP_K", _SEMANTIC_SEARCH.get("pos_top_k", 3)))
    SEMANTIC_NEGATIVE_WEIGHT = float(os.getenv("SEMANTIC_NEGATIVE_WEIGHT", _SEMANTIC_SEARCH.get("negative_weight", 0.35)))
    SEMANTIC_NEGATIVE_POWER = float(os.getenv("SEMANTIC_NEGATIVE_POWER", _SEMANTIC_SEARCH.get("negative_power", 1.0)))
    SEMANTIC_LENGTH_PENALTY = float(os.getenv("SEMANTIC_LENGTH_PENALTY", _SEMANTIC_SEARCH.get("length_penalty", 0.02)))
    SEMANTIC_LENGTH_REWARD = float(os.getenv("SEMANTIC_LENGTH_REWARD", _SEMANTIC_SEARCH.get("length_reward", 0.0)))
    SEMANTIC_CENTER_WEIGHT = float(os.getenv("SEMANTIC_CENTER_WEIGHT", _SEMANTIC_SEARCH.get("center_weight", 0.0)))
    SEMANTIC_CLUSTER_DELTA = float(os.getenv("SEMANTIC_CLUSTER_DELTA", _SEMANTIC_SEARCH.get("cluster_delta", 0.0)))
    SEMANTIC_CLUSTER_MIN_WINDOWS = int(
        os.getenv("SEMANTIC_CLUSTER_MIN_WINDOWS", _SEMANTIC_SEARCH.get("cluster_min_windows", 1))
    )
    SEMANTIC_CLUSTER_OVERLAP_ONLY = os.getenv(
        "SEMANTIC_CLUSTER_OVERLAP_ONLY",
        str(_SEMANTIC_SEARCH.get("cluster_overlap_only", True)).lower(),
    ).lower() == "true"
    SEMANTIC_TRIM_TAIL_NEG_THRESHOLD = float(
        os.getenv("SEMANTIC_TRIM_TAIL_NEG_THRESHOLD", _SEMANTIC_SEARCH.get("trim_tail_neg_threshold", 0.4))
    )
    SEMANTIC_TRIM_TAIL_POS_THRESHOLD = float(
        os.getenv("SEMANTIC_TRIM_TAIL_POS_THRESHOLD", _SEMANTIC_SEARCH.get("trim_tail_pos_threshold", 0.34))
    )
    SEMANTIC_TRIM_HEAD_NEG_THRESHOLD = float(
        os.getenv("SEMANTIC_TRIM_HEAD_NEG_THRESHOLD", _SEMANTIC_SEARCH.get("trim_head_neg_threshold", 0.55))
    )
    SEMANTIC_TRIM_HEAD_POS_THRESHOLD = float(
        os.getenv("SEMANTIC_TRIM_HEAD_POS_THRESHOLD", _SEMANTIC_SEARCH.get("trim_head_pos_threshold", 0.3))
    )
    SEMANTIC_BOUNDARY_NEG_THRESHOLD = float(
        os.getenv("SEMANTIC_BOUNDARY_NEG_THRESHOLD", _SEMANTIC_SEARCH.get("boundary_neg_threshold", 0.5))
    )
    SEMANTIC_BOUNDARY_POS_THRESHOLD = float(
        os.getenv("SEMANTIC_BOUNDARY_POS_THRESHOLD", _SEMANTIC_SEARCH.get("boundary_pos_threshold", 0.32))
    )
    SEMANTIC_BOUNDARY_TAIL_RUN = int(
        os.getenv("SEMANTIC_BOUNDARY_TAIL_RUN", _SEMANTIC_SEARCH.get("boundary_tail_run", 0))
    )
    SEMANTIC_BOUNDARY_HEAD_RUN = int(
        os.getenv("SEMANTIC_BOUNDARY_HEAD_RUN", _SEMANTIC_SEARCH.get("boundary_head_run", 0))
    )
    SEMANTIC_WINDOW_MAX_LINES = int(os.getenv("SEMANTIC_WINDOW_MAX_LINES", _SEMANTIC_SEARCH.get("window_max_lines", 24)))
    SEMANTIC_MIN_LINES = int(os.getenv("SEMANTIC_MIN_LINES", _SEMANTIC_SEARCH.get("min_lines", 2)))

    # Keyword extractor
    KEYWORDS_TECH_PATH = os.getenv("KEYWORDS_TECH_PATH", _default_keywords_path())
    _KEYWORDS_TECH = _load_json(KEYWORDS_TECH_PATH)

    # Classifier configs (can be extended)
    CLASSIFIER_FOREIGNER_PATH = os.getenv(
        "CLASSIFIER_FOREIGNER_PATH", str(CONFIG_ROOT / "classifiers" / "foreigner.json")
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
            "config_source": getattr(cls, "CONFIG_SOURCE", "file"),
            "db": f"{cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}",
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "log_to_file": cls.LOG_TO_FILE,
            "openai_model": cls.OPENAI_MODEL,
            "semantic_model": cls.SEMANTIC_MODEL,
            "semantic_threshold": cls.SEMANTIC_THRESHOLD,
            "semantic_accelerator": cls.SEMANTIC_ACCELERATOR,
            "semantic_device": cls.semantic_runtime_device(),
            "semantic_show_progress": cls.SEMANTIC_SHOW_PROGRESS,
            "semantic_templates_path": cls.SEMANTIC_TEMPLATES_PATH,
            "semantic_pos_templates_path": cls.SEMANTIC_POS_TEMPLATES_PATH,
            "semantic_neg_templates_path": cls.SEMANTIC_NEG_TEMPLATES_PATH,
            "semantic_context_radius": cls.SEMANTIC_CONTEXT_RADIUS,
            "semantic_global_threshold": cls.SEMANTIC_JOB_GLOBAL_THRESHOLD,
            "semantic_field_threshold": cls.SEMANTIC_JOB_FIELD_THRESHOLD,
            "semantic_negative_weight": cls.SEMANTIC_NEGATIVE_WEIGHT,
            "semantic_negative_power": cls.SEMANTIC_NEGATIVE_POWER,
            "semantic_pos_top_k": cls.SEMANTIC_POS_TOP_K,
            "semantic_length_penalty": cls.SEMANTIC_LENGTH_PENALTY,
            "semantic_length_reward": cls.SEMANTIC_LENGTH_REWARD,
            "semantic_center_weight": cls.SEMANTIC_CENTER_WEIGHT,
            "semantic_cluster_delta": cls.SEMANTIC_CLUSTER_DELTA,
            "semantic_cluster_min_windows": cls.SEMANTIC_CLUSTER_MIN_WINDOWS,
            "semantic_cluster_overlap_only": cls.SEMANTIC_CLUSTER_OVERLAP_ONLY,
            "semantic_trim_tail_neg_threshold": cls.SEMANTIC_TRIM_TAIL_NEG_THRESHOLD,
            "semantic_trim_tail_pos_threshold": cls.SEMANTIC_TRIM_TAIL_POS_THRESHOLD,
            "semantic_trim_head_neg_threshold": cls.SEMANTIC_TRIM_HEAD_NEG_THRESHOLD,
            "semantic_trim_head_pos_threshold": cls.SEMANTIC_TRIM_HEAD_POS_THRESHOLD,
            "semantic_boundary_neg_threshold": cls.SEMANTIC_BOUNDARY_NEG_THRESHOLD,
            "semantic_boundary_pos_threshold": cls.SEMANTIC_BOUNDARY_POS_THRESHOLD,
            "semantic_boundary_tail_run": cls.SEMANTIC_BOUNDARY_TAIL_RUN,
            "semantic_boundary_head_run": cls.SEMANTIC_BOUNDARY_HEAD_RUN,
            "semantic_window_max_lines": cls.SEMANTIC_WINDOW_MAX_LINES,
            "semantic_min_lines": cls.SEMANTIC_MIN_LINES,
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
    def semantic_runtime_device(cls) -> str:
        if cls.SEMANTIC_DEVICE:
            return cls.SEMANTIC_DEVICE

        mode = cls.SEMANTIC_ACCELERATOR
        if mode not in {"cpu", "gpu", "auto"}:
            mode = "cpu"

        if mode == "cpu":
            return "cpu"

        try:
            import torch
        except Exception:
            return "cpu"

        if bool(torch.cuda.is_available()):
            return "cuda"

        return "cpu"

    @classmethod
    def semantic_global_templates(cls) -> list[str]:
        templates: list[str] = []
        for item in cls._SEMANTIC_POS_TEMPLATES:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                text = item["text"].strip()
                if text:
                    templates.append(text)
            elif isinstance(item, str):
                text = item.strip()
                if text:
                    templates.append(text)
        return templates

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
    def semantic_negative_templates(cls) -> list[str]:
        templates: list[str] = []
        for item in cls._SEMANTIC_NEG_TEMPLATES:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                text = item["text"].strip()
                if text:
                    templates.append(text)
            elif isinstance(item, str):
                text = item.strip()
                if text:
                    templates.append(text)
        return templates

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
