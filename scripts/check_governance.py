#!/usr/bin/env python3
"""V3 canonical policy integrity. Not a substitute for full desktop security tests."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = [
    'AGENTS.md','docs/agent/AI_STRICT_PROTOCOL.md','docs/MASTER_PLAN_V3_2.md','CLAUDE.md','GEMINI.md','.cursor/rules/00-project-governance.mdc',
    '.github/copilot-instructions.md','.github/pull_request_template.md',
    'docs/MASTER_PLAN_V3.md','docs/state/STATUS.md','docs/state/HANDOFF.md',
    'docs/state/PHASE.json','docs/state/PHASES.json','docs/state/MODULES.json',
    'docs/research/DESIGN_RESEARCH.md','docs/quality/PRE_DEVELOPMENT_CHECKLIST.md',
    'docs/quality/RELEASE_GATES.md','docs/operations/ISSUE_AUTOMATION.md',
    'docs/operations/DOCUMENTATION_HELP_WIKI.md'
]
errors=[]
for f in REQUIRED:
    path=ROOT/f
    if not path.is_file() or not path.read_text(encoding='utf-8').strip(): errors.append('Missing/empty: '+f)
try:
    phase=json.loads((ROOT/'docs/state/PHASE.json').read_text())
    if phase.get('schema_version') != 3:errors.append('Phase schema version must be 3')
    if not str(phase.get('phase','')).startswith('P'):errors.append('phase must start P')
    if phase.get('active_branch') and not phase['active_branch'].startswith('phase/'):
        errors.append('Current active phase branch must be phase/*')
    if phase.get('primary_pr') is not None and phase.get('active_branch') is None:
        errors.append('Primary PR requires a phase branch')
    if phase.get('phase_status') == 'MERGED_VERIFIED' and not phase.get('last_verified_remote_sha'):
        errors.append('Merged phase requires verified remote commit')
except Exception as e:errors.append('Invalid phase state: '+str(e))
for name in ['CLAUDE.md','GEMINI.md','.github/copilot-instructions.md','.cursor/rules/00-project-governance.mdc']:
    p=ROOT/name
    if p.is_file() and not all(k in p.read_text() for k in ('AGENTS.md','AI_STRICT_PROTOCOL.md')): errors.append(name+' must link AGENTS.md and AI_STRICT_PROTOCOL.md')
    if p.is_file() and 'MASTER_PLAN_V3.md' in p.read_text(): errors.append(name+' points to superseded plan V3')
if errors:
    for e in errors:print('ERROR:',e)
    sys.exit(1)
print('V3 governance: PASS (local static policy)')
