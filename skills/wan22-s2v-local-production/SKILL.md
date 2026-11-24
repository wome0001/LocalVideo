---
name: wan22-s2v-local-production
description: Execute local Wan2.2-S2V shots through pinned ComfyUI, locked references, asynchronous jobs, real sampler telemetry, editing and quality checks. Dialogue direction and casting use scene-dialogue.
---

# Wan2.2-S2V 执行

先核当前项目配置、已审输入和版本。此技能随附 scripts、assets/API模板和可选CPU权重复用节点；GPU环境/模型须先按 LocalVideo 的 INSTALL/RESOURCES 安装，不能直接拿本机旧路径运行。

1. `scripts/prepare_run.py config.json` 建四个不重叠的新根：project元数据、artifact_root媒体、work临时、hot热副本。环境字段有model_library/comfy_root/comfy_python/plugin_root/ffmpeg/ffprobe/port。只有显式 `--install-plugin` 新增同版本节点，不覆盖异版。validation_only禁止任何GPU动作。
2. 通过锁文件准备图片/音频/text_cache，每项path+SHA。图明确832×480，声音按批准版安排前后handles。`scripts/build_shots.py run-config.json shots.locked.json` 生成单窗口API图；预期帧数必须实际核，不把剪辑时长当采样长度。
3. 用配置中的Comfy Python运行生成的runtime.py：stage→launch→run，保存task_id/history/真实Sampler步数/缓存命中和telemetry。超时先查原任务，绝不重复提交当重试。每attempt新ID、证据不覆盖。
4. 模板是历史4步LCM/匹配LightX2V、scaledFP8、16fps的S2V组合，不是通用I2V/双专家模板。CPU权重复用默认关闭，只在锁定Wrapper版本/推理eval/blocking/未合并LoRA/无编译预取组合做对照；可变buffer走原方法。
5. `scripts/compare_native.py` 完整RGB/PTS核等价，不能证明听感/身份。新角度、脸型、裁切或时钟变化不得复用旧口部mask和修复链。
6. `scripts/compose_from_plan.py` 按明确视频滤镜、frames/fps和批准音轨窗口合成。roots约束三个输出根，实际PCM覆盖不足拒绝；不拉伸或悄悄补齐声音。
7. 停止只处理出生时间/命令行归属本次且队列空的服务。无通用递归清理；先核永久原件和授权再逐项清热副本。

对白必用 `scene-dialogue`。先代表小样独审，按项目要求人审后扩批。输出MP4、字幕/音轨、分镜/来源/源码/模型锁、耗时、拒绝记录和未验证项。总流程/其它模型分流用 `local-ai-video-production`。
