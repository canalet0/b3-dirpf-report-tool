import sys
from pathlib import Path


def write_report(content: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(content)
        sys.stdout.write("\n")
    else:
        output.write_text(content, encoding="utf-8")
