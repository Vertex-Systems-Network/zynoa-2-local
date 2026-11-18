#!/usr/bin/env python3
"""Verify v3 local spec completeness. Does not validate a running product or GitHub."""
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
required=['AGENTS.md','CLAUDE.md','GEMINI.md','docs/MASTER_PLAN_V3.md','docs/quality/PRE_DEVELOPMENT_CHECKLIST.md','docs/quality/RELEASE_GATES.md','docs/operations/ISSUE_AUTOMATION.md','docs/operations/DOCUMENTATION_HELP_WIKI.md','docs/research/DESIGN_RESEARCH.md','docs/ui/OPTION_CATALOG.csv','docs/ui/SCREEN_INVENTORY.csv','docs/screenshots/MANIFEST.json','docs/state/MODULES.json']
for path in required:
    if not (ROOT/path).is_file(): errors.append('Missing required '+path)
mods=sorted((ROOT/'docs/modules').glob('M[0-9][0-9].md'))
if len(mods)!=26: errors.append(f'Expected 26 modules, found {len(mods)}')
for p in mods:
    mid=p.stem
    for rel in [f'docs/help/articles/{mid}.md',f'docs/wiki/pages/{mid}.md',f'docs/diagrams/{mid.lower()}-flow.svg']:
        if not (ROOT/rel).is_file(): errors.append('Missing related '+rel)
with (ROOT/'docs/ui/OPTION_CATALOG.csv').open(encoding='utf-8') as f: opts=list(csv.DictReader(f))
with (ROOT/'docs/ui/SCREEN_INVENTORY.csv').open(encoding='utf-8') as f: screens=list(csv.DictReader(f))
manifest=json.loads((ROOT/'docs/screenshots/MANIFEST.json').read_text())
if len(manifest['required'])!=len(opts)+len(screens): errors.append('Screenshot obligations mismatch')
if any(entry['status']=='CAPTURED' and not (ROOT/entry['path']).is_file() for entry in manifest['required']): errors.append('Falsely marked captured screenshot')

module_states=json.loads((ROOT/'docs/state/MODULES.json').read_text())
if len(module_states)!=26: errors.append('Expected 26 module state entries')
for entry in module_states:
    if entry.get('state')!='COMPLETED_VERIFIED': continue
    module_id=entry['module']
    if not entry.get('completed_commit_sha'): errors.append(module_id+' missing completion commit SHA')
    for capture in (x for x in manifest['required'] if x['module']==module_id):
        if capture.get('status')!='CAPTURED' or not (ROOT/capture['path']).is_file(): errors.append(module_id+' missing real screenshot '+capture['asset_id'])
    article=ROOT/f'docs/help/articles/{module_id}.md'
    if 'PENDING' in article.read_text():errors.append(module_id+' help contains pending screenshot placeholders')

print(json.dumps({'result':'PASS' if not errors else 'FAIL','module_dossiers':len(mods),'option_specs':len(opts),'screens':len(screens),'screenshot_obligations':len(manifest['required']),'actual_product_screenshots_captured':0,'errors':errors},indent=2))
sys.exit(1 if errors else 0)
