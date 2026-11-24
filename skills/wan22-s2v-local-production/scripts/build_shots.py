"""Build source-locked single-window S2V API graphs, without executing nodes."""
from pathlib import Path
import argparse,copy,json
from common import read,write,locked,copy_new,sha,ident,probe,under
def main():
 p=argparse.ArgumentParser();p.add_argument('run_config');p.add_argument('shot_list');a=p.parse_args()
 c=read(a.run_config);R=Path(c['project']).resolve();W=Path(c['work']).resolve();own=read(R/'provenance/ownership.json')
 M=Path(c['artifact_root']).resolve()
 assert Path(own['project']).resolve()==R and Path(own['work']).resolve()==W
 assert Path(own['artifact_root']).resolve()==M
 plan=read(a.shot_list);shots=plan['shots'];assert shots and len({s['id'] for s in shots})==len(shots)
 base=read(Path(__file__).resolve().parents[1]/'assets/s2v-template.json');prepared=[]
 required=['characters','scene','action','emotion','shot_size','camera','dialogue','duration','reference_id']
 # Validate whole batch before writing a graph or copying assets.
 for s in shots:
  ident(s['id']);tag=ident(s['id']+'-'+s['attempt'])
  for key in required:assert key in s,(tag,key)
  assert s['duration']>0 and s['expected_frames']>0 and s['fps']==16
  window=int(s['frame_window']);assert window>0 and window%4==0
  assert 0<s['expected_frames']<=window+1,'Only bounded single-window workflow is packaged'
  assert not (R/f'workflows/{tag}.json').exists(),'Version every attempt'
  image=locked(s['image']);audio=locked(s['audio']);text=locked(s['text_cache'])
  assert probe(image)['streams'][0]['width']==832 and probe(image)['streams'][0]['height']==480,'This profile needs 832x480 reference; make reviewed crop explicitly'
  assert any(v['codec_type']=='audio' for v in probe(audio)['streams'])
  names=[(image,W/f"input/img-{s['image']['sha256']}{image.suffix}"),(audio,W/f'input/{tag}{audio.suffix}')]
  assert names[0][1]!=names[1][1]
  if names[0][1].exists():assert sha(names[0][1])==s['image']['sha256']
  assert not names[1][1].exists(),names[1][1]
  prepared.append((s,tag,names,text))
 for s,tag,names,text in prepared:
  for src,dst in names:
   if dst.exists():assert sha(dst)==sha(src)
   else:copy_new(src,dst)
  cached=M/'inputs/text-cache'/(s['text_cache']['sha256']+'.safetensors')
  if cached.exists():assert sha(cached)==s['text_cache']['sha256']
  else:copy_new(text,cached)
  g=copy.deepcopy(base)
  g['5']['inputs']['image']=names[0][1].name;g['9']['inputs']['audio']=names[1][1].name
  g['12']['inputs'].update(path=str(cached),expected_sha256=s['text_cache']['sha256'])
  g['8']['inputs']['num_frames']=int(s['frame_window'])+1
  g['13']['inputs']['frame_window_size']=int(s['frame_window'])
  g['14']['inputs']['seed']=int(s.get('seed',45))
  g['17']['inputs']['filename_prefix']='shots/'+tag
  g['23']['inputs'].update(job_tag=tag,evidence_dir=str(R/'provenance/adapter'),reuse_cpu_weights=s.get('reuse_cpu_weights',False))
  dest=R/f'workflows/{tag}.json';write(dest,g)
  write(R/f'provenance/{tag}-inputs.json',{'shot':s,'graph':str(dest),'graph_sha256':sha(dest),'inputs':[{'path':str(dst),'sha256':sha(dst)} for _,dst in names],'text_cache':str(cached),'text_sha256':sha(cached),'expected_native_frames':s['expected_frames'],'expected_duration':s['expected_frames']/16,'warning':'Expected frames must be checked after execution; no inference performed'})
  print(tag,dest)
if __name__=='__main__':main()
