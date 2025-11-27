"""
临时脚本：分割多招聘块并导出 CSV（一封邮件多行输出）。
用法：
    cd backend && uv run python tests/export_split_to_csv.py --input ../data --output ./tests/out_split.csv
"""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import List

# 确保 backend 根目录在 sys.path 中，便于直接运行脚本
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.cleaner import clean_body
from app.services.email_parser import EmailContent, parse_directory, parse_email_file
from app.services.preprocess import LineFilter
from app.services.semantic import prepare_semantic_input
from app.services.splitter import SplitBlock, Splitter
from app.utils.config import Config


def _load_messages(target: Path) -> List[EmailContent]:
    if target.is_file():
        return parse_email_file(target)
    return parse_directory(target)


def export_split_to_csv(input_path: Path, output_path: Path):
    start = time.perf_counter()
    contents = _load_messages(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    line_filter = LineFilter(Config)
    splitter = Splitter(Config)

    with output_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "source_path",
                "subject",
                "sender",
                "recipients",
                "received_at",
                "parser",
                "error",
                "block_index",
                "block_start_line",
                "block_end_line",
                "body_filtered",
                "block_text",
            ],
        )
        writer.writeheader()

        rows_written = 0
        for item in contents:
            body_clean = clean_body(item)
            body_filtered = prepare_semantic_input(body_clean, line_filter=line_filter)
            blocks = splitter.split(body_filtered)
            for idx, block in enumerate(blocks):
                writer.writerow(
                    {
                        "source_path": item.source_path,
                        "subject": item.subject,
                        "sender": item.sender,
                        "recipients": ";".join(item.recipients),
                        "received_at": item.received_at or "",
                        "parser": item.parser,
                        "error": item.error or "",
                        "block_index": idx,
                        "block_start_line": block.start_line,
                        "block_end_line": block.end_line,
                        "body_filtered": body_filtered,
                        "block_text": block.text,
                    }
                )
                rows_written += 1
                if rows_written % 10 == 0:
                    print(f"[progress] 已写入 {rows_written} 块")

    print(f"[done] 共写入 {rows_written} 块 -> {output_path}")
    print(f"[time] 总耗时 {time.perf_counter() - start:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Split multiple job blocks and export to CSV")
    parser.add_argument("--input", required=True, help="文件或目录路径，支持 .eml/.msg/.pst")
    parser.add_argument("--output", required=True, help="CSV 输出路径（将自动创建目录）")
    args = parser.parse_args()

    export_split_to_csv(Path(args.input), Path(args.output))
    print(f"CSV 已生成：{args.output}")


if __name__ == "__main__":
    main()
