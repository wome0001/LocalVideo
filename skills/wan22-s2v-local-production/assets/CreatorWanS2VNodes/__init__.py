"""Optional Wan2.2 inference adapter; per-sampler state, no project paths or core edits."""
import contextvars,functools,hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
import torch
from safetensors.torch import load_file
from . import cpu_weight_views as views

BUILD_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ACTIVE=contextvars.ContextVar('creator_wan_s2v_sampler',default=None)
INSTALLED=False

def loaded(suffix):
    modules=[m for m in list(sys.modules.values()) if str(getattr(m,'__file__','')).replace('\\','/').lower().endswith(suffix.lower())]
    if len(modules)!=1:raise RuntimeError('Expected exactly one loaded WanVideoWrapper module: '+suffix)
    return modules[0]

def dump(path,value):
    with path.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def install_hooks():
    global INSTALLED
    if INSTALLED:return
    if any('/CreatorWanProfile/' in str(getattr(m,'__file__','')).replace('\\','/') for m in list(sys.modules.values())):
        raise RuntimeError('Use an isolated backend without the old diagnostic hook')
    sampler=loaded('/ComfyUI-WanVideoWrapper/nodes_sampler.py')
    model=loaded('/ComfyUI-WanVideoWrapper/wanvideo/modules/model.py')
    original_to=model.WanAttentionBlock.to
    @functools.wraps(original_to)
    def block_to(self,*args,**kwargs):
        state=ACTIVE.get()
        if state is None or not state['reuse']:return original_to(self,*args,**kwargs)
        target=views.device_only(args,kwargs)
        if target is None:return original_to(self,*args,**kwargs)
        cache=state['cpu_views'];key=id(self)
        if target.type=='cuda':
            if key not in cache:cache[key]=views.capture(self)
            else:
                views.validate_cpu(self,cache[key])
                if any(param.data_ptr()!=value.data_ptr() for _,param,value,*_ in cache[key]):
                    raise RuntimeError('Onload must start at original CPU parameter storage')
        elif key in cache:
            proof=views.restore(self,cache[key])
            result=original_to(self,*args,**kwargs) # preserve every mutable buffer
            state['restores'].append(proof)
            return result
        return original_to(self,*args,**kwargs)
    original_forward=model.WanModel.forward
    @functools.wraps(original_forward)
    def forward(self,*args,**kwargs):
        state=ACTIVE.get()
        if state is not None and self is state['transformer']:state['forward_calls']+=1
        return original_forward(self,*args,**kwargs)
    original_sampler=sampler.WanVideoSampler.process
    @functools.wraps(original_sampler)
    def sample(self,*args,**kwargs):
        # ComfyUI passes node inputs by name; preserve positional calling contract too.
        import inspect
        bound=inspect.signature(original_sampler).bind(self,*args,**kwargs);bound.apply_defaults()
        patcher=bound.arguments['model'];options=patcher.model_options.get('transformer_options',{})
        cfg=options.get('creator_s2v_reuse')
        if cfg is None:return original_sampler(self,*args,**kwargs)
        out=Path(cfg['evidence_dir'])/(cfg['job_tag']+'-result.json')
        if out.exists():raise RuntimeError('This job tag already has evidence; use a new attempt ID')
        swap=options.get('block_swap_args') or {}
        if cfg['enabled'] and (options.get('merge_loras',False) or swap.get('use_non_blocking',False)
                               or swap.get('prefetch_blocks',0) or patcher.model['compile_args'] is not None):
            raise RuntimeError('Weight reuse currently requires unmergedLoRA,blocking,no prefetch,no compile')
        state={'reuse':cfg['enabled'],'cpu_views':{},'restores':[],'forward_calls':0,'transformer':patcher.model.diffusion_model}
        token=ACTIVE.set(state);started=time.perf_counter();success=False;failure=None
        try:
            result=original_sampler(self,*args,**kwargs);success=True;return result
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc);raise
        finally:
            state['cpu_views'].clear();ACTIVE.reset(token)
            evidence={'job_tag':cfg['job_tag'],'success':success,'error':failure,'reuse_cpu_weights':cfg['enabled'],
                'forward_calls':state['forward_calls'],'restore_events':state['restores'],
                'immutable_parameter_payload_bytes_reused':sum(x['immutable_parameter_bytes_reused'] for x in state['restores']),
                'python_sampler_wall_seconds':time.perf_counter()-started,'timing_scope':'Python sampler span,not pureCUDA; use serverhistory for whole-graph timing',
                'hook_source_sha256':BUILD_SHA256,'helper_source_sha256':views.CODE_SHA256,
                'requested_steps':bound.arguments['steps'],'requested_cfg':bound.arguments['cfg'],'seed':bound.arguments['seed']}
            if success:dump(out,evidence)
            else:
                try:dump(out,evidence)
                except OSError:pass # retain the original model exception
    model.WanAttentionBlock.to=block_to
    model.WanModel.forward=forward
    sampler.WanVideoSampler.process=sample
    INSTALLED=True

class CreatorWanS2VSettings:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'model':('WANVIDEOMODEL',),'reuse_cpu_weights':('BOOLEAN',{'default':True}),
             'job_tag':('STRING',{'default':'shot-attempt-001'}),'evidence_dir':('STRING',{'default':''})}}
    RETURN_TYPES=('WANVIDEOMODEL',)
    FUNCTION='configure'
    CATEGORY='Creator/WanS2V'
    def configure(self,model,reuse_cpu_weights,job_tag,evidence_dir):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',job_tag):raise ValueError('Invalid unique job tag')
        path=Path(evidence_dir)
        if not path.is_absolute():raise ValueError('Use an explicit absolute evidence directory')
        path=path.resolve();path.mkdir(parents=True,exist_ok=True)
        install_hooks()
        cfg={'enabled':reuse_cpu_weights,'job_tag':job_tag,'evidence_dir':str(path)}
        dump(path/(job_tag+'-config.json'),{**cfg,'utc':datetime.now(timezone.utc).isoformat(),
             'hook_source_sha256':BUILD_SHA256,'helper_source_sha256':views.CODE_SHA256})
        result=model.clone()
        result.model_options.setdefault('transformer_options',{})['creator_s2v_reuse']=cfg
        return (result,)

class CreatorWanLoadText:
    @classmethod
    def INPUT_TYPES(cls):return {'required':{'path':('STRING',{'default':''}),'expected_sha256':('STRING',{'default':''})}}
    RETURN_TYPES=('WANVIDEOTEXTEMBEDS',)
    FUNCTION='load'
    CATEGORY='Creator/WanS2V'
    def load(self,path,expected_sha256):
        p=Path(path)
        if not p.is_absolute() or p.suffix!='.safetensors' or not re.fullmatch('[a-f0-9]{64}',expected_sha256):raise ValueError('Explicit local text cache and SHA required')
        with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected_sha256:raise ValueError('Text cache hash mismatch')
        data=load_file(str(p),device='cpu')
        return ({'prompt_embeds':data['positive'],'negative_prompt_embeds':data['negative']},)

NODE_CLASS_MAPPINGS={'CreatorWanS2VSettings':CreatorWanS2VSettings,'CreatorWanLoadText':CreatorWanLoadText}
