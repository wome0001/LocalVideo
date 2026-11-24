"""Portable tools and source locks. Do not use Python optimized mode."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
if sys.flags.optimize:raise RuntimeError('Do not use python -O: workflow contracts require assertions')
FF=os.environ.get('LOCALVIDEO_FFMPEG') or shutil.which('ffmpeg') or 'ffmpeg'
PROBE=os.environ.get('LOCALVIDEO_FFPROBE') or shutil.which('ffprobe') or 'ffprobe'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def locked(item):
 p=Path(item['path']).resolve();assert p.is_file(),p
 assert re.fullmatch('[a-f0-9]{64}',item['sha256']),item
 assert sha(p)==item['sha256'],f'Input changed: {p}'
 return p
def copy_new(src,dst):
 dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 with Path(src).open('rb') as a,dst.open('xb') as b:
  while data:=a.read(8*1024*1024):b.write(data)
 assert sha(src)==sha(dst)
def probe(p):return json.loads(subprocess.check_output([PROBE,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def ident(s):assert re.fullmatch('[A-Za-z0-9_-]{1,72}',s),s;return s
def under(p,root):
 p=Path(p).resolve();r=Path(root).resolve();assert p.is_relative_to(r) and p!=r,(p,r);return p
