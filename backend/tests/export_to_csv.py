"""
临时测试脚本：解析目录下的 .eml/.msg/.pst 邮件，清洗正文并导出为 CSV。

用法：
    cd backend && uv run python tests/export_to_csv.py --input ../data --output ./tests/out.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, List

# 确保 backend 根目录在 sys.path 中，便于直接运行脚本
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.cleaner import clean_body
from app.services.email_parser import EmailContent, parse_directory, parse_email_file


def _load_messages(target: Path) -> List[EmailContent]:
    if target.is_file():
        return parse_email_file(target)
    return parse_directory(target)


def _rows(contents: Iterable[EmailContent]):
    for item in contents:
        yield {
            "source_path": item.source_path,
            "subject": item.subject,
            "sender": item.sender,
            "recipients": ";".join(item.recipients),
            "received_at": item.received_at or "",
            "parser": item.parser,
            "error": item.error or "",
            "body_clean": clean_body(item),
        }


def export_to_csv(input_path: Path, output_path: Path):
    contents = _load_messages(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
                "body_clean",
            ],
        )
        writer.writeheader()
        writer.writerows(_rows(contents))


def main():
    parser = argparse.ArgumentParser(description="Export parsed emails to CSV (test-only helper)")
    parser.add_argument("--input", required=True, help="文件或目录路径，支持 .eml/.msg/.pst")
    parser.add_argument("--output", required=True, help="CSV 输出路径（将自动创建目录）")
    args = parser.parse_args()

    export_to_csv(Path(args.input), Path(args.output))
    print(f"CSV 已生成：{args.output}")


if __name__ == "__main__":
    main()
