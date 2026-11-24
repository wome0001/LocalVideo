# 从场景到成片：可重复执行的完整主线

## 一、定调、剧本和资产

写清风格、受众、最终规格、时长区间、画面/声音能否复用。剧情靠动作和人物对白推进；不要把小说原文逐段念出来。每场标目的、阻碍、转折和离场动作。

复制 [shot-list 模板](../examples/shots.template.json)、[对白计划](../examples/dialogue.plan.json) 到自己的项目资料目录。结构分镜保留镜头ID、角色/说话者/听者、场景状态、动作顺序、情绪、景别/运镜、对白、时长、参考ID及输入SHA。状态卡锁住发型/衣服/伤处/电话UI；反打、近景、手部、环境分别制作。先审核图片和代表镜头，不先生成整集。

参考图、授权声音和所有输出在自己的工作目录，**不要放进 Git**。本仓库没有任何原型或作品。可用 `tools/blender_product.py` 生成一个完全程序化的瓶子作为非人物试验输入；这只能验证技术链路，不能验证人脸/嘴型。

## 二、先完成对白

按 [DIALOGUE.md](DIALOGUE.md) 分句生成、分角色、混音、试听。通过后锁定最终WAV字节、词和气口。镜头窗口围绕批准音轨安排；护士/电话远端说话时，不能驱动画面里的听者嘴巴。不要用强制拉长声音来适配旧视频。

## 三、初始化 Wan 新任务

复制 [run-config](../examples/run-config.template.json)，把所有路径换成你的绝对路径。`project` 存源码/工作流/证据，`artifact_root` 存媒体，`work` 存服务临时数据，`hot` 存本次可丢弃模型热副本。四根必须全新、互不嵌套。`model_library` 是永久模型根；`comfy_root`、`comfy_python`、`plugin_root` 是你安装的环境和额外节点目录。

```bash
localvideo wan-init /your/metadata/config.json --install-plugin
```

初始化仅创建文件，不启动GPU、不下载模型。安装插件只新增缺失文件；遇到不同版本不覆盖。`validation_only=true` 是只做准备的隔离模式：生成的运行器禁止 stage/launch/run/stop。真正生成要在**另一个新任务**使用 false。

## 四、生成提示词缓存和源锁

准备自己写的正/负提示纯文本。`encode-text` 必须用 Comfy 的 Python 环境，可直接调用工具文件：

```bash
/your/comfy-python tools/encode_wan_text.py --comfy-root /your/tools/ComfyUI --encoder /your/models/wan22/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --prompt /your/inputs/positive.txt --negative /your/inputs/negative.txt --output /your/media/text.safetensors
python tools/lock_inputs.py /your/metadata/shots.template.json --output /your/metadata/shots.locked.json
localvideo wan-build /your/project/run-config.json /your/metadata/shots.locked.json
```

Windows 对完整 Python 路径用 `& 'F:/your/env/Scripts/python.exe' tools/encode_wan_text.py ...`。`lock_inputs` 将模板的 `AUTO` SHA 替换为实读哈希，路径相对模板解析；既有SHA不匹配会拒绝。图片明确裁成832×480并审核，不隐式裁脸。音频是该镜头已批准片段，留合适前后静默 handles。原生输出帧数受窗口/音频/版本影响，模板的 `expected_frames` 只是代表 profile 的预期；首镜必须实测，再冻结该项目规格，不从最终剪辑时长推断采样帧数。

## 五、按单GPU队列运行

以下运行器命令都用 **Comfy 环境 Python**；`run-config.json` 给出的 `comfy_python` 也应是同一环境。

```bash
/your/comfy-python /your/project/src/runtime.py stage --kind s2v
/your/comfy-python /your/project/src/runtime.py launch
/your/comfy-python /your/project/src/runtime.py run --id shot01-v1 --graph /your/project/workflows/shot01-v1.json --free
```

`stage` 逐项核永久模型SHA，复制到独立hot目录并读回；保留18GiB余量，不编辑分页。`launch` 使用 loopback 服务和隔离 input/output，不碰现有 Comfy 根配置。`run` 记录 prompt_id、真实 sampler 步骤、执行/缓存节点、内存/GPU采样和完整 history，轮询到成功/失败，再校验实际输出。提交成功不是完成。超时先查同一 prompt_id，不重复提交；必要时读停止标记，核服务状态后再建新attempt。

默认 `reuse_cpu_weights=false`，4步LCM/匹配LoRA为历史profile。要比较 CPU 权重复用优化，把同一锁定镜头只改此字段，分别出新attempt；保持模型/输入/seed/精度/步数/帧数一致。静态缓存可复用；Sampler命中缓存不算新推理。`--free` 用于冷/暖定义明确的对照，批内缓存策略必须单列。

## 六、审核、复用与剪辑

每镜技术完整性、动作顺序、脸/手/手机、静听闭口、跨镜一致、音画/自然度分别审。失败只重做对应镜头。需要新嘴型/脸型时不能套用旧口部修复坐标；只有完整RGB和PTS等价才能继承已审后处理。

复制 [edit-plan](../examples/edit-plan.template.json)，锁视频/音频/字幕SHA，给明确 `frames/fps`、视频trim和音频区间。`roots` 声明你自己的媒体/元数据/临时根，各目标必须位于对应根内。

```bash
localvideo compose /your/metadata/edit-plan.json
python skills/wan22-s2v-local-production/scripts/compare_native.py /your/baseline.mp4 /your/optimized.mp4 --expected-frames 81 --evidence /your/metadata/comparison
```

合成验证音频源区间真实存在、帧数和PCM覆盖；先用FFV1/PCM中间件，最后一次H264/AAC编码。AAC是有损的，尾填充单列；不会把源声音拉伸/补齐后冒充批准版。SRT由最终对白时间换算，字幕渲染字体按平台安装。没有听觉/实时播放能力时不能只凭哈希宣称自然度通过。

## 七、交付、停止和归档

交付MP4、SRT/音轨、源锁/分镜、模型/版本与代码、计时、选用/拒绝take、独立审核结论和限制。先审核再按授权发布。

```bash
/your/comfy-python /your/project/src/runtime.py stop
```

只停止出生时间/命令行匹配且无队列任务的本次服务。永久模型不能删。公开包**不提供任意目录递归清理器**；缓存释放先停进程、核永久原件与SHA，按清单清本任务热副本。单盘多目录和符号链接不算备份，见 [存储说明](STORAGE.md)。
