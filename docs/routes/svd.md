# SVD-XT：无对白的短图生视频

使用 [官方SVD-XT模型卡](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt)，确认许可。XT1.1可能要求Hugging Face授权；没有权限时不通过第三方镜像绕开。以下只对应已测XT。

单独Python环境安装 `torch==2.7.1` 对应CUDA构建、`diffusers==0.35.2`、transformers、accelerate、safetensors、Pillow、imageio和imageio-ffmpeg；按model card下载完整fp16目录。精确依赖随上游支持，先做导入检查，不覆盖Wan环境。

```bash
/your/svd-python tools/svd_generate.py --model /your/models/svd-xt --image /your/inputs/reviewed-1024x576.png --output /your/media/svd-seed45.mp4 --seed 45
```

代码固定25帧、7fps、30步、CFG3、temporal decoder、CPU-offload和FFN chunk5；原生约3.571秒，无声音。参数来自历史两预定seed轻动作肖像实验。用第二个预定seed复测动作，不挑好片；保留拖影和身份变化失败。

时长可通过编辑拼接，不把循环/插帧说成更长原生推理。SVD不负责文本对白、精确嘴型、多人物复杂表演。历史并未证明比Wan快；医院人物入画动作失败。只有新镜头通过质量门槛才可选用。
