"""Local per-line casting. Run in the separately installed CosyVoice environment."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','voices','cosy-root','model','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--device',choices=('cpu','cuda'),default='cpu');p.add_argument('--threads',type=int,default=6)
    p.add_argument('--mode',choices=('zero-shot','directed'),default='zero-shot')
    a=p.parse_args();plan=json.loads(a.plan.read_text(encoding='utf-8-sig'));voices=json.loads(a.voices.read_text(encoding='utf-8-sig'))
    if not a.cosy_root.is_dir() or not a.model.is_dir():raise FileNotFoundError('Prepare the complete local CosyVoice source and model directories first')
    rows=[row for scene in plan['scenes'] for row in scene['lines']]
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('Unique nonempty cue IDs required')
    import re
    for row in rows:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,72}',row['id']):raise ValueError('Invalid cue ID')
        v=voices[row['role']]
        if v.get('consent_confirmed') is not True:raise ValueError('Use only explicitly authorized voice references')
        ref=Path(v['reference_audio'])
        if not ref.is_file() or sha(ref)!=v['reference_sha256']:raise ValueError('Reference missing or changed')
        if not v['reference_text'].strip():raise ValueError('Exact transcript of reference is required')
        if not .85<=float(row.get('rate',1))<=1.15:raise ValueError('Use restrained scene-specific speaking rate')
    if a.output.exists():raise FileExistsError('Use a new take directory; never overwrite approved takes')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'):os.environ[key]='1'
    if a.device=='cpu':os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path.insert(0,str(a.cosy_root.resolve()));sys.path.insert(0,str(a.cosy_root.resolve()/'third_party/Matcha-TTS'))
    import numpy as np, soundfile as sf, torch
    import torchaudio
    # Avoid implicit TorchCodec/download dependencies for local reference WAVs.
    def local_wave(path,*args,**kwargs):
        value,rate=sf.read(path,dtype='float32',always_2d=True)
        return torch.from_numpy(value.T.copy()),rate
    torchaudio.load=local_wave
    from cosyvoice.cli.cosyvoice import AutoModel
    torch.set_num_threads(a.threads);started=time.monotonic()
    model=AutoModel(model_dir=str(a.model.resolve()),fp16=False)
    for role in {r['role'] for r in rows}:
        v=voices[role];model.add_zero_shot_spk(v['reference_text'],v['reference_audio'],role)
    loaded=time.monotonic()-started;a.output.mkdir(parents=True)
    for row in rows:
        tick=time.monotonic();seed=int(row.get('seed',42));torch.manual_seed(seed);np.random.seed(seed)
        v=voices[row['role']];rate=float(row.get('rate',1));mode=row.get('mode',a.mode)
        with torch.inference_mode():
            if mode=='directed':
                # Experimental, upstream-internal API: do not claim universal SSML support.
                direction=row['direction']+'<|endofprompt|>';front=model.frontend
                cond=front.frontend_instruct2(row['text'],direction,v['reference_audio'],model.sample_rate,row['role'])
                token,length=front._extract_text_token(direction);cond.update(prompt_text=token,prompt_text_len=length)
                stream=model.model.tts(**cond,stream=False,speed=rate)
            elif mode=='zero-shot':
                stream=model.inference_zero_shot(row['text'],'','',zero_shot_spk_id=row['role'],stream=False,speed=rate,text_frontend=False)
            else:raise ValueError('Unsupported line mode')
            chunks=[x['tts_speech'].detach().cpu() for x in stream]
        if not chunks:raise RuntimeError('TTS emitted no speech')
        speech=torch.cat(chunks,dim=-1).reshape(-1).numpy()
        if len(speech)<model.sample_rate*.16 or not np.isfinite(speech).all() or np.max(np.abs(speech))<.005:raise RuntimeError('Invalid take; retain prior outputs and retry with a versioned directory')
        wave=a.output/(row['id']+'.wav');sf.write(wave,speech,model.sample_rate,subtype='PCM_24')
        meta={'id':row['id'],'text':row['text'],'voice':v.get('name',row['role']),'reference_sha256':v['reference_sha256'],'wave_sha256':sha(wave),'seed':seed,'rate':rate,'mode':mode,'model_load_seconds':loaded,'inference_seconds':time.monotonic()-tick,'seconds':len(speech)/model.sample_rate,'engine':'CosyVoice2-0.5B','device':a.device,'quality_status':'pending_listening_review'}
        wave.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps({'cue':row['id'],'seconds':meta['seconds'],'inference_seconds':meta['inference_seconds']}),flush=True)
if __name__=='__main__':main()
