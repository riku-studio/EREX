"""
按“外国籍 可/不可”分类统计并输出摘要。
用法：
    cd backend && uv run python tests/export_classifier_foreigner.py --input ../data
"""

import argparse
import sys
import time
from pathlib import Path

# 确保 backend 根目录可导入
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.cleaner import clean_body
from app.services.classifier import Classifier
from app.services.email_parser import EmailContent, parse_directory, parse_email_file
from app.services.preprocess import LineFilter
from app.services.semantic import prepare_semantic_input
from app.services.splitter import Splitter


def _load_messages(target: Path):
    if target.is_file():
        return parse_email_file(target)
    return parse_directory(target)


def main():
    parser = argparse.ArgumentParser(description="Classify foreigner eligibility from emails")
    parser.add_argument("--input", required=True, help="文件或目录路径，支持 .eml/.msg/.pst")
    parser.add_argument(
        "--config",
        default=str(BACKEND_ROOT / "config" / "classifiers" / "foreigner.json"),
        help="分类器配置文件路径（默认为 foreigner.json）",
    )
    args = parser.parse_args()

    start = time.perf_counter()
    contents = _load_messages(Path(args.input))

    line_filter = LineFilter()
    splitter = Splitter()
    classifier = Classifier(args.config)

    blocks = []
    for msg in contents:
        body_clean = clean_body(msg)
        body_filtered = prepare_semantic_input(body_clean, line_filter=line_filter)
        blocks.extend(block.text for block in splitter.split(body_filtered))

    summary = classifier.summarize(blocks)
    total = len(blocks)
    print(f"Total blocks: {total}")
    for cls, stats in summary.items():
        ratio_pct = stats["ratio"] * 100
        print(f"  {cls}: {stats['count']} ({ratio_pct:.1f}%)")

    print(f"[done] elapsed={time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    main()
