#!/usr/bin/env python3
"""Local incident ingestion demo (no network). Sanitizes, deduplicates and persists.

Remote GitHub relay / end-user consent configuration are NOT implemented by this tool.
"""
import argparse,datetime,hashlib,json,re,sqlite3,sys
from pathlib import Path

SENSITIVE_KEYS=('password','secret','token','authorization','cookie','prompt','source','filepath','filename','code','document','email','ip_address','user_id','chat')
SAFE_KEYS={'module','error_code','severity','source_type','app_version','platform','message_class'}
LEVELS={'P0','P1','P2','P3'}


def scrub(text):
    t=str(text)[:400]
    t=re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._\-]+',r'\1[REDACTED]',t)
    t=re.sub(r'(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*\S+',r'\1=[REDACTED]',t)
    t=re.sub(r'[A-Za-z]:\\(?:[^\s\\]+\\)+[^\s\\]*','[LOCAL_PATH]',t)
    t=re.sub(r'/((?:home|Users)/)[^\s:/]+(?:/[^\s:]*)?','/[REDACTED_PATH]',t)
    t=re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','[EMAIL]',t)
    t=re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[IP_ADDRESS]',t)
    return t


def sanitize(event):
    if not isinstance(event,dict): raise ValueError('Incident must be object')
    if event.get('severity','P2') not in LEVELS: raise ValueError('Unsupported severity')
    out={k:scrub(event[k]) for k in SAFE_KEYS if k in event}
    out['severity']=event.get('severity','P2')
    out['module']=re.sub(r'[^A-Z0-9]','',str(event.get('module','UNKNOWN')).upper())[:12] or 'UNKNOWN'
    out['error_code']=re.sub(r'[^A-Z0-9_]','',str(event.get('error_code','UNKNOWN')).upper())[:64]
    out['message_class']=re.sub(r'[^A-Za-z0-9_ .-]','',scrub(event.get('message_class','RuntimeError')))[:100]
    out['app_version']=re.sub(r'[^0-9A-Za-z.+-]','',str(event.get('app_version','unknown')))[:35]
    # Do not retain stack/content from an end-user incident, even if caller supplies it.
    band='.'.join(out['app_version'].split('.')[:2])
    seed='|'.join([out['module'],out['error_code'],out['message_class'],band])
    out['fingerprint']=hashlib.sha256(seed.encode()).hexdigest()[:32]
    out['schema_version']=1
    out['redaction_policy']='v1'
    return out


def upsert(db_path,record):
    db=sqlite3.connect(db_path)
    db.execute('CREATE TABLE IF NOT EXISTS incidents (fingerprint TEXT PRIMARY KEY, body TEXT NOT NULL, count INTEGER NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL)')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    row=db.execute('SELECT count,first_seen FROM incidents WHERE fingerprint=?',(record['fingerprint'],)).fetchone()
    count=(row[0]+1) if row else 1
    first=row[1] if row else now
    db.execute('INSERT OR REPLACE INTO incidents VALUES (?,?,?,?,?)',(record['fingerprint'],json.dumps(record,sort_keys=True),count,first,now))
    db.commit();db.close()
    return {'fingerprint':record['fingerprint'],'occurrence_count':count,'first_seen':first,'last_seen':now,'publication':'LOCAL_ONLY'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--event',required=True,type=Path)
    p.add_argument('--db',required=True,type=Path)
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    event=json.loads(args.event.read_text(encoding='utf-8'))
    clean=sanitize(event)
    if args.dry_run:
        result={'sanitized':clean,'publication':'DRY_RUN_NO_NETWORK'}
    else:
        args.db.parent.mkdir(parents=True,exist_ok=True)
        result=upsert(args.db,clean)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
