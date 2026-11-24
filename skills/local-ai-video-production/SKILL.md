---
name: local-ai-video-production
description: Plan and validate local AI films, short dramas and model comparisons with structured shots, assets, dialogue, performance receipts, editing and independent quality gates. Route Wan execution to wan22-s2v-local-production and dialogue to scene-dialogue.
---

# 本地视频制作总流程

先读用户当前要求、项目交付索引和审核记录。新模型先查官方真实输入/输出和成熟实例，冻结版本、规格和门槛；不把能运行当质量通过。只做短样/对照时不生成整集。

流程：定调 → 场景剧本 → 结构分镜 → 人物/场景/声音资产 → 代表镜头 → 小批生成 → 独立审核/定向重做 → 剪辑/混音/字幕 → 归档与发布。

- 分镜含ID、说话者/听者、场景状态、动作次序、情绪、景别/运镜、对白、参考ID/SHA、原生帧数/FPS、有效入出点。
- 对白用 `scene-dialogue`，已审声音锁字节和节奏，远端说话不能驱动画面听者的嘴。
- Wan用 `wan22-s2v-local-production`。其它模型先核T2V/I2V/S2V/原生音轨能力；不能靠后配音让静音模型变成原生AV。
- 先算复用和真正需生成的镜头，一个GPU队列，静态缓存与采样结果缓存分开；记录新task_id、真实步骤、装载/编码/采样/解码/导出/审核/等待。
- 技术完整、可见缺陷、身份、动作、静听口部、声音自然度分项裁决。缺听觉/实时播放就写未验证。拒绝take和失败日志保留，不事后放宽门槛。
- 文件放用户明确的元数据/媒体/临时/永久模型根，不默认特定盘符。热副本不是唯一模型，不碰分页文件，单盘链接不算备份。

代码与详细配方位于 LocalVideo 克隆仓库；定位 `LOCALVIDEO_HOME` 或用户工作区，不推定技能安装目录就是仓库。先读 `docs/INSTALL.md`、`docs/WORKFLOW.md`，换模型再读 `docs/MODELS.md`/`docs/RESOURCES.md`。仅复制技能不等于安装GPU运行时。外部访问、收费、审核和发布按当前用户授权，不新增审批。
