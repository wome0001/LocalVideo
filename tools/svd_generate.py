"""SVD-XT silent I2V. Run in the separate pinned Diffusers GPU environment."""
from pathlib import Path
import argparse,hashlib,json,os,time
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('model','image','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--seed',type=int,default=45);p.add_argument('--steps',type=int,default=30);a=p.parse_args()
    if not a.model.is_dir() or not a.image.is_file():raise FileNotFoundError('Local model directory and authorized image required')
    if a.output.exists() or a.output.with_suffix('.json').exists():raise FileExistsError('Video or evidence already exists')
    from PIL import Image
    image=Image.open(a.image).convert('RGB')
    if image.size!=(1024,576):raise ValueError('Make and review an explicit 1024x576 crop; no hidden identity-changing resize')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    import torch,diffusers
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import export_to_video
    tick=time.monotonic()
    pipe=StableVideoDiffusionPipeline.from_pretrained(str(a.model),variant='fp16',torch_dtype=torch.float16,local_files_only=True)
    pipe.enable_model_cpu_offload();pipe.unet.enable_forward_chunking(chunk_size=5,dim=0)
    load_seconds=time.monotonic()-tick;sampling=time.monotonic()
    with torch.inference_mode():frames=pipe(image,num_frames=25,num_inference_steps=a.steps,min_guidance_scale=3,max_guidance_scale=3,fps=7,motion_bucket_id=127,noise_aug_strength=.02,decode_chunk_size=8,generator=torch.Generator(device='cpu').manual_seed(a.seed)).frames[0]
    a.output.parent.mkdir(parents=True,exist_ok=True);export_to_video(frames,str(a.output),fps=7)
    def sha(path):
        with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    a.output.with_suffix('.json').write_text(json.dumps({'status':'generated_pending_quality_review','model':'SVD-XT','silent':True,'image_sha256':sha(a.image),'video_sha256':sha(a.output),'seed':a.seed,'steps':a.steps,'frames':len(frames),'fps':7,'model_load_seconds':load_seconds,'sampling_decode_export_seconds':time.monotonic()-sampling,'torch':torch.__version__,'diffusers':diffusers.__version__},indent=2),encoding='utf8')
if __name__=='__main__':main()
