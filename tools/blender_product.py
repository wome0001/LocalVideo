"""Blender 4.5+ procedural product shot. No private assets or external model calls."""
import argparse,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--engine',choices=('CYCLES','EEVEE'),default='EEVEE');p.add_argument('--device',choices=('CPU','GPU'),default='GPU');p.add_argument('--seconds',type=float,default=5);p.add_argument('--height',type=int,default=480);p.add_argument('--render',action='store_true');p.add_argument('--still',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=a.output.expanduser().resolve()
if out.exists():raise FileExistsError('Use a new output directory')
out.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES' if a.engine=='CYCLES' else 'BLENDER_EEVEE_NEXT'
if a.engine=='CYCLES':
    scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.device=a.device
    if a.device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences
        found=False
        for backend in ('OPTIX','CUDA'):
            try:
                prefs.compute_device_type=backend;prefs.get_devices()
                for device in prefs.devices:device.use=device.type!='CPU'
                if any(d.use for d in prefs.devices):found=True;break
            except (TypeError,RuntimeError):continue
        if not found:raise RuntimeError('No supported GPU; explicitly choose --device CPU')
scene.render.resolution_x=round(a.height*832/480);scene.render.resolution_y=a.height;scene.render.resolution_percentage=100
scene.render.fps=24;scene.frame_start=1;scene.frame_end=round(a.seconds*24)
scene.world.color=(.04,.04,.04)
def material(name,color,metallic=0,roughness=.25,transmission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metallic;n.inputs['Roughness'].default_value=roughness;n.inputs['Transmission Weight'].default_value=transmission;n.inputs['IOR'].default_value=1.46;return m
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,1.1));bottle=bpy.context.object;bottle.scale=(.75,.43,1.1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel=bottle.modifiers.new('Rounded glass edges','BEVEL');bevel.width=.12;bevel.segments=5;bottle.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bottle.data.materials.append(material('Amber glass',(.55,.18,.035),roughness=.12,transmission=.85))
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.23,depth=.38,location=(0,0,2.36));bpy.context.object.data.materials.append(material('Cap',(.2,.16,.09),.85,.2))
bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.data.materials.append(material('Table',(.12,.14,.16),roughness=.3))
for location,power,size in (((-3,-4,6),1100,4),((3,1,4),1600,3),((0,4,5),800,2)):
    bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=62
for frame,loc in ((1,(4,-7,3.5)),(scene.frame_end,(3.1,-6.3,3.05))):
    camera.location=loc;camera.rotation_euler=(Vector((0,0,1.25))-camera.location).to_track_quat('-Z','Y').to_euler();camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_euler',frame=frame)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'product.blend'))
if a.render:
    if a.still:scene.frame_set(1);scene.render.filepath=str(out/'reference.png');bpy.ops.render.render(write_still=True)
    else:bpy.ops.render.render(animation=True)
