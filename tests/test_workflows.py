"""Synthetic-only checks; no model download, private media or external API."""
from pathlib import Path
import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    return subprocess.run([sys.executable,'-B',*map(str,args)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=180)

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='localvideo-test-');cls.base=Path(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_public_tree(self):
        p=run(ROOT/'tools/check_public_tree.py');self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_cli_option_forwarding(self):
        for command in ('models','dialogue-mix','tts','wan-init','compose'):
            p=run('-m','localvideo',command,'--help');self.assertEqual(p.returncode,0,p.stderr)

    def test_json_and_local_document_links(self):
        import re,urllib.parse
        for path in ROOT.rglob('*.json'):
            if '.git' not in path.parts:json.loads(path.read_text(encoding='utf-8-sig'))
        for path in ROOT.rglob('*.md'):
            if '.git' in path.parts:continue
            for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
                if target.startswith(('http:','https:','#','mailto:')):continue
                local=urllib.parse.unquote(target.split('#',1)[0].strip('<>'))
                self.assertTrue((path.parent/local).exists(),(path,target))

    def test_cpu_demo_and_audio_window_failure(self):
        target=self.base/'demo'
        p=run('-m','localvideo','demo','--work',target);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        receipt=json.loads((target/'metadata/assembly.json').read_text(encoding='utf8'))
        self.assertEqual(receipt['audio_source_windows'][0]['decoded_samples'],240000)
        self.assertEqual(receipt['final_audio_checks']['expected_samples'],240000)
        self.assertTrue((target/'media/demo.mp4').stat().st_size>1000)
        plan=json.loads((target/'metadata/edit-plan.json').read_text(encoding='utf8'))
        bad=copy.deepcopy(plan);bad.update(work=str(target/'temporary/invalid'),output=str(target/'media/invalid.mp4'),receipt=str(target/'metadata/invalid.json'))
        bad['clips'][0].update(audio_start=5,audio_end=10)
        path=target/'metadata/bad-plan.json';path.write_text(json.dumps(bad),encoding='utf8')
        p=run('-m','localvideo','compose',path);self.assertNotEqual(p.returncode,0)
        self.assertFalse(Path(bad['work']).exists());self.assertFalse(Path(bad['output']).exists());self.assertFalse(Path(bad['receipt']).exists())
        p=run('-m','localvideo','demo','--work',target);self.assertNotEqual(p.returncode,0)

    def test_initializer_validation_only_and_optimized_refusal(self):
        base=self.base/'init';base.mkdir()
        config={k:str(base/k) for k in ('project','work','hot','artifact_root')}
        config.update(comfy_root=str(base/'comfy'),comfy_python=sys.executable,model_library=str(base/'models'),plugin_root=str(base/'nodes'),validation_only=True)
        path=base/'config.json';path.write_text(json.dumps(config),encoding='utf8')
        p=run('-m','localvideo','wan-init',path);self.assertEqual(p.returncode,0,p.stderr)
        runtime=Path(config['project'])/'src/runtime.py'
        for extra in ([],['-O']):
            p=run(*extra,runtime,'stage');self.assertNotEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertFalse((base/'nodes').exists())
        p=run('-m','localvideo','wan-init',path);self.assertNotEqual(p.returncode,0)

    def test_benchmark_distinct_runs_and_finite_times(self):
        base=self.base/'benchmark';base.mkdir()
        paths=[]
        for i in range(4):
            path=base/f'{i}.json';path.write_text(json.dumps({'status':'generated_self_checked_pending_independent_review','sampler_checks':{'14':{'passed':True}},'comparison_settings':{'seed':45,'frames':81},'prompt_id':f'fresh-{i}','submitter_wall_seconds':100 if i<2 else 80}),encoding='utf8');paths.append(str(path))
        manifest=base/'manifest.json'
        def check(groups):
            manifest.write_text(json.dumps({'groups':groups}),encoding='utf8');return run('-m','localvideo','benchmark',manifest)
        p=check({'baseline':paths[:2],'optimized':paths[2:]});self.assertEqual(p.returncode,0,p.stderr)
        p=check({'baseline':[paths[0],paths[0]],'optimized':paths[2:]});self.assertNotEqual(p.returncode,0)
        data=json.loads(Path(paths[3]).read_text());data['submitter_wall_seconds']=float('nan');Path(paths[3]).write_text(json.dumps(data))
        self.assertNotEqual(check({'baseline':paths[:2],'optimized':paths[2:]}).returncode,0)

    def test_hash_lock_and_unconsented_voice_rejection(self):
        base=self.base/'lock';base.mkdir();(base/'reference.txt').write_text('original')
        path=base/'plan.json';path.write_text(json.dumps({'input':{'path':'reference.txt','sha256':'f'*64}}))
        dest=base/'locked.json';p=run(ROOT/'tools/lock_inputs.py',path,'--output',dest)
        self.assertNotEqual(p.returncode,0);self.assertFalse(dest.exists())
        engine=base/'engine';engine.mkdir();model=base/'model';model.mkdir()
        plan=base/'dialogue.json';plan.write_text(json.dumps({'scenes':[{'lines':[{'id':'line01','role':'A','text':'test'}]}]}))
        voices=base/'voices.json';voices.write_text(json.dumps({'A':{'consent_confirmed':False}}))
        p=run(ROOT/'tools/cosyvoice2_batch.py','--plan',plan,'--voices',voices,'--cosy-root',engine,'--model',model,'--output',base/'takes')
        self.assertNotEqual(p.returncode,0);self.assertIn('authorized',p.stderr);self.assertFalse((base/'takes').exists())

    def test_dialogue_mixing_with_synthetic_takes(self):
        import wave,math,array,shutil
        base=self.base/'dialogue';base.mkdir();takes=base/'takes';takes.mkdir()
        plan=json.loads((ROOT/'examples/dialogue.plan.json').read_text(encoding='utf8'))
        for scene in plan['scenes']:
            for row in scene['lines']:
                target=takes/(row['id']+'.wav')
                values=array.array('h',(0 if i<9600 or i>=43200 else round(3000*math.sin(2*math.pi*220*i/48000)) for i in range(48000)))
                with wave.open(str(target),'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(48000);out.writeframes(values.tobytes())
                target.with_suffix('.json').write_text(json.dumps({'text':row['text'],'voice':'synthetic-test-tone'}),encoding='utf8')
        planfile=base/'plan.json';planfile.write_text(json.dumps(plan),encoding='utf8')
        dest=base/'audition';ff=os.environ.get('LOCALVIDEO_FFMPEG') or shutil.which('ffmpeg')
        p=run('-m','localvideo','dialogue-mix','--plan',planfile,'--takes',takes,'--output',dest,'--ffmpeg',ff)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        p=run('-m','localvideo','dialogue-check',dest/'dialogue-audition.wav',dest/'dialogue-audition.srt')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(len(json.loads((dest/'timeline.json').read_text())['dialogue_scenes'][0]['cues']),3)

    def test_privacy_negative(self):
        base=self.base/'privacy';base.mkdir();(base/'bad.txt').write_text('gh'+'p_'+'x'*36)
        p=run(ROOT/'tools/check_public_tree.py','--root',base)
        self.assertNotEqual(p.returncode,0);self.assertNotIn('x'*36,p.stdout)

if __name__=='__main__':unittest.main()
