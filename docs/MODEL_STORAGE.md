# 模型磁盘占用与部署空间

以下为2026-11-24的固定文件元数据或已装模型目录**只读逻辑长度**。GiB=2^30字节，GB=10^9字节；不是显存、内存或文件系统簇实际占用。完整数值在configs/model-storage.json，来源URL/SHA在models.json/optional-models.json和RESOURCES。

|模型或组件|文件数|GiB|逻辑字节|统计口径|
|---|---:|---:|---:|---|
|Wan component: diffusion_models/Wan2_2-S2V-14B_fp8_e4m3fn_scaled_KJ.safetensors|1|15.510|16653330620|Exact downloadable file SHA/bytes in models.json|
|Wan component: audio_encoders/wav2vec2_large_english_fp16.safetensors|1|0.588|630997322|Exact downloadable file SHA/bytes in models.json|
|Wan component: vae/Wan2.1_VAE_official_fp32.pth|1|0.473|507609880|Exact downloadable file SHA/bytes in models.json|
|Wan component: loras/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors|1|0.587|630697104|Exact downloadable file SHA/bytes in models.json|
|Wan component: text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors|1|6.273|6735906897|Exact downloadable file SHA/bytes in models.json|
|Wan2.2-S2V complete five-file profile|5|23.431|25158541823|Includes shared VAE, UMT5, audio encoder and LoRA; permanent original only, excludes hot copy/output|
|Wan S2V four-file staged hot set|4|17.157|18422634926|Additional to permanent library when stage copies models; text encoding is a separate process; plus 18GiB free headroom required by runtime|
|LTX-2.3 historical download set|2|36.303|38979586280|Exact selected file metadata; excludes runtime/output/cache and other model versions|
|SVD-XT historical fp16 directory|11|4.200|4509208849|Selected exact model snapshot files; excludes optional spatial VAE|
|SVD optional spatial VAE|2|0.312|334643823|Optional historical decode comparison; not needed by default svd_generate.py|
|FreeVideo stored h3-base|15|10.264|11021193831|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo stored stage-dmd-step-250|5|0.000|49312|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo stored encoder|1|14.610|15687142551|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo stored latent_upscaler|1|0.643|690592672|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo stored sampling-cache|100|0.135|145220800|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo stored prepared|278|21.355|22929329625|Historical stored pool; prepared includes multiple representations, not the minimum single-run requirement|
|FreeVideo whole historical model/cache pool|401|47.007|50473546395|Includes original and prepared formats; not a required minimum, installer may reuse/select a subset|
|ContentV-8B complete snapshot|30|25.880|27788913196|Official snapshot metadata at 40c0e022a2b997448a6a7f89c67df735b540e3e6; model weights and repo side files|
|CosyVoice2-0.5B installed model directory|22|5.230|5616074425|Read-only installed-directory measurement; excludes engine/venv/voice references; skipped aliases=0|
|MuseTalk observed model-resource directory|13|6.293|6757304142|Installed bundle observation, not minimum required space; exact full version set not locked. Weight-only GiB=3.619|
|GPT-SoVITS observed model-resource directory|9|1.026|1101658571|Installed bundle observation, not minimum required space; exact full version set not locked. Weight-only GiB=1.026|
|LatentSync-1.6 observed model-resource directory|6|5.106|5482439039|Installed bundle observation, not minimum required space; exact full version set not locked. Weight-only GiB=5.106|

## 需要另外预留什么

- 永久原件和完整热副本会使模型磁盘需求接近两份；五文件Wan profile并非只需要主模型那一行的空间。模板stage还保留18GiB余量。
- Hugging Face下载缓存、断点/失败下载、准备格式、torch/venv/Sage/Triton编译缓存和视频/latent输出另计。下载器是否复用同一物理文件由版本决定，不能默认不占空间。
- FreeVideo stored pool包括原权重、准备后的多种表示、采样缓存，不是每位用户必须下载的最小集合。使用官方安装器按目标GPU选择；不要把完整库总量与单次运行所选文件相混。
- 模型共用的VAE/编码器只计一份；组件行和含组件的total行相互重叠，不应相加。
- 显存需求随帧数/尺寸/精度/attention/offload变化，历史16GB卡上的成功不意味着每行模型都只要16GB。先做短样，再测峰值。

## 未测量的可选工具

LivePortrait、MuseTalk、LatentSync、Forge基础模型、AnimateDiff模块、ACE-Step、Stable Audio Tools、GPT-SoVITS、DiffSinger声库、DiffRhythm：本次未冻结其完整可下载权重集合，因此磁盘总量标为**未验证**，不填网上估算值；实际大小依模型/声库版本而异。下载入口和配置在RESOURCES对应行。仅评估过或安装了工具，不代表已经下载某个型号。

下载自己的版本后，可运行 `python tools/measure_models.py --root 你的模型目录` 测大小，保存输出与实际revision/模型SHA。再计共享组件、下载缓存与热副本。软件/模型随时间会变化，这张表不替代下载前核所选版本文件清单。
