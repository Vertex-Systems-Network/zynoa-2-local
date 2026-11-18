#!/usr/bin/env python3
"""PR changed-path gate. In a real GitHub Actions PR this requires a real base SHA.
In non-repository distributed spec kits it explicitly reports NOT VERIFIED.
"""
import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.changelog import validate_records
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('GITHUB_BASE_SHA')
if not BASE:
    print('CHG-PR-GATE: NOT VERIFIED — no GITHUB_BASE_SHA; requires GitHub PR checkout')
    sys.exit(0)
p=subprocess.run(['git','diff','--name-only',f'{BASE}...HEAD'],cwd=ROOT,capture_output=True,text=True)
if p.returncode:
    print('CHG-PR-GATE: FAIL — cannot verify base commit:',p.stderr.strip(),file=sys.stderr)
    sys.exit(1)
changed=[x.strip() for x in p.stdout.splitlines() if x.strip()]
code_changes=[x for x in changed if x.startswith(('apps/','crates/','packages/','optional-workers/'))]
record_files=[ROOT/x for x in changed if x.startswith(('.changes/records/','docs/changelog/records/')) and x.endswith('.json')]
if code_changes and not record_files:
    print('CHG-PR-GATE: FAIL — product code changes require change record in same PR',file=sys.stderr)
    sys.exit(1)
errors=[]
for f in record_files:
    if not f.is_file():continue
    try:
        data=json.loads(f.read_text())
        errors+=validate_records(data if isinstance(data,list) else [data],ROOT,check_docs=True)
    except Exception as exc:errors.append(f'{f}: {exc}')
if errors:
    for e in errors:print('CHG-PR-GATE: FAIL:',e,file=sys.stderr)
    sys.exit(1)
print(f'CHG-PR-GATE: PASS (changed code files: {len(code_changes)}, PR change records: {len(record_files)})')
