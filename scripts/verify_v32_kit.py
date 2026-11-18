#!/usr/bin/env python3
"""Static v3.2 specification validator; NOT a desktop product acceptance test."""
import csv,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
errors=[]
metadata=json.loads((R/'KIT_METADATA.json').read_text())
with (R/'docs/ui/OPTION_CATALOG.csv').open(encoding='utf-8') as f:options=list(csv.DictReader(f))
with (R/'docs/ui/SCREEN_INVENTORY.csv').open(encoding='utf-8') as f:screens=list(csv.DictReader(f))
manifest=json.loads((R/'docs/screenshots/MANIFEST.json').read_text())
mods=sorted((R/'docs/modules').glob('M[0-9][0-9].md'))
states=json.loads((R/'docs/state/MODULES.json').read_text())
for k,v in [('modules',len(mods)),('ui_options',len(options)),('ui_screens',len(screens)),('screenshot_obligations',len(manifest['required']))]:
    if metadata[k]!=v:errors.append(f'{k}: metadata {metadata[k]} != actual {v}')
if len(mods)!=26 or len(states)!=26:errors.append('M26 module/state missing')
for i in range(1,27):
    m=f'M{i:02d}'
    for name in [f'docs/modules/{m}.md',f'docs/help/articles/{m}.md',f'docs/wiki/pages/{m}.md',f'docs/diagrams/{m.lower()}-flow.svg']:
        if not (R/name).is_file():errors.append('missing '+name)
for rel in ['docs/MASTER_PLAN_V3_2.md','docs/PLANNING_CHANGELOG.md','CHANGELOG.md','docs/operations/CHANGE_INTELLIGENCE_CHANGELOG.md','docs/changelog/schema/change-record.schema.json','docs/changelog/schema/change-event.schema.json','docs/research/CHANGELOG_TOOL_COMPARISON.csv','docs/adr/0007-change-intelligence-and-changelog.md','tools/changelog.py','scripts/check_changelog_pr.py','tests/test_changelog.py','.github/pull_request_template.md']:
    if not (R/rel).is_file():errors.append('missing '+rel)
ids=[x['asset_id'] for x in manifest['required']]
if len(ids)!=len(set(ids)):errors.append('duplicate asset id')
for m,inv,attr in [('M26',screens,'screen_id'),('M26',options,'option_id')]:
    for r in [e for e in inv if e['module_id']==m]:
        if r[attr] not in ids:errors.append('missing manifest screenshot '+r[attr])
if not (sum(x['module_id']=='M26' for x in screens)==8 and sum(x['module_id']=='M26' for x in options)==20):errors.append('M26 screen/option count wrong')
if any(x.get('status')=='CAPTURED' and not (R/x['path']).is_file() for x in manifest['required']):errors.append('false captured screenshots')
if 'CHANGE-01' not in (R/'docs/quality/RELEASE_GATES.md').read_text():errors.append('no change gate')
if 'CHANGE INTELLIGENCE' not in (R/'AGENTS.md').read_text().upper():errors.append('AI rules missing changelog')
if 'verify_v32_kit.py' not in (R/'.github/workflows/governance.yml').read_text():errors.append('CI spec validator not wired')
print(json.dumps({'status':'PASS' if not errors else 'FAIL','spec_version':metadata.get('version'),'modules':len(mods),'screens':len(screens),'options':len(options),'screenshot_obligations':len(manifest['required']),'product_implemented':False,'errors':errors},indent=2))
sys.exit(bool(errors))
