"""
Export tech keyword summary to stdout (block-level, de-duplicated per block).

Usage:
    cd backend && uv run python tests/export_keyword_summary.py --input ../data
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure backend root importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.cleaner import clean_body
from app.services.email_parser import EmailContent, parse_directory, parse_email_file
from app.services.extractor import KeywordExtractor
from app.services.preprocess import LineFilter
from app.services.splitter import Splitter
from app.services.semantic import prepare_semantic_input


def _load_messages(target: Path):
    if target.is_file():
        return parse_email_file(target)
    return parse_directory(target)


def main():
    parser = argparse.ArgumentParser(description="Print keyword summary grouped by category")
    parser.add_argument("--input", required=True, help="Path to file or directory containing messages")
    args = parser.parse_args()

    start = time.perf_counter()
    contents = _load_messages(Path(args.input))

    line_filter = LineFilter()
    splitter = Splitter()
    extractor = KeywordExtractor()

    blocks = []
    for msg in contents:
        body_clean = clean_body(msg)
        body_filtered = prepare_semantic_input(body_clean, line_filter=line_filter)
        blocks.extend(block.text for block in splitter.split(body_filtered))

    summary = extractor.summarize(blocks)
    total_blocks = len(blocks)
    print(f"Total blocks: {total_blocks}")
    for category, items in summary.items():
        if not items:
            continue
        print(f"\n[{category}]")
        for item in items:
            ratio_pct = item['ratio'] * 100
            print(f"  {item['keyword']}: {item['count']} ({ratio_pct:.1f}%)")

    print(f"\n[done] elapsed={time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    main()
