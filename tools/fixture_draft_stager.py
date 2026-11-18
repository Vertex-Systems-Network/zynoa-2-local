"""P00 ephemeral fixture draft staging (never source edits, code execution, or GitHub writes).

An LLM may suggest a DRAFT_ONLY fixture file, but a trusted host must provide
the same validated plan and candidate UTF-8 text. Candidates are staged under
a NEW OS-managed temporary directory, parsed *without execution*, hashed and
deleted before returning. No actual workspace file is read or written.

This is NOT an operating-system security sandbox or an autonomous patcher.
Never expose the model to this Python process's host filesystem privileges.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Mapping

from tools.dev_model_planner import ModelPlanDenied, validate_model_plan
from tools.workspace_policy import WorkspaceScope

_NAME = re.compile(r"^tests/fixtures/[A-Za-z0-9][A-Za-z0-9_.-]{0,71}\.(?:json|py|txt|md)$")
_MAX_ONE = 8192
_MAX_TOTAL = 32768
_MAX_LINES = 200


class FixtureStageDenied(ValueError):
    """Fail closed; never echo raw proposal text or private temporary paths."""


def _text_bytes(text: object) -> bytes:
    if not isinstance(text, str) or not text:
        raise FixtureStageDenied("candidate must be nonempty UTF-8 text")
    if unicodedata.normalize("NFC", text) != text:
        raise FixtureStageDenied("candidate is not NFC-normalized")
    for char in text:
        category = unicodedata.category(char)
        if category in ("Cf", "Cs") or (category == "Cc" and char not in ("\n", "\t")):
            raise FixtureStageDenied("candidate contains unsafe control characters")
    if text.count("\n") + 1 > _MAX_LINES:
        raise FixtureStageDenied("candidate has excessive line count")
    try:
        data = text.encode("utf-8", errors="strict")
    except UnicodeError:
        raise FixtureStageDenied("invalid UTF-8 candidate") from None
    if len(data) > _MAX_ONE:
        raise FixtureStageDenied("candidate too large")
    return data


def _static_parse(filename: str, value: str) -> str:
    try:
        if filename.endswith(".py"):
            # AST parser only; never import/eval/run or compile model code.
            ast.parse(value, filename="<ephemeral-fixture>")
            return "PYTHON_AST_PARSED_NOT_EXECUTED"
        if filename.endswith(".json"):
            json.loads(value)
            return "JSON_PARSED_NOT_EXECUTED"
        return "TEXT_VALIDATED_NOT_EXECUTED"
    except (SyntaxError, ValueError, UnicodeError, RecursionError):
        raise FixtureStageDenied("candidate static syntax check failed") from None


def preview_fixture_drafts(
    plan: dict, candidates: Mapping[str, str], scope: WorkspaceScope
) -> dict:
    """Static preview only. Actual source and user files stay untouched.

    The trusted host MUST separately authorize any later source-file changes
    and use a process-isolated broker. The model cannot call this to change
    the repository; the only writes here are to a fresh disposable tempdir.
    """
    if not isinstance(plan, dict) or not isinstance(candidates, dict):
        raise FixtureStageDenied("invalid plan or candidates")
    task_id = plan.get("task_id")
    try:
        validated = validate_model_plan(plan, task_id, scope)
    except (ModelPlanDenied, ValueError):
        raise FixtureStageDenied("untrusted model proposal failed validation") from None
    wanted = [entry["path"] for entry in validated["file_proposals"]]
    if set(candidates) != set(wanted) or len(candidates) != len(wanted):
        raise FixtureStageDenied("draft inventory must exactly match approved proposals")
    prepared = []
    total = 0
    for filename in wanted:
        if not _NAME.fullmatch(filename):
            raise FixtureStageDenied("only one-level tests/fixtures drafts permitted")
        # Path validation already done by validate_model_plan; rechecked
        # above before *any* disposable file is created.
        value = candidates[filename]
        data = _text_bytes(value)
        total += len(data)
        if total > _MAX_TOTAL:
            raise FixtureStageDenied("total draft bytes exceed preview budget")
        status = _static_parse(filename, value)
        prepared.append((filename, data, status))

    records = []
    # Only a newly allocated OS-owned temp directory is writable. The
    # workspace root is neither copied into this area nor changed.
    with tempfile.TemporaryDirectory(prefix="zynoa-p00-fixture-preview-") as parent:
        stage = Path(parent) / "tests" / "fixtures"
        stage.mkdir(parents=True, mode=0o700)
        for filename, data, status in prepared:
            dest = stage / filename.rsplit("/", 1)[-1]
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(dest, flags, 0o600)
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                    out.flush()
                    os.fsync(out.fileno())
                stored = dest.read_bytes()
            except OSError:
                raise FixtureStageDenied("disposable staging IO failed") from None
            if stored != data:
                raise FixtureStageDenied("staging integrity mismatch")
            records.append({
                "path": filename,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(stored).hexdigest(),
                "static_check": status,
            })
        # With cleanup on scope exit, nothing can be replayed as a source patch.
    receipt_data = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return {
        "status": "EPHEMERAL_FIXTURE_PREVIEW_ONLY",
        "phase": "P00",
        "task_id": task_id,
        "candidate_count": len(records),
        "total_candidate_bytes": total,
        "receipt_sha256": hashlib.sha256(receipt_data).hexdigest(),
        "candidate_receipts": records,
        "disposable_files_staged_and_removed": len(records),
        "workspace_files_written": 0,
        "user_files_written": 0,
        "commands_executed": 0,
        "github_writes": 0,
        "model_code_executed": False,
        "os_sandbox_verified": False,
        "persistent_worker_deployed": False,
    }
