# Blender：不依赖视频大模型的可控路线

Blender官方安装/渲染资料：[命令行渲染](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html)、[GPU渲染](https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html)。使用自己建模/合法授权资产、骨骼/表情/动作和灯光运镜。脚本可精确控制物理接触、道具状态与相机，但创建像真人的角色仍需高质量资产和动画制作。

```bash
blender --background --python tools/blender_product.py -- --output /your/media/product --engine EEVEE --seconds 5 --height 480 --render
ffmpeg -framerate 24 -i /your/media/product/frame_%04d.png -c:v libx264 -pix_fmt yuv420p /your/media/product.mp4
```

`--engine CYCLES --device GPU` 请求本地OptiX/CUDA；若设备不可用明确失败，不静默回落后声称GPU。CPU可显式 `--device CPU`。Eevee由图形后端加速，不能把Cycles的CPU/GPU开关直接套给Eevee。

示例只建立程序化玻璃瓶、桌面、灯光和相机缓动，所有素材由代码生成，无私人原型/作品。可先加 `--still` 出一张832×480参考，再喂自己选择的I2V模型；产品图不能检验人脸/嘴型。长期项目先锁镜头、资产和连续性，避免只追求“脚本可控”却忽略表演与身份。
