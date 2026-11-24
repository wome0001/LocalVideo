"""Encode locally through ComfyUI's native WAN text loader, once per prompt."""
from pathlib import Path
import argparse,json,sys,hashlib,os,time
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('comfy-root','encoder','prompt','negative','output'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    if a.output.exists() or a.output.with_suffix('.json').exists():raise FileExistsError(a.output)
    positive=a.prompt.read_text(encoding='utf8');negative=a.negative.read_text(encoding='utf8')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    sys.path.insert(0,str(a.comfy_root.resolve()));sys.argv=sys.argv[:1]
    import torch, comfy.sd
    from safetensors.torch import save_file
    tick=time.monotonic()
    clip=comfy.sd.load_clip(ckpt_paths=[str(a.encoder.resolve())],embedding_directory=[],clip_type=comfy.sd.CLIPType.WAN)
    tensors={}
    with torch.inference_mode():
        for key,text in (('positive',positive),('negative',negative)):
            tensors[key]=clip.encode_from_tokens_scheduled(clip.tokenize(text))[0][0].detach().cpu().contiguous()
            if not tensors[key].numel():raise RuntimeError('Empty text embeddings')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    save_file(tensors,str(a.output),metadata={'positive_text':positive,'negative_text':negative})
    def sha(path):
        with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    a.output.with_suffix('.json').write_text(json.dumps({'sha256':sha(a.output),'encoder_sha256':sha(a.encoder),'seconds':time.monotonic()-tick,'tensor_shapes':{k:list(v.shape) for k,v in tensors.items()}},indent=2),encoding='utf8')
if __name__=='__main__':main()
