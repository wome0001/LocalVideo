"""Fail-closed text-only public tree check. Reports locations, never secret values."""
from pathlib import Path
import argparse,os,re,subprocess,json
ALLOW={'.py','.md','.json','.yaml','.yml','.toml','.txt','.ps1','.sh','.in'}
SPECIAL={'LICENSE','.gitignore','.gitattributes'}
PATTERNS={
    'provider_token':re.compile(r'(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})'),
    'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'personal_windows_path':re.compile(r'[C-F]:[\\/]+Users[\\/]+(?!Public[\\/]|YOUR_USER[\\/])[^\s"\']+',re.I),
}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--staged',action='store_true');a=p.parse_args();root=a.root.resolve();fail=[];count=0
    entries=[]
    if a.staged:
        data=subprocess.check_output(['git','-C',str(root),'ls-files','--stage','-z']).decode('utf8')
        for row in filter(None,data.split('\0')):
            meta,name=row.split('\t',1);mode,oid,stage=meta.split()
            if mode!='100644' and mode!='100755':fail.append({'file':name,'issue':'non-regular Git entry'});continue
            entries.append((name,subprocess.check_output(['git','-C',str(root),'cat-file','blob',oid])))
    else:
        for base,dirs,files in os.walk(root,followlinks=False):
            dirs[:]=[d for d in dirs if d not in ('.git','__pycache__','.venv','venv') and not d.endswith('.egg-info')]
            for name in [*dirs,*files]:
                path=Path(base)/name;rel=path.relative_to(root).as_posix();st=path.lstat()
                if path.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:
                    fail.append({'file':rel,'issue':'reparse/symlink'})
                    if name in dirs:dirs.remove(name)
                    continue
                if path.is_file():
                    if st.st_size>1024*1024:fail.append({'file':rel,'issue':'unexpected large file'});continue
                    entries.append((rel,path.read_bytes()))
    for name,body in entries:
        count+=1;path=Path(name)
        if path.name not in SPECIAL and path.suffix not in ALLOW:fail.append({'file':name,'issue':'not allowed source/document type'});continue
        if len(body)>1024*1024:fail.append({'file':name,'issue':'unexpected large text file'});continue
        try:text=body.decode('utf-8-sig')
        except UnicodeDecodeError:fail.append({'file':name,'issue':'non UTF-8/binary'});continue
        if '\x00' in text:fail.append({'file':name,'issue':'binary NUL'});continue
        for label,pattern in PATTERNS.items():
            match=pattern.search(text)
            if match:fail.append({'file':name,'issue':label,'line':text[:match.start()].count('\n')+1})
    print(json.dumps({'status':'failed' if fail else 'passed','files':count,'findings':fail,'scope':'Current filesystem or exact staged blobs; separately review full Git history and provenance'},indent=2))
    if fail:raise SystemExit(1)
if __name__=='__main__':main()
