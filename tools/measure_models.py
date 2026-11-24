"""Read-only footprint measurement, excluding reparse points and no deletion."""
from pathlib import Path
import argparse,json,os
def measure(root):
    root=Path(root).resolve();total=weights=count=0;skipped=[]
    suffixes={'.safetensors','.bin','.pt','.pth','.onnx','.ckpt','.tflite'}
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in dirs[:]:
            path=Path(base)/name;st=path.lstat()
            if path.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:dirs.remove(name);skipped.append(str(path.relative_to(root)))
        for name in files:
            path=Path(base)/name;st=path.lstat()
            if path.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:skipped.append(str(path.relative_to(root)));continue
            total+=st.st_size;count+=1
            if path.suffix.lower() in suffixes:weights+=st.st_size
    return {'files':count,'logical_bytes':total,'weight_bytes':weights,'logical_GiB':round(total/2**30,3),'skipped_reparse_points':skipped,'scope':'Logical file lengths, not allocated bytes, VRAM or peak runtime memory; shared components must not be double-counted'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    if not a.root.is_dir():raise FileNotFoundError(a.root)
    print(json.dumps(measure(a.root),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
