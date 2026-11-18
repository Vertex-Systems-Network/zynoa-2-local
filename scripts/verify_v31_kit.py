#!/usr/bin/env python3
"""Spec verification only, NOT a product or signed installer test."""
from pathlib import Path
import json,csv,sys
root=Path(__file__).resolve().parents[1]
errors=[]
modules=sorted((root/'docs/modules').glob('M[0-9][0-9].md'))
if len(modules)!=26:errors.append(f'Expected 26 module documents: got {len(modules)}')
for i in range(1,27):
    mid=f'M{i:02d}'
    for r in [f'docs/modules/{mid}.md',f'docs/help/articles/{mid}.md',f'docs/wiki/pages/{mid}.md',f'docs/diagrams/{mid.lower()}-flow.svg']:
        if not (root/r).exists():errors.append('Missing '+r)
with (root/'docs/ui/OPTION_CATALOG.csv').open(encoding='utf-8') as f:opts=list(csv.DictReader(f))
with (root/'docs/ui/SCREEN_INVENTORY.csv').open(encoding='utf-8') as f:screens=list(csv.DictReader(f))
manifest=json.loads((root/'docs/screenshots/MANIFEST.json').read_text())
if len(manifest['required'])!=len(opts)+len(screens):errors.append('Screenshot obligation count mismatch')
ids=[x['asset_id'] for x in manifest['required']]
if len(ids)!=len(set(ids)):errors.append('Duplicate screenshot IDs')
if any(x.get('status')=='CAPTURED' and not (root/x['path']).is_file() for x in manifest['required']):errors.append('False claim of screenshot captured')
states=json.loads((root/'docs/state/MODULES.json').read_text())
if len(states)!=26:errors.append('Expected 26 status entries')
for file in ['docs/operations/DATA_VAULT_BACKUP_RECOVERY.md','docs/operations/STORAGE_DOWNLOADS_RELOCATION.md','docs/operations/AUTO_RELEASE_AND_UPDATES.md','templates/github-workflows/release-windows.yml']:
    if not (root/file).is_file():errors.append('Missing system design '+file)
for mid in ['M23','M24','M25']:
    if not any(x['module_id']==mid for x in opts):errors.append('Missing options '+mid)
    if not any(x['module_id']==mid for x in screens):errors.append('Missing screens '+mid)
for module in ['M23','M24','M25']:
    if not any(x['module']==module for x in manifest['required']):errors.append('Missing screenshot obligations '+module)
for required in ['data/state.sqlite','backup','user','rollback','signature']:
    if not any(required.lower() in (root/p).read_text(encoding='utf-8').lower() for p in ['docs/operations/DATA_VAULT_BACKUP_RECOVERY.md','docs/operations/STORAGE_DOWNLOADS_RELOCATION.md','docs/operations/AUTO_RELEASE_AND_UPDATES.md']):
        errors.append('Missing critical topic '+required)
print(json.dumps({'status':'PASS' if not errors else 'FAIL','module_specifications':len(modules),'ui_screens':len(screens),'option_specifications':len(opts),'screenshot_obligations_pending':len(manifest['required']),'actual_application_built':False,'errors':errors},indent=2))
sys.exit(bool(errors))
