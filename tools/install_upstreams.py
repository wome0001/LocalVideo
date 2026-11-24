"""Clone one exact source revision into a new directory; no pip or model download."""
from pathlib import Path
import argparse,json,subprocess
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',required=True);p.add_argument('--destination',required=True,type=Path);a=p.parse_args()
    items=json.loads((Path(__file__).resolve().parents[1]/'configs/upstreams.lock.json').read_text(encoding='utf8'))['upstreams']
    item=next((x for x in items if x['name']==a.name),None)
    if item is None:raise ValueError('Unknown upstream')
    dest=a.destination.expanduser().resolve()
    if dest.exists():raise FileExistsError('Use a new destination; no existing source is overwritten')
    subprocess.run(['git','clone','--no-checkout',item['url'],str(dest)],check=True)
    subprocess.run(['git','-C',str(dest),'checkout','--detach',item['commit']],check=True)
    subprocess.run(['git','-C',str(dest),'submodule','update','--init','--recursive'],check=True)
    actual=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
    if actual!=item['commit']:raise RuntimeError('Commit mismatch')
    print(json.dumps({'name':a.name,'commit':actual,'destination':str(dest),'models_downloaded':False}))
if __name__=='__main__':main()
