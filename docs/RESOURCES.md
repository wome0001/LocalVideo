# 全部资源下载、安装与配置索引

先选路线，只下载该路线资源。表中“历史锁”用于复现实验版本，“上游安装”由该版本官方工具解析其依赖；不承诺替代工具的一键全自动安装。所有素材/权重在仓库外保存，不要提交到fork。

**空间规划先看[每模型占用表](MODEL_STORAGE.md)**：包含权重/编码器/VAE/LoRA、完整快照和共享/准备缓存的分组；未冻结的可选型号明确标未验证。不要把磁盘GiB与显存GiB混淆。

## A. 基础软件（所有路线）

|资源|官方下载地址|安装与配置|验证|
|---|---|---|---|
|Python 3.11+；历史3.12.10|[发行下载](https://www.python.org/downloads/)、[3.12.10文件](https://www.python.org/ftp/python/3.12.10/)|安装到自选tools目录；`python -m venv 路径`，不要复用系统环境|`python --version`|
|Git|[下载](https://git-scm.com/downloads)|安装并加入PATH；不需GitHub令牌即可clone公开代码|`git --version`|
|FFmpeg/ffprobe|[官方入口](https://ffmpeg.org/download.html)、[Windows Gyan构建](https://www.gyan.dev/ffmpeg/builds/)|解压含libx264/libass构建，bin加入PATH，或设LOCALVIDEO_FFMPEG/LOCALVIDEO_FFPROBE；Ubuntu `sudo apt-get install ffmpeg`|`localvideo doctor`、`ffmpeg -filters`含subtitles|
|中文字体|[Noto CJK官方发行](https://github.com/notofonts/noto-cjk/releases)|安装Noto Sans CJK；Windows亦可用系统已许可字体；Linux刷新fontconfig|`fc-match 'Noto Sans CJK SC'`或实际字幕烟测|
|LocalVideo核心依赖|[pyproject.toml](../pyproject.toml)|克隆根执行`python -m pip install -e .`；只装numpy/scipy/soundfile/aiohttp/psutil，不偷偷装模型|`python -m unittest discover -s tests -v`|
|NVIDIA驱动|[NVIDIA官方](https://www.nvidia.com/Download/index.aspx)|按自己显卡/系统安装；此仓库不静默改驱动、HAGS或分页|`nvidia-smi`|
|GPU PyTorch/CUDA运行时|[PyTorch官方安装选择器](https://pytorch.org/get-started/locally/)、[历史版本](https://pytorch.org/get-started/previous-versions/)|独立GPU venv；历史torch2.7.1/torchvision0.22.1/torchaudio2.7.1的cu128构建：`python -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128`|`python -c "import torch; print(torch.__version__,torch.cuda.is_available())"`|

安装来源的license/架构/校验以其官方发行页为准；FFmpeg/字体和GPU运行时是独立资源，不由LocalVideo的MIT覆盖。

## B. Wan2.2-S2V 主线：软件与五个精确模型文件

|资源|下载|位置/安装|
|---|---|---|
|ComfyUI源码|[官方](https://github.com/Comfy-Org/ComfyUI)，commit `c5751c81abe131202eea9e4c66d000589013dd0b`|`python tools/install_upstreams.py --name ComfyUI --destination 你的Comfy目录`，在其独立venv安装requirements|
|WanVideoWrapper|[官方](https://github.com/kijai/ComfyUI-WanVideoWrapper)，commit `a7439db30bed0c5b5fa437d77ae8a7bb220dfd00`|安装到Comfy/custom_nodes/ComfyUI-WanVideoWrapper，`install_upstreams.py --name WanVideoWrapper`，同venv装requirements|
|LocalVideo自有节点|本仓库`skills/wan22-s2v-local-production/assets/CreatorWanS2VNodes`|`localvideo wan-init 配置 --install-plugin`新装到配置plugin_root；不同版本不覆盖|
|SageAttention|[官方源码/发布](https://github.com/thu-ml/SageAttention)、[Windows构建项目](https://github.com/woct0rdho/SageAttention)|先匹配Python/torch/CUDA/平台再安装wheel；历史ABI `2.2.0+cu128torch2.7.1.post3`。没有相同合法构建就从上游build或更换attention并重新验证，不从不明网盘取wheel|
|Triton|[官方](https://github.com/triton-lang/triton)、[Windows发行](https://github.com/woct0rdho/triton-windows/releases)|历史Windows `triton-windows==3.3.1.post21`；Linux按匹配torch依赖安装，不在两个平台混装|

五个权重/VAE/编码器/LoRA的**可直接下载URL、固定HF revision、字节数和完整SHA**见 [configs/models.json](../configs/models.json)。其中：

|角色|本地相对路径|来源|
|---|---|---|
|S2V scaledFP8主模型|diffusion_models/Wan2_2-S2V-14B_fp8_e4m3fn_scaled_KJ.safetensors|Kijai/WanVideo_comfy_fp8_scaled|
|音频编码器|audio_encoders/wav2vec2_large_english_fp16.safetensors|Comfy-Org/Wan_2.2_ComfyUI_Repackaged|
|VAE FP32|vae/Wan2.1_VAE_official_fp32.pth|Wan-AI/Wan2.2-S2V-14B（源文件Wan2.1_VAE.pth，工具按catalog保存别名）|
|匹配蒸馏LoRA|loras/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors|Kijai/WanVideo_comfy|
|文本编码器|text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors|Comfy-Org/Wan_2.1_ComfyUI_repackaged|

`localvideo models --library 你的永久模型根 --download` 下载并SHA读回。随后run-config的model_library指同一根，脚本生成extra-model-paths，stage只复制已验证原件。模型约25GB；另备热副本和临时空间。text cache是你按提示生成的产物，不从别人的人物缓存下载。

## C. 本地多角色对白

|资源|下载|安装/配置|
|---|---|---|
|CosyVoice源码|[官方](https://github.com/QwenAudio/CosyVoice)，历史commit `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`|`tools/install_upstreams.py --name CosyVoice --destination 你的目录`；递归子模块，独立venv装requirements|
|Matcha-TTS子模块|由CosyVoice锁定提交的.gitmodules定位|`git submodule update --init --recursive`；工具自动加入third_party/Matcha-TTS路径|
|CosyVoice2-0.5B完整模型|[HF下载树](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B/tree/main)、[ModelScope官方镜像](https://www.modelscope.cn/models/iic/CosyVoice2-0.5B)|完整snapshot_download到自己的models目录；锁所选revision并保存全目录SHA，勿漏tokenizer/frontend文件；DIALOGUE给出命令|
|SoundFile/libsndfile等音频依赖|[SoundFile](https://pypi.org/project/soundfile/)、CosyVoice requirements|pip装核心/引擎依赖；Linux按需装libsndfile与sox；参考WAV可通过SoundFile本地读取，避免隐式TorchCodec下载|
|参考声音|**自备授权录音，不公开下载私有声线**|单说话人5–15秒、无音乐/混响、精确转录；自行确认授权后填voices.template，lock_inputs计算SHA|
|可选ASR|[whisper.cpp](https://github.com/ggml-org/whisper.cpp)、[模型列表/下载脚本](https://github.com/ggml-org/whisper.cpp/tree/master/models)|按上游构建/发行安装，下载所选多语模型如base/small；只辅助掉字检查，不替代人耳|

此模块的自然度依赖你自己授权的声音和表演稿，无法下载私人听审版本原样重现。参考录音不满足条件应重新录，不去抓取他人声音。

## D. 其它视频路线（按需，不是主线必装）

|路线/资源|下载入口|安装配置与限制|
|---|---|---|
|FreeVideo源码/安装器|[官方仓库及Releases](https://github.com/FlashML-org/FreeVideo/releases)、[历史源锁](../configs/upstreams.lock.json)|Windows按官方安装器选择独立Comfy；Linux按官方setup.sh；已有Comfy按其custom-node步骤。不要把核心venv当作FreeVideo运行时|
|H3基础模型|[OpenVDN/vdn-minimax-h3](https://huggingface.co/OpenVDN/vdn-minimax-h3)，历史revision `751739ee5b9e3ac802dca5d5111075fdaeb47885`|交由匹配FreeVideo设置下载/准备base、视频/audio VAE、scheduler与采样缓存，保留布局|
|H3 int8 edge权重|[OpenVDN/vdn-minimax-h3-edge](https://huggingface.co/OpenVDN/vdn-minimax-h3-edge)，历史revision `da37681f5a1f7015fdb63482142b865111b687d3`|历史int8-convrot/cache方案，不与其它准备格式混称同配置|
|H3 NVFP4文本编码器|[t8star/Vdn-Minimax-H3-Comfy](https://huggingface.co/t8star/Vdn-Minimax-H3-Comfy/tree/d6aa5dfc669a749dc9364a36f3b6d4d1545a53e8/text_encoders)|qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors，配置在FreeVideo Settings；其格式/硬件支持由上游环境处理|
|H3二采latent upscaler|[LBH-123-AI模型](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler/tree/3f941d5d182014dd5c0a5e16330420ee2d4aa0c6)|选择3d_conv_v1_fp16，按FreeVideo模型设置安装，不把无低清首采的配置叫二采提速|
|SVD-XT|[官方完整下载树](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/tree/main)|完整fp16 snapshot；参考文件版本/SHA见optional-models.json，独立Diffusers环境；路线仅静音短片|
|SVD-XT1.1|[官方授权入口](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt-1-1)|需许可/本机登录时自行完成；本仓库未测试该版本，不绕过401|
|LTX-2.3模型/文本编码器|[Comfy官方安装例](https://docs.comfy.org/tutorials/video/ltx/ltx-2-3)、[固定下载文件](../configs/optional-models.json)|表内有历史具体文件/URL/commit/SHA；根据对应版本放到diffusion_models/text_encoders等。不是当前所有LTX型号的锁文件|
|ContentV-8B|[官方代码](https://github.com/bytedance/ContentV)、[HF模型](https://huggingface.co/ByteDance/ContentV-8B/tree/40c0e022a2b997448a6a7f89c67df735b540e3e6)|独立venv按官方requirements/demo；全量snapshot；仅T2V，不提供伪造I2V/声音参数|
|LivePortrait|[源码/安装与模型清单](https://github.com/KwaiVGI/LivePortrait)|按其README准备pretrained_weights及人脸分析依赖，检查额外许可证，再短样复核身份|
|MuseTalk1.5|[源码/安装与权重清单](https://github.com/TMElyralab/MuseTalk)|独立环境，按官方models目录下载UNet/VAE/Whisper/人脸检测等完整依赖，参见portrait/freevideo路线|
|LatentSync1.6|[源码/安装与模型](https://github.com/bytedance/LatentSync)|按对应版本安装、下载UNet/Whisper，配置音频/裁脸/时间窗口；不默认任意分辨率都能保持身份|
|Stable Diffusion Forge|[官方仓库](https://github.com/lllyasviel/stable-diffusion-webui-forge)|按上游包/venv准备自己的合法基础模型，适合图像/重绘；不把图像稳定等同视频表演通过|
|AnimateDiff|[官方](https://github.com/guoyww/AnimateDiff)|按README装运动模块、基础模型/配置；只列可选研究方向，未在此仓库验证生产质量|

## E. 脚本渲染、UI、课件和音乐

|资源|下载入口|安装配置|
|---|---|---|
|Blender 4.5系列|[官方](https://www.blender.org/download/)、[历史版本目录](https://download.blender.org/release/Blender4.5/)|解压或安装到自选tools；命令行可用blender，Cycles按设备选OptiX/CUDA/CPU；Eevee独立配置|
|67.js|[源码](https://github.com/codepawl/67.js)、[官方文档](https://67js.codepawl.com)、[npm](https://www.npmjs.com/package/@codepawlhq/67js)|Node独立项目：历史依赖`npm install @codepawlhq/67js@0.19.0`；按文档构建动画，版本API可能变更；不承诺其能替代真人表演|
|Node.js|[官方](https://nodejs.org/en/download)|仅UI脚本/67.js需要，安装LTS并核node/npm，勿把用户token放进npm项目|
|LibreOffice课件转换|[官方下载](https://www.libreoffice.org/download/download-libreoffice/)|headless导PDF→按页渲染→本地TTS解释→FFmpeg，详见slides-ui路线；自备有权使用的PPT|
|PDF页渲染|[PyMuPDF文档](https://pymupdf.readthedocs.io/en/latest/installation.html)|独立环境pip安装PyMuPDF，按其许可使用；不随仓库转发课件图片|
|ACE-Step / Stable Audio Tools|[ACE-Step](https://github.com/ace-step/ACE-Step)、[Stable Audio Tools](https://github.com/Stability-AI/stable-audio-tools)|照对应版本安装与下载模型卡中的开放权重，先短段；某个云端Stable Audio型号不等于有本地权重|
|GPT-SoVITS / DiffSinger / DiffRhythm|[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)、[DiffSinger](https://github.com/openvpi/DiffSinger)、[DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)|各自独立环境、按README模型/声库/词音配置；未提供私人歌声；适用能力与显存见music路线|

## F. 仍需用户提供的资源

人像/角色参考、克隆声线、剧本、已审对白和作品不提供下载地址，这是公开范围的明确限制。可用自己的授权照片/录音，或用本仓库Blender程序化产品图进行非人物链路试验。没有参考授权就不能完整复现同一个人；这里不提供所谓“替代私有素材”的下载绕过方式。

每个资源保存下载来源、实际revision、许可、大小与SHA；缺项则写未验证。官方下架、鉴权/许可未获批或ABI无可用构建时，记录阻塞，不把另一个同名资源当成相同字节。所有流程边界见 REPRODUCIBILITY。
