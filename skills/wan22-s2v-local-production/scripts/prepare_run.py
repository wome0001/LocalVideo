"""Create a portable owned run; never download models or start GPU."""
from pathlib import Path
import argparse,json,sys
from common import read,write,copy_new,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--install-plugin',action='store_true');a=p.parse_args()
    c=read(a.config);S=Path(__file__).resolve().parents[1]
    names=('project','work','hot','artifact_root')
    roots=[Path(c[k]).expanduser().resolve() for k in names]
    for x in roots:
        assert x!=Path(x.anchor),'Never use a drive/filesystem root'
        assert not x.exists(),f'Use a fresh run: {x}'
        for y in roots:
            if x!=y:assert not x.is_relative_to(y),'Ownership roots must not overlap'
    assert len(set(roots))==4
    R,W,E,M=roots
    for key in ('comfy_root','comfy_python','model_library','plugin_root'):
        c[key]=str(Path(c[key]).expanduser().resolve())
    port=int(c.get('port',8193));assert 1024<=port<=65535
    test=bool(c.get('validation_only',False));assert not(test and a.install_plugin)
    target=Path(c['plugin_root'])/'CreatorWanS2VNodes'
    plugin_files=list((S/'assets/CreatorWanS2VNodes').glob('*.py'))
    if a.install_plugin:
        for f in plugin_files:
            dest=target/f.name
            if dest.exists():assert sha(dest)==sha(f),f'Existing plugin differs: {dest}; use versioned deployment'
    for d in roots:d.mkdir(parents=True)
    for d in ('src/vendor','provenance/jobs','workflows','inputs','research'):(R/d).mkdir(parents=True)
    for d in ('renders/native','delivery'):(M/d).mkdir(parents=True)
    for d in ('input','output','logs','temp','user','base/models','base/custom_nodes'):(W/d).mkdir(parents=True)
    values={'@@PROJECT@@':repr(str(R)),'@@WORK@@':repr(str(W)),'@@HOT@@':repr(str(E)),
            '@@ARTIFACT@@':repr(str(M)),'@@PORT@@':str(port),'@@VALIDATION_ONLY@@':repr(test),
            '@@MODELLIB@@':repr(c['model_library']),'@@PYTHON@@':repr(c['comfy_python']),
            '@@COMFYROOT@@':repr(c['comfy_root']),'@@PLUGINROOT@@':repr(c['plugin_root']),
            '@@FFMPEG@@':repr(c.get('ffmpeg','ffmpeg')),'@@FFPROBE@@':repr(c.get('ffprobe','ffprobe'))}
    text=(S/'assets/runtime_template.py.in').read_text(encoding='utf8')
    for token,value in values.items():text=text.replace(token,value)
    assert '@@' not in text;compile(text,'runtime.py','exec')
    (R/'src/runtime.py').write_text(text,encoding='utf8')
    copy_new(S/'scripts/comfy_submit.py',R/'src/vendor/comfy_submit.py')
    q=lambda x:json.dumps(str(x),ensure_ascii=False)
    paths=f'run_hot:\n  base_path: {q(E/"models")}\n  is_default: true\n  diffusion_models: diffusion_models\n  audio_encoders: audio_encoders\n  vae: vae\n  loras: loras\nlibrary:\n  base_path: {q(c["model_library"])}\n  diffusion_models: diffusion_models\n  text_encoders: text_encoders\n  audio_encoders: audio_encoders\n  vae: vae\n  loras: loras\nwrapper_nodes:\n  custom_nodes: {q(Path(c["comfy_root"])/"custom_nodes")}\nlocalvideo_nodes:\n  custom_nodes: {q(c["plugin_root"])}\n'
    (R/'workflows/extra-paths.yaml').write_text(paths,encoding='utf8')
    deployed=[]
    if a.install_plugin:
        for f in plugin_files:
            dest=target/f.name
            if not dest.exists():copy_new(f,dest)
            deployed.append({'path':str(dest),'sha256':sha(dest)})
    c.update({k:str(v) for k,v in zip(names,roots)});c.update(port=port)
    write(R/'run-config.json',c)
    write(R/'provenance/ownership.json',dict(zip(names,map(str,roots)))|{'validation_only':test,'installed_plugin':deployed,'gpu_started':False,'models_staged':False})
    print(json.dumps({'project':str(R),'runtime':str(R/'src/runtime.py'),'validation_only':test}))
if __name__=='__main__':main()
