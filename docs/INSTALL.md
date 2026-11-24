# 安装：先验证小工具，再选择独立模型环境

## 1. 核心工具（不安装模型）

需要 Python 3.11+、Git、带 `libx264`/`aac`/`subtitles` 的 FFmpeg 和 ffprobe。字幕渲染需要 libass；Linux 建议安装 Noto CJK 字体。本项目通过源码克隆和 editable 安装运行，不发布独立安装包。

```bash
git clone https://github.com/wome0001/LocalVideo.git
cd LocalVideo
python -m venv /your/tools/localvideo-core
# Linux/macOS
source /your/tools/localvideo-core/bin/activate
# Windows PowerShell：& 'F:/your-tools/localvideo-core/Scripts/Activate.ps1'
python -m pip install -e .
localvideo doctor
localvideo demo --work /your/work/localvideo-smoke-001
```

上面的 `/your/...` 是你要替换的绝对路径。PowerShell 的新路径示例：`localvideo demo --work F:/Creator/localvideo-smoke-001`。工具不依赖这些盘符。`doctor` 仅查询；`demo` 是5秒测试卡和测试音，验证80帧、音频覆盖、字幕和合成，**不是 AI 人物/对白质量演示**。演示文件只在你给出的新目录生成。

非 PATH 工具可设 `LOCALVIDEO_FFMPEG`、`LOCALVIDEO_FFPROBE` 为可执行文件的完整路径；Windows 用 `$env:LOCALVIDEO_FFMPEG='F:/your-tools/ffmpeg.exe'`，bash 用 `export LOCALVIDEO_FFMPEG=/your/tools/ffmpeg`。

如果本机 `venv/ensurepip` 初始化阻塞，可用 [uv官方安装](https://docs.astral.sh/uv/getting-started/installation/) 后新建**另一个**干净环境：`uv venv /your/tools/localvideo-core`，`uv pip install --python /your/tools/localvideo-core/bin/python -e .`。Windows解释器路径是 `Scripts/python.exe`。保留失败目录/日志，不能把未安装成功写成通过。uv与pip安装的是同一pyproject，后续CLI/测试不变。

## 2. Wan GPU 环境

不要把所有模型塞进一个 Python 环境。Wan/ComfyUI、CosyVoice、SVD 各自建 venv；LTX/FreeVideo 按各自上游环境安装。RTX 5060 Ti 16GB 是历史测试卡，非所有路线的最低要求。CPU-only 核心烟测不需要 CUDA。

先安装适合自己 GPU 的 [官方 PyTorch](https://pytorch.org/get-started/locally/)。历史 Blackwell 路线使用 cu128 / torch2.7.1 ABI 的 SageAttention 组合；不把 CUDA13/NVFP4、`--force-fp16` 或某个 Sage wheel 当成普适提速开关。核 `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`。自行选择版本时，记录它并重新做小样验收。

源码安装使用锁文件中的精确 commit，下面的 `COMMIT_FROM_LOCK` 必须替换为对应40位提交：

```bash
git clone https://github.com/Comfy-Org/ComfyUI.git /your/tools/ComfyUI
git -C /your/tools/ComfyUI checkout COMMIT_FROM_LOCK
python -m pip install -r /your/tools/ComfyUI/requirements.txt
git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git /your/tools/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper
git -C /your/tools/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper checkout WRAPPER_COMMIT_FROM_LOCK
python -m pip install -r /your/tools/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/requirements.txt
python -m pip install aiohttp psutil safetensors
```

运行这些 pip 命令时，应已激活 **Comfy 环境**。精确 commit 在 [upstreams.lock.json](../configs/upstreams.lock.json)，可用 `python tools/install_upstreams.py --name ComfyUI --destination /your/tools/ComfyUI` 自动完成 clone+checkout（目标必须新建），Wrapper 同理 `--name WanVideoWrapper`。依赖由上游 requirements 管理；更换依赖不是已验证性能的自动继承。

SageAttention 需要匹配操作系统、torch/CUDA/Python。没有兼容版本时，修改模板 `attention_mode` 为节点支持的 SDPA 模式并另存新 profile，不能仍称同条件速度复现。Windows 实测组合见 [性能记录](PERFORMANCE.md)。不用全局关分页/HAGS或强改驱动来完成安装。

## 3. 下载并核模型

```bash
localvideo models --library /your/models/wan22
localvideo models --library /your/models/wan22 --download
```

第一条仅检查，第二条会下载约25GB的五个文件。目录需要容纳下载与热副本的额外空间。URL 固定文件版本，SHA/字节数来自历史已核原件；每个下载文件读回SHA通过才写 `.verified.json`。网络/许可问题保留失败，不绕过 gated 模型授权；工具不读取或上传令牌。已有相同字节模型可以放到清单规定相对路径后核验。冲突/损坏文件不会被覆盖，先人工检查并另存失败副本。

## 4. 下一步

按 [完整执行流程](WORKFLOW.md) 建新任务、编码提示词、锁素材、出单镜头，再合成。CosyVoice2 安装与角色声线见 [对白指南](DIALOGUE.md)。本仓库不替你获取人物/声音授权，也不下载他人声线。
