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
    SEMANTIC_BATCH_SIZE = int(os.getenv("SEMANTIC_BATCH_SIZE", 64))

    # Lightweight line filter (between cleaner and semantic)
    ENABLE_LINE_FILTER = os.getenv("ENABLE_LINE_FILTER", "true").lower() == "true"
    LINE_FILTER_DECORATION_CHARS = "＝=―─－━_*＊~゜・+|／\\┏┗■□◆◯★☆※〜ー"
    LINE_FILTER_GREETING_PATTERNS = [
        r"いつもお世話になっております",
        r"お世話になっております",
        r"ご担当者\s*様",
        r"下記.*ご案内いたします",
        r"下記.*ご案内申し上げます",
        r"下記、案件にて人材を募集しております",
        r"本メールは.*送信をしております",
        r"お問い合わせは、本メールにご返信",
    ]
    LINE_FILTER_CLOSING_PATTERNS = [
        r"何卒.*よろしく.*お願い",
        r"宜しくお願い申し上げます",
        r"よろしくご検討のほどお願い",
        r"以上、?何卒宜しく",
    ]
    LINE_FILTER_SIGNATURE_COMPANY_PREFIX = [
        "株式会社",
        "有限会社",
        "合同会社",
    ]
    LINE_FILTER_SIGNATURE_KEYWORDS = [
        "TEL",
        "Tel",
        "tel",
        "ＴＥＬ",
        "携帯",
        "Mobile",
        "MOBILE",
        "M.",
        "T.",
        "FAX",
        "Fax",
        "住所",
        "ADDRESS",
        "〒",
        "Mail",
        "MAIL",
        "mail",
        "E-mail",
    ]
    LINE_FILTER_FOOTER_PATTERNS = [
        r"不特定多数.*情報.*開示",
        r"本案件情報を不特定の者が閲覧できる状態におくこと",
        r"配信停止",
        r"よくあるご質問と回答はこちら",
        r"本案件へのご質問・ご提案以外のお問い合わせ",
        r"現在要員募集中の案件一覧は下記ページで確認できます",
        r"このURLは .* まで有効です",
    ]
    LINE_FILTER_JOB_KEYWORDS = [
        "案件",
        "求人",
        "募集",
        "エンジニア",
        "案件名",
        "業務内容",
        "作業内容",
        "必須スキル",
        "歓迎スキル",
        "スキル",
        "スキル要件",
        "年齢",
        "外国籍",
        "国籍",
        "勤務形態",
        "就業",
        "就業開始",
        "勤務時間",
        "週稼働",
        "勤務地",
        "就業場所",
        "最寄り",
        "期間",
        "参画",
        "開始日",
        "稼働",
        "単価",
        "金額",
        "支払",
        "支払いサイト",
        "サイト",
        "契約形態",
        "契約",
        "商流",
        "精算",
        "時間精算",
        "人数",
        "募集人数",
        "募　集",
        "面談",
        "面接",
        "備考",
        "尚可スキル",
        "言語",
        "OS",
        "DB",
        "開発環境",
    ]

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
            "line_filter_enabled": cls.ENABLE_LINE_FILTER,
            "line_filter_job_keywords": len(cls.LINE_FILTER_JOB_KEYWORDS),
            "line_filter_greeting_patterns": len(cls.LINE_FILTER_GREETING_PATTERNS),
            "index_rule_source": cls.INDEX_RULE_SOURCE,
            "index_rules_path": cls.INDEX_RULES_PATH,
            "index_rule_table": cls.INDEX_RULE_TABLE,
        }


# 使用方式
# from app.utils.config import Config
# print(Config.summary())
