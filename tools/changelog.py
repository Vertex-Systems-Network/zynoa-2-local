#!/usr/bin/env python3
"""Local PR change record validator and demo changelog renderer.

This does NOT query GitHub, sign a release, prove a published installer, or provide
runtime event persistence. Never ship demo output as authoritative release notes.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys

VALID_KINDS={'feature','enhancement','bugfix','performance','security','breaking','docs','dependency','maintenance'}
VALID_STATES={'reported','triaged','planned','implementing','merged','verified','released','reverted','cancelled'}
CHANNELS={'stable','beta','nightly','security','internal'}
REQUIRED={'change_id','module_id','kind','title','summary','status','audience','source_issue_urls','source_pr_url','docs_paths','help_paths','wiki_paths','test_evidence','commit_sha','release','verification','breaking_change','migration_notes','created_at','updated_at','version_bump'}
GROUPS={'feature':'Added','enhancement':'Added','bugfix':'Fixed','performance':'Changed','security':'Security','breaking':'Changed','docs':'Changed','dependency':'Changed','maintenance':'Changed'}
ORDER=['Added','Changed','Deprecated','Removed','Fixed','Security']

def _iso(value, *, date_only=False):
    if not isinstance(value,str): return False
    try:
        if date_only: dt.date.fromisoformat(value)
        else: dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        return True
    except ValueError:return False

def _safe_repo_path(p):
    return isinstance(p,str) and bool(p) and not p.startswith(('/', '\\')) and '..' not in Path(p).parts and '\\' not in p and p.startswith('docs/')

def validate_records(records:list, root:Path|None=None, check_docs:bool=False)->list[str]:
    errors=[]
    if not isinstance(records,list):return ['Top-level records must be a JSON array']
    seen=set()
    for i,r in enumerate(records):
        loc=f'record[{i}]'
        if not isinstance(r,dict):errors.append(f'{loc}: must be object');continue
        mid=r.get('change_id')
        if not isinstance(mid,str) or not re.fullmatch(r'CHG-[A-Za-z0-9-]{5,80}',mid):errors.append(f'{loc}: invalid change_id')
        elif mid in seen:errors.append(f'{loc}: duplicate change_id {mid}')
        seen.add(mid)
        missing=REQUIRED-set(r)
        if missing:errors.append(f'{loc}: missing {sorted(missing)}');continue
        if not re.fullmatch(r'M[0-9]{2}',str(r['module_id'])):errors.append(f'{loc}: invalid module_id')
        if r['kind'] not in VALID_KINDS:errors.append(f'{loc}: invalid kind')
        if r['status'] not in VALID_STATES:errors.append(f'{loc}: invalid status')
        if r['audience'] not in {'user','developer','private'}:errors.append(f'{loc}: invalid audience')
        if r['version_bump'] not in {'major','minor','patch','none'}:errors.append(f'{loc}: invalid version_bump')
        if not isinstance(r['title'],str) or len(r['title'])<3:errors.append(f'{loc}: invalid title')
        if not isinstance(r['summary'],str) or len(r['summary'])<8:errors.append(f'{loc}: invalid summary')
        for k in ['created_at','updated_at']:
            if not _iso(r[k]):errors.append(f'{loc}: invalid {k}')
        for key in ['source_issue_urls','docs_paths','help_paths','wiki_paths','test_evidence']:
            if not isinstance(r[key],list) or any(not isinstance(x,str) for x in r[key]):errors.append(f'{loc}: invalid {key}')
        for key in ['docs_paths','help_paths','wiki_paths']:
            if isinstance(r[key],list):
                for path in r[key]:
                    if not _safe_repo_path(path):errors.append(f'{loc}: unsafe {key} path {path!r}')
                    elif check_docs and root and not (root/path).is_file():errors.append(f'{loc}: missing linked documentation {path}')
        if not isinstance(r.get('breaking_change'),bool):errors.append(f'{loc}: breaking_change must be bool')
        if not isinstance(r.get('migration_notes'),str):errors.append(f'{loc}: migration_notes must be string')
        if r.get('breaking_change') and not r.get('migration_notes'):errors.append(f'{loc}: breaking change missing migration notes')
        v=r['verification']
        if not isinstance(v,dict) or any(not isinstance(v.get(k),bool) for k in ['tests_passed','merge_verified','release_published']):
            errors.append(f'{loc}: invalid verification flags');v={}
        if r['status']=='released':
            if any(not v.get(k) for k in ['tests_passed','merge_verified','release_published']): errors.append(f'{loc}: released without all verification flags')
            if not r.get('source_pr_url') or not r.get('commit_sha'):errors.append(f'{loc}: released without PR and SHA evidence')
            if not all(isinstance(r[k],list) and r[k] for k in ['docs_paths','help_paths','wiki_paths','test_evidence']):errors.append(f'{loc}: released without docs/help/wiki/test links')
            release=r.get('release')
            if not isinstance(release,dict) or not all(release.get(k) for k in ['version','date','channel']):errors.append(f'{loc}: released without version, date and channel')
            else:
                if release['channel'] not in CHANNELS:errors.append(f'{loc}: bad channel')
                if not _iso(release['date'],date_only=True):errors.append(f'{loc}: bad release date')
        elif r.get('release') is not None:
            errors.append(f'{loc}: non-released record must not claim a published release')
        if r.get('audience')!='private':
            for url in (r.get('source_issue_urls') or [])+[r.get('source_pr_url')] if isinstance(r.get('source_issue_urls'),list) else []:
                if url is not None and not (isinstance(url,str) and url.startswith('https://')):errors.append(f'{loc}: invalid public link')
    return errors

def _clean_markdown(s):
    s=' '.join(str(s).split())
    # Escape Markdown link syntax and angle brackets; do not render raw source URLs.
    return re.sub(r'([\\`*_[\]<>])',r'\\\1',s)

def render_preview(records:list,version:str,date:str,channel:str='stable')->str:
    errors=validate_records(records)
    if errors:raise ValueError('Invalid records: '+'; '.join(errors))
    if not _iso(date,date_only=True):raise ValueError('Invalid release date')
    if channel not in CHANNELS:raise ValueError('Invalid release channel')
    eligible=[r for r in records if r['status']=='released' and r['audience']=='user' and r['release'] and r['release']['version']==version and r['release']['date']==date and r['release']['channel']==channel]
    if not eligible:raise ValueError('No verified user-visible released records match requested version/channel/date')
    groups={k:[] for k in ORDER}
    for r in sorted(eligible,key=lambda x:x['change_id']):
        line=f"- {_clean_markdown(r['summary'])} ({_clean_markdown(r['change_id'])}; {_clean_markdown(r['module_id'])})."
        groups[GROUPS[r['kind']]].append(line)
    lines=['<!-- TEST PREVIEW ONLY: NOT A PUBLISHED APPLICATION RELEASE -->',f'## [{_clean_markdown(version)}] - {date} ({channel})']
    for section in ORDER:
        if groups[section]:lines.extend(['',f'### {section}',*groups[section]])
    return '\n'.join(lines)+'\n'

def read_records(path:Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    return data if isinstance(data,list) else [data]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='action',required=True)
    for action in ('validate','render'):
        p=sub.add_parser(action);p.add_argument('--records',required=True,type=Path);p.add_argument('--check-docs',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
        if action=='render':
            p.add_argument('--version',required=True);p.add_argument('--date',required=True);p.add_argument('--channel',default='stable')
    args=ap.parse_args()
    try:
        records=read_records(args.records)
        errors=validate_records(records,args.root,args.check_docs)
        if errors:
            for e in errors:print('ERROR:',e,file=sys.stderr)
            return 1
        if args.action=='validate':print(f'PASS — {len(records)} local fixture/PR records valid; no remote-release proof checked');return 0
        print(render_preview(records,args.version,args.date,args.channel),end='');return 0
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print('ERROR:',e,file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
