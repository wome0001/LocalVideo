"""Inspect/download pinned public model files. No account or token handling."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,urllib.request,os
CATALOG=Path(__file__).resolve().parents[1]/'configs/models.json'
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library',type=Path,required=True);p.add_argument('--download',action='store_true');p.add_argument('--catalog',type=Path,default=CATALOG);p.add_argument('--route');a=p.parse_args()
    root=a.library.expanduser().resolve();items=json.loads(a.catalog.read_text(encoding='utf8'))['files']
    if a.route:items=[x for x in items if x.get('route')==a.route]
    if not items:raise ValueError('No matching model records')
    for item in items:
        rel=PurePosixPath(item['relative'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid catalog path')
        target=(root/str(rel)).resolve()
        if not target.is_relative_to(root):raise ValueError('Model target outside library')
        if not target.exists():
            if not a.download:print('MISSING',item['relative']);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            # Exclusive create; incomplete downloads are preserved, never silently retried/overwritten.
            with urllib.request.urlopen(item['url'],timeout=60) as response,target.open('xb') as out:
                while block:=response.read(8*1024*1024):out.write(block)
                out.flush();os.fsync(out.fileno())
        actual=sha(target)
        if actual!=item['sha256'] or target.stat().st_size!=item['bytes']:raise ValueError(f'Model content mismatch; preserved for investigation: {target}')
        meta=target.with_suffix('.verified.json')
        record={'verified':True,'sha256':actual,'actual_sha256':actual,'url':item['url'],'size':item['bytes']}
        if meta.exists():
            prior=json.loads(meta.read_text(encoding='utf-8-sig'))
            if (prior.get('actual_sha256') or prior.get('sha256'))!=actual:raise ValueError('Existing verification record conflicts')
        else:
            with meta.open('x',encoding='utf8') as f:json.dump(record,f,indent=2)
        print('VERIFIED',item['relative'])
if __name__=='__main__':main()
