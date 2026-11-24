"""Offline frame-counted edit assembly. Approved filters/audio timing are explicit."""
from pathlib import Path
import argparse,subprocess,time,json,shutil,math
from common import read,write,locked,FF,probe,sha,under

def audio_info(path):
 q=probe(path);streams=[s for s in q['streams'] if s['codec_type']=='audio']
 assert len(streams)==1,f'One explicit audio stream required: {path}'
 a=streams[0];rate=int(a['sample_rate']);channels=int(a['channels'])
 assert rate>0 and channels>0
 return a,rate,channels

def decoded_samples(path,rate,channels,start=None,end=None):
 args=[FF,'-nostdin','-v','error','-xerror','-i',str(path),'-map','0:a:0','-vn']
 if start is not None:args+=['-af',f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS']
 args+=['-ar',str(rate),'-ac',str(channels),'-c:a','pcm_s16le','-f','s16le','pipe:1']
 cp=subprocess.run(args,capture_output=True)
 assert cp.returncode==0,f'Audio decode failed: {path}: {cp.stderr.decode("utf8",errors="replace")[:1000]}'
 assert len(cp.stdout)%(channels*2)==0,'Incomplete decoded PCM sample'
 return len(cp.stdout)//(channels*2),args

def check_encoded_audio(path,seconds,rate,channels,*,aac=False):
 a,actual_rate,actual_channels=audio_info(path)
 assert (actual_rate,actual_channels)==(rate,channels),'Audio format changed; declare conversion explicitly'
 samples,args=decoded_samples(path,rate,channels);expected=round(seconds*rate)
 # Lossless intermediates must cover the complete window. AAC can retain only
 # its final codec padding; this is not permission to drop input samples.
 upper=1026 if aac else 2
 assert expected-2<=samples<=expected+upper,(path,'Audio sample coverage mismatch',samples,expected)
 start=float(a.get('start_time',0));assert math.isfinite(start) and abs(start)<=.002,(path,'Audio start offset',start)
 if a.get('duration') not in (None,'N/A'):
  assert abs(float(a['duration'])-seconds)<=max(.002,1026/rate if aac else 2/rate),(path,'Audio duration mismatch')
 return {'sample_rate':rate,'channels':channels,'decoded_samples':samples,'expected_samples':expected,'start_seconds':start,'allowed_trailing_codec_padding_samples':upper if aac else 0,'decode_command':args}
def main():
 p=argparse.ArgumentParser();p.add_argument('plan');a=p.parse_args();plan=read(a.plan)
 work=under(plan['work'],plan['roots']['temporary']);output=under(plan['output'],plan['roots']['media'])
 receipt=under(plan['receipt'],plan['roots']['metadata'])
 assert not output.is_relative_to(work) and not work.is_relative_to(output.parent),'Separate temporary and permanent media roots'
 assert not work.exists() and not output.exists() and not receipt.exists(),'Version outputs and receipt; do not overwrite'
 fps=int(plan['fps']);assert fps in (16,24,25,30,60)
 sources={};clips=plan['clips'];assert clips;window_checks=[];audio_format=None;preflight_commands=[]
 for c in clips:
  for k in ('video','audio'):
   key=(c[k]['path'],c[k]['sha256'])
   if key not in sources:sources[key]=locked(c[k])
  assert isinstance(c['frames'],int) and c['frames']>0
  assert abs(c['audio_end']-c['audio_start']-c['frames']/fps)<1e-6,'No implicit audio retiming or padding'
  assert c['audio_start']>=0
  assert all(isinstance(c[k],(int,float)) and math.isfinite(c[k]) for k in ('audio_start','audio_end'))
  assert c['video_filter'],'Explicit source trim/crop/FPS filter required'
  _,rate,channels=audio_info(c['audio']['path'])
  if audio_format is None:audio_format=(rate,channels)
  assert audio_format==(rate,channels),'Heterogeneous audio formats: explicitly prepare matching approved inputs first'
  samples,cmd=decoded_samples(c['audio']['path'],rate,channels,c['audio_start'],c['audio_end'])
  expected=round(c['frames']/fps*rate)
  assert abs(samples-expected)<=2,('Requested audio window not fully present',samples,expected,c['audio']['path'])
  window_checks.append({'source':c['audio']['path'],'source_sha256':c['audio']['sha256'],'start':c['audio_start'],'end':c['audio_end'],'decoded_samples':samples,'expected_samples':expected,'sample_rate':rate,'channels':channels});preflight_commands.append(cmd)
 sub=locked(plan['subtitles']) if plan.get('subtitles') else None
 work.mkdir(parents=True);output.parent.mkdir(parents=True,exist_ok=True)
 commands=preflight_commands;tick=time.monotonic();temps=[];intermediate_audio=[];rate,channels=audio_format
 def call(args):
  commands.append(args)
  cp=subprocess.run(args,capture_output=True)
  if cp.returncode:
   (work/'ffmpeg-failure.log').write_bytes(cp.stderr);raise RuntimeError(f'FFmpeg failed; see {work}')
 for i,c in enumerate(clips):
  dest=work/f'{i:04}.mkv';temps.append(dest)
  # FFV1 intermediates avoid repeated lossy compression. Locked voice is trimmed,
  # not resynthesized/normalized/stretched. Export codec is declared separately.
  call([FF,'-nostdin','-v','error','-threads','2','-i',c['video']['path'],'-i',c['audio']['path'],'-map','0:v:0','-map','1:a:0','-vf',c['video_filter'],'-af',f"atrim=start={c['audio_start']}:end={c['audio_end']},asetpts=PTS-STARTPTS",'-frames:v',str(c['frames']),'-t',str(c['frames']/fps),'-c:v','ffv1','-level','3','-c:a','pcm_s16le',str(dest)])
  q=probe(dest);v=next(x for x in q['streams'] if x['codec_type']=='video')
  assert int(v['nb_read_frames'])==c['frames'] and v['r_frame_rate']==f'{fps}/1'
  intermediate_audio.append(check_encoded_audio(dest,c['frames']/fps,rate,channels))
 listing=work/'concat.txt';listing.write_text(''.join("file '"+str(p).replace('\\','/').replace("'","'\\''")+"'\n" for p in temps),encoding='utf8')
 vf=[]
 if sub:
  local=work/('captions'+sub.suffix);shutil.copyfile(sub,local)
  # Relative basename avoids Windows drive-colon escaping inside lavfi.
  vf=['-vf',"subtitles=filename='"+local.name+"':force_style='FontName=Microsoft YaHei,FontSize=20,Outline=2,MarginV=18'"]
 total_seconds=sum(c['frames'] for c in clips)/fps
 args=[FF,'-nostdin','-v','error','-f','concat','-safe','0','-i',str(listing),*vf,'-t',str(total_seconds),'-c:v','libx264','-threads','4','-preset','fast','-crf',str(plan.get('crf',14)),'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output)]
 commands.append(args);cp=subprocess.run(args,cwd=work,capture_output=True)
 if cp.returncode:
  (work/'ffmpeg-failure.log').write_bytes(cp.stderr);raise RuntimeError('Final encode failed')
 final=probe(output);v=next(x for x in final['streams'] if x['codec_type']=='video')
 assert int(v['nb_read_frames'])==sum(c['frames'] for c in clips)
 final_audio=check_encoded_audio(output,total_seconds,rate,channels,aac=True)
 call([FF,'-nostdin','-v','error','-i',str(output),'-f','null','-'])
 write(receipt,{'status':'technical_self_checks_passed_pending_independent_review','plan':str(Path(a.plan).resolve()),'plan_sha256':sha(a.plan),'output':str(output),'sha256':sha(output),'seconds':time.monotonic()-tick,'commands':commands,'media':final,'audio_source_windows':window_checks,'intermediate_audio_checks':intermediate_audio,'final_audio_checks':final_audio,'audio_scope':'Decoded source windows and output sample coverage/start clock checked; AAC export is lossy and may retain final codec padding, not original encoded byte copy','native_fps_note':'Output FPS may include deterministic duplication; not native model FPS','not_verified':['subjective performance','auditory naturalness','identity or aesthetic approval']})
 print(output)
if __name__=='__main__':main()
