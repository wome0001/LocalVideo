"""Compare all software-decoded native RGB24 frames, PTS, duration and size."""
from pathlib import Path
import argparse,subprocess,json
from common import FF,write,sha,probe
def frames(path):
 p=subprocess.run([FF,'-v','error','-threads','1','-i',str(path),'-map','0:v:0','-an','-vf','format=rgb24','-fps_mode','passthrough','-f','framehash','-hash','sha256','-'],capture_output=True,check=True)
 assert not p.stderr,p.stderr
 text=p.stdout.decode();return p.stdout,[v.strip() for v in text.splitlines() if v and not v.startswith('#')],[v for v in text.splitlines() if v.startswith(('#tb','#dimensions'))]
def main():
 p=argparse.ArgumentParser();p.add_argument('reference');p.add_argument('candidate');p.add_argument('--evidence',required=True);p.add_argument('--expected-frames',type=int,required=True);a=p.parse_args()
 out=Path(a.evidence);assert not out.exists(),'Use a new evidence directory';out.mkdir(parents=True)
 data=[]
 for label,path in [('reference',a.reference),('candidate',a.candidate)]:
  raw,rows,header=frames(path);(out/f'{label}.framehash').write_bytes(raw)
  data.append({'label':label,'path':str(Path(path).resolve()),'sha256':sha(path),'rows':rows,'header':header,'probe':probe(path)})
 passed=len(data[0]['rows'])==a.expected_frames and data[0]['rows']==data[1]['rows'] and data[0]['header']==data[1]['header']
 write(out/'comparison.json',{'status':'exact_native_rgb_pts_match' if passed else 'different_or_wrong_frame_count','passed':passed,'expected_frames':a.expected_frames,'sources':data,'scope':'No audio, identity, aesthetic or dialogue naturalness verdict'})
 print('EXACT_MATCH' if passed else 'DIFFERENT');raise SystemExit(0 if passed else 2)
if __name__=='__main__':main()
