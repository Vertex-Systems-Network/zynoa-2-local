"""Deterministic P02 UI static reviewer for reviewdog's errorformat reporter.

Outputs file:line: message diagnostics, no network, no arbitrary evaluation.
Reviewdog filters diagnostics to changed PR lines; existing mandatory CI remains the gate.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

UI_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".jsx"})
FORBIDDEN = {
    "dangerouslySetInnerHTML": "P02-RD001 unsafe HTML injection: render typed plain text",
    "localStorage": "P02-RD002 UI preference persistence is not yet authorized",
    "sessionStorage": "P02-RD003 UI storage must use an approved native contract",
    "document.write(": "P02-RD004 DOM document injection bypasses React",
    "new Function(": "P02-RD005 arbitrary source execution is forbidden",
    "eval(": "P02-RD006 arbitrary source evaluation is forbidden",
}
FOCUS_HIDING = re.compile(
    r"(?:button|input|select|textarea|a\b|workbench-tabpanel)"
    r"[^{}]*:focus(?!-visible)[^{]*\{[^}]*outline\s*:\s*(?:0|none)\b",
    re.IGNORECASE,
)
IMG = re.compile(r"<img(?:\s|/|>)")


def review_text(path: str, data: str) -> list[tuple[str, int, str]]:
    """Return only actionable high-confidence P02 UI violations."""
    findings: list[tuple[str, int, str]] = []
    suffix = Path(path).suffix
    if suffix in UI_SUFFIXES:
        for number, line in enumerate(data.splitlines(), 1):
            if line.lstrip().startswith(("//", "*", "/*")):
                continue
            for marker, warning in FORBIDDEN.items():
                if marker in line:
                    findings.append((path, number, warning))
            if IMG.search(line) and "alt=" not in line:
                findings.append((path, number, "P02-RD007 native images must have alt text"))
    if suffix == ".css":
        for match in FOCUS_HIDING.finditer(data):
            number = data.count("\n", 0, match.start()) + 1
            findings.append((path, number, "P02-RD008 interactive keyboard focus outline is hidden"))
    return findings


def review(root: Path) -> list[tuple[str, int, str]]:
    src = root / "apps/desktop/src"
    issues: list[tuple[str, int, str]] = []
    for file in sorted(src.rglob("*")):
        if file.is_file() and file.suffix in UI_SUFFIXES | {".css"}:
            issues.extend(review_text(file.relative_to(root).as_posix(), file.read_text(encoding="utf-8")))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    for filename, line, issue in review(args.root):
        print(f"{filename}:{line}: {issue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
