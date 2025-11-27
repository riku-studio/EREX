from app.services.preprocess import LineFilter


def test_filters_greeting_lines():
    line_filter = LineFilter()
    lines = ["お世話になっております", "案件名: テスト案件です"]

    assert line_filter.filter_lines(lines) == ["案件名: テスト案件です"]


def test_filters_signature_and_contact_lines():
    line_filter = LineFilter()
    lines = ["TEL: 03-1234-5678", "Mobile: 080-1111-2222", "週稼働 5日"]

    assert line_filter.filter_lines(lines) == ["週稼働 5日"]


def test_filters_footer_disclaimer_lines():
    line_filter = LineFilter()
    lines = ["配信停止をご希望の方はこちら", "必須スキル: Python"]

    assert line_filter.filter_lines(lines) == ["必須スキル: Python"]


def test_keeps_job_keywords_even_if_signature_pattern_present():
    line_filter = LineFilter()
    lines = ["案件名: API開発 TEL: 03-1234-5678", "外国籍不可"]

    assert line_filter.filter_lines(lines) == lines


def test_filters_decorative_lines():
    line_filter = LineFilter()
    lines = ["＝＝＝", "――――――", "スキル: Golang"]

    assert line_filter.filter_lines(lines) == ["スキル: Golang"]


def test_force_delete_overrides_job_keywords():
    class ConfigOverride:
        ENABLE_LINE_FILTER = True
        LINE_FILTER_DECORATION_CHARS = ""
        LINE_FILTER_GREETING_PATTERNS = []
        LINE_FILTER_CLOSING_PATTERNS = []
        LINE_FILTER_SIGNATURE_COMPANY_PREFIX = []
        LINE_FILTER_SIGNATURE_KEYWORDS = []
        LINE_FILTER_FOOTER_PATTERNS = []
        LINE_FILTER_JOB_KEYWORDS = ["案件"]
        LINE_FILTER_FORCE_DELETE_PATTERNS = [r".*@.*"]

    line_filter = LineFilter(config=ConfigOverride)
    lines = ["案件紹介 株式会社example@example.com", "案件情報: A"]

    assert line_filter.filter_lines(lines) == ["案件情報: A"]
