# Third-party software, models and reference material

MIT in this repository covers LocalVideo's original orchestration code, agent skills, templates and documentation. It does **not** relicense an upstream engine, weights, model outputs, fonts, voice or image rights. Engines/weights are downloaded separately. No upstream source tree, private media, model weights or third-party sample clips are bundled.

| Project | Role | Authoritative source and license |
|---|---|---|
| ComfyUI | Local workflow server | [Source / license](https://github.com/Comfy-Org/ComfyUI); use the license at the locked commit |
| Wan2.2 | S2V/I2V model family | [Official source](https://github.com/Wan-Video/Wan2.2), [S2V model card](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B) |
| WanVideoWrapper | ComfyUI nodes | [Kijai's source / license](https://github.com/kijai/ComfyUI-WanVideoWrapper) |
| FP8 model/LightX2V adapters | Historical low-memory profile | Exact model cards and file revisions in [models.json](configs/models.json); quantization/distillation is not a new ownership grant |
| CosyVoice | Local speech synthesis | [Official source](https://github.com/QwenAudio/CosyVoice), [CosyVoice2 model card](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) |
| FreeVideo / OpenVDN | Experimental H3 route | [FreeVideo](https://github.com/FlashML-org/FreeVideo), [VDN-H3 card](https://huggingface.co/OpenVDN/vdn-minimax-h3) |
| Stable Video Diffusion | Silent image-to-video | [SVD-XT model and license](https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt); gated access/terms may apply |
| LTX | Experimental audio/video route | [Official LTX-2](https://github.com/Lightricks/LTX-2); model generation/version/license must be checked separately |
| ContentV | Experimental silent text-to-video | [Official source](https://github.com/bytedance/ContentV) |
| LivePortrait | Portrait animation | [Official source](https://github.com/KwaiVGI/LivePortrait); check any external face-analysis model licenses too |
| MuseTalk / LatentSync | Optional local lip sync | [MuseTalk](https://github.com/TMElyralab/MuseTalk), [LatentSync](https://github.com/bytedance/LatentSync) |
| Blender / FFmpeg | Procedural scenes and assembly | [Blender license](https://www.blender.org/about/license/), [FFmpeg license](https://ffmpeg.org/legal.html); FFmpeg build options affect its license |
| 67.js / Node.js | Optional UI and scripted animation | [67.js](https://github.com/codepawl/67.js), [Node.js](https://nodejs.org/); exact npm package metadata is recorded in configs/67js-package.json |
| LibreOffice / PyMuPDF / Noto CJK | Optional slides and text rendering | Follow the official project licenses linked in docs/RESOURCES.md; no slides, rendered pages or fonts are bundled |
| PyTorch / Diffusers / NumPy / SciPy / SoundFile / aiohttp / psutil | Runtime dependencies | Each installed package retains its own license and notices |

Pinned installed-source references are recorded in [upstreams.lock.json](configs/upstreams.lock.json). They describe the historical implementation; newer `main` versions are not automatically equivalent. Model cards linked in the catalog are the place to check availability and permissions before use, especially for commercial projects.

The `CreatorWanS2VNodes` implementation is LocalVideo-authored glue and opt-in inference instrumentation; it calls upstream classes rather than redistributing their implementation. Its monkeypatches are version-dependent. Do not treat it as an upstream-endorsed patch.

FreeVideo inspired the **organization** of the project introduction (purpose, setup, requirements and limitations). Its branding, screenshots, examples and README text are not copied. No affiliation or endorsement is implied.
