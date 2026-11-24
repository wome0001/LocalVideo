"""Inference-only immutable CPU parameter views; mutable buffers use original .to."""
import torch
import hashlib
from pathlib import Path
CODE_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def device_only(args,kwargs):
    if len(args)!=1 or set(kwargs)-{'non_blocking'} or kwargs.get('non_blocking',False):return None
    if not isinstance(args[0],(str,torch.device)):return None
    target=torch.device(args[0])
    return target if target.type in ['cpu','cuda'] else None

def capture(module):
    if torch.is_grad_enabled() or module.training:raise RuntimeError('CPU weight view reuse is inference/eval only')
    rows=[]
    for name,param in module.named_parameters():
        if param.device.type!='cpu' or param.grad is not None:raise RuntimeError('Capture only original CPU parameters without gradients')
        value=param.data
        rows.append((name,param,value,tuple(value.shape),value.dtype,value.data_ptr()))
    if not rows:raise RuntimeError('No CPU block weights to reuse')
    return rows

def validate_cpu(module,rows):
    current=dict(module.named_parameters())
    if set(current)!=set(x[0] for x in rows):raise RuntimeError('Block parameter structure changed')
    for name,param,value,shape,dtype,ptr in rows:
        if current[name] is not param or value.device.type!='cpu' or value.data_ptr()!=ptr:
            raise RuntimeError('Original CPU parameter identity changed')
        if tuple(current[name].shape)!=shape or current[name].dtype!=dtype:
            raise RuntimeError('Parameter shape or dtype changed')

def restore(module,rows):
    if torch.is_grad_enabled() or module.training:raise RuntimeError('Never restore CPU views during training')
    validate_cpu(module,rows) # validate all entries before changing any parameter
    if any(param.device.type!='cuda' for _,param,*_ in rows):raise RuntimeError('Expected onloaded CUDA block')
    torch.cuda.synchronize() # complete all reads before releasing original GPU storage
    total=0
    for name,param,value,shape,dtype,ptr in rows:
        param.data=value
        if param.data_ptr()!=ptr:raise RuntimeError('CPU storage alias restore failed')
        total+=value.numel()*value.element_size()
    # Caller still invokes original module.to(cpu) so buffers/LoRA scheduling state are preserved.
    return {'parameter_count':len(rows),'immutable_parameter_bytes_reused':total,'mutable_buffers_use_original_to':True}
