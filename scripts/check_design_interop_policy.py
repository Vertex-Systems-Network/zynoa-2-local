#!/usr/bin/env python3
"""Static P00 DESIGN-IO specification policy check; not a product functionality test."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "docs/MASTER_PLAN_V3_2.md",
    "docs/PHASE_SPECS.md",
    "docs/operations/DESIGN_INTEROPERABILITY.md",
    "docs/adr/0008-design-import-export-gate.md",
    "docs/quality/RELEASE_GATES.md",
]

def validate(root=ROOT):
    problems = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            problems.append("Missing: " + relative)
    if problems:
        return problems
    contract = (root / "docs/operations/DESIGN_INTEROPERABILITY.md").read_text(encoding="utf-8")
    phase = (root / "docs/PHASE_SPECS.md").read_text(encoding="utf-8")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    master = (root / "docs/MASTER_PLAN_V3_2.md").read_text(encoding="utf-8")
    gate = (root / "docs/quality/RELEASE_GATES.md").read_text(encoding="utf-8")
    for item in ("P08I", "DESIGN-IO-01", "DESIGN-IO-10", "Figma", "Penpot", "OpenPencil", "Unsupported"):
        if item not in contract:
            problems.append("Missing contract marker: " + item)
    if "## P08I" not in phase or "P08 verified" not in phase:
        problems.append("P08I must be a phase only after P08 verified merge")
    if "P08I" not in master or "P08I" not in agents:
        problems.append("Master/agent rules missing deferred interoperability")
    if "DESIGN-IO-01" not in gate:
        problems.append("Quality gate DESIGN-IO-01 missing")
    return problems

if __name__ == "__main__":
    errors = validate()
    print("DESIGN-IO POLICY:", "PASS (spec only)" if not errors else "FAIL")
    for error in errors:
        print("ERROR:", error)
    sys.exit(1 if errors else 0)
