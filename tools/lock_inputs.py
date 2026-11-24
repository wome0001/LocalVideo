"""Resolve user-owned reference paths and compute SHA256 for example plans."""
from pathlib import Path
import argparse,hashlib,json
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('template',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    def locked(path,expected):
        path=(a.template.resolve().parent/Path(path).expanduser()).resolve()
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if expected not in (None,'AUTO',actual):raise ValueError(f'Existing source SHA changed: {path}')
        return str(path),actual
    def visit(value):
        if isinstance(value,list):return [visit(v) for v in value]
        if not isinstance(value,dict):return value
        out={k:visit(v) for k,v in value.items()}
        if 'path' in out and 'sha256' in out:out['path'],out['sha256']=locked(out['path'],out['sha256'])
        if 'reference_audio' in out:out['reference_audio'],out['reference_sha256']=locked(out['reference_audio'],out.get('reference_sha256'))
        return out
    data=visit(json.loads(a.template.read_text(encoding='utf-8-sig')))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    print(a.output)
if __name__=='__main__':main()
