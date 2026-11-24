# FreeVideo/H3：可选实验路线

官方：[FreeVideo](https://github.com/FlashML-org/FreeVideo)。源码安装参考固定 commit 见 configs；新版本模板和节点可能变化。使用官方下载器/安装器，按上游README在独立Comfy环境安装，下载其指定模型；本仓库不转发二进制、图标、样片或权重。

## 实施步骤

1. 在FreeVideo工作台用自己的图片/文本/可选参考音频或guide，先做单条短样。音频参考/重建不是自动自然对白；对话先用本地TTS完成听审。
2. 先确定支持的二采尺寸。历史960×544配置可先480×288采8步再3步细化；832×480并非同一种低分辨率二采，不能只改输出标签。
3. 保存工作台设置、实际API图、种子、模型/LoRA/音频参考和所有输入SHA。需要脚本化时，从当前版本导出**API格式**JSON，使用通用 `skills/wan22-s2v-local-production/scripts/comfy_submit.py` 提交；不要拿前端layout JSON直接当API图。
4. 显式提供 `--url http://127.0.0.1:端口 --input-dir 本次input --output-dir 本次output --report 新回执.json`；服务必须自行按FreeVideo官方方式启动。客户端轮询完成/错误、检查文件和完整解码，不改FreeVideo模型实现。
5. guide生成是独立成本：历史用MuseTalk1.5连续口部guide；孤立开闭口帧、逐帧不连续及音画错位会放大问题。原音、参考、guide生成、推理与后期分别计时。
6. 冻结同一输入，与Wan比较冷/暖机、实际采样、有效交付长度和质量。FreeVideo历史5.5秒约400.859秒，**尚未证明比Wan快**；嘴齿软/上半脸固定、自然度与逐音素仍需人工审。

这是“官方工具+导出图+通用客户端”的接入配方，没有假装提供适配所有FreeVideo版本的一键生成器。README的精简介绍/安装/硬件/限制层次是本仓库展示参考；使用者应看官方当前文档再测新版本。
