"""Portable entrypoints. No automatic downloads, GPU start or source deletion."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(os.environ.get('LOCALVIDEO_HOME',Path(__file__).resolve().parents[2])).resolve()

def tool(name):
    path=ROOT/name
    if not path.is_file():raise RuntimeError('Clone the repository and use pip install -e .; or set LOCALVIDEO_HOME to that clone')
    return path

def call(name,args,python=None):
    subprocess.run([python or sys.executable,'-B',str(tool(name)),*map(str,args)],check=True)

def doctor():
    tools={k:os.environ.get('LOCALVIDEO_'+k.upper()) or shutil.which(k) for k in ('ffmpeg','ffprobe')}
    data={'python':sys.version.split()[0],'platform':sys.platform,'tools':tools,'gpu':None,'scope':'Inspection only; no installation or system changes'}
    for key,value in tools.items():
        data[key+'_ok']=False
        if value:
            p=subprocess.run([value,'-version'],capture_output=True,text=True)
            data[key+'_ok']=p.returncode==0
    smi=shutil.which('nvidia-smi')
    if smi:
        p=subprocess.run([smi,'--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True)
        data['gpu']=p.stdout.strip() if p.returncode==0 else 'query failed'
    print(json.dumps(data,indent=2,ensure_ascii=False))
    if not all(data[k+'_ok'] for k in tools):raise SystemExit('Install FFmpeg/ffprobe or set LOCALVIDEO_FFMPEG and LOCALVIDEO_FFPROBE')

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def demo(root):
    root=root.expanduser().resolve()
    if root.exists():raise FileExistsError('Use a new demo directory')
    root.mkdir(parents=True)
    media=root/'media';metadata=root/'metadata';temp=root/'temporary'
    for folder in (media,metadata,temp):folder.mkdir()
    ff=os.environ.get('LOCALVIDEO_FFMPEG') or shutil.which('ffmpeg')
    if not ff:raise RuntimeError('FFmpeg not found; run localvideo doctor')
    video=media/'test-card.mp4';audio=media/'test-tone.wav'
    subprocess.run([ff,'-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=832x480:rate=16:duration=5','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p',str(video)],check=True)
    subprocess.run([ff,'-nostdin','-v','error','-f','lavfi','-i','sine=frequency=330:sample_rate=48000:duration=5','-c:a','pcm_s16le',str(audio)],check=True)
    sub=metadata/'captions.srt'
    sub.write_text('1\n00:00:00,200 --> 00:00:02,200\nLocalVideo: local workflow smoke test\n\n2\n00:00:02,700 --> 00:00:04,700\nSynthetic test tone. No AI or speech model used.\n',encoding='utf8')
    plan={'roots':{'temporary':str(temp),'media':str(media),'metadata':str(metadata)},'work':str(temp/'assembly'),'output':str(media/'demo.mp4'),'receipt':str(metadata/'assembly.json'),'fps':16,'subtitles':{'path':str(sub),'sha256':sha(sub)},'clips':[{'video':{'path':str(video),'sha256':sha(video)},'audio':{'path':str(audio),'sha256':sha(audio)},'video_filter':'trim=start=0:end=5,setpts=PTS-STARTPTS,setsar=1,format=yuv420p,fps=16','frames':80,'audio_start':0,'audio_end':5}]}
    path=metadata/'edit-plan.json';path.write_text(json.dumps(plan,indent=2),encoding='utf8')
    call('skills/wan22-s2v-local-production/scripts/compose_from_plan.py',[path])
    print(json.dumps({'status':'technical_smoke_test_completed','video':str(media/'demo.mp4'),'receipt':str(metadata/'assembly.json'),'not_verified':['AI generation','speech naturalness','model quality']},ensure_ascii=False))

def main():
    if sys.flags.optimize:raise RuntimeError('Use normal Python, not python -O')
    routes={'wan-init':'skills/wan22-s2v-local-production/scripts/prepare_run.py','wan-build':'skills/wan22-s2v-local-production/scripts/build_shots.py','compose':'skills/wan22-s2v-local-production/scripts/compose_from_plan.py','dialogue-mix':'skills/scene-dialogue/scripts/compose_audition.py','dialogue-check':'skills/scene-dialogue/scripts/validate_audition.py','models':'tools/models.py','encode-text':'tools/encode_wan_text.py','tts':'tools/cosyvoice2_batch.py','svd':'tools/svd_generate.py','benchmark':'tools/benchmark_report.py'}
    if len(sys.argv)>1 and sys.argv[1] in routes:
        call(routes[sys.argv[1]],sys.argv[2:]);return
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
    s.add_parser('doctor')
    d=s.add_parser('demo');d.add_argument('--work',required=True,type=Path)
    for command in ('wan-init','wan-build','compose','dialogue-mix','dialogue-check','models','encode-text','tts','svd','benchmark'):
        t=s.add_parser(command,add_help=False);t.add_argument('args',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if a.action=='doctor':doctor();return
    if a.action=='demo':demo(a.work);return
