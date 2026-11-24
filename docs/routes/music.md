# 音乐、主题曲与歌声：按能力选工具

音乐与对白分开制作、审核、归档，不把TTS自然度通过等同歌曲通过。可选官方工具：

- [ACE-Step](https://github.com/ace-step/ACE-Step)：按上游版本评估本地歌曲/伴奏；先短段、确认硬件/许可再做全曲。
- [Stable Audio Tools](https://github.com/Stability-AI/stable-audio-tools)：本地音乐/音效工具入口；具体“Stable Audio”型号是否开放本地权重必须另核，云服务名称不等于可部署模型。
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)：参考语音合成/声线方向，不默认承担完整歌曲制作。
- [DiffSinger](https://github.com/openvpi/DiffSinger)：曲谱/声库驱动歌声，需合法声库与准确音符/歌词，不是随意一段文字就会写歌。
- [DiffRhythm](https://github.com/ASLP-lab/DiffRhythm)：按当前上游支持的base/chunked/片长与显存设置先验证；不能把历史“8GB”口头估计当所有配置最低要求。

实践顺序：主题/情绪→词曲/器乐短候选→段落结构→人耳审核→全曲→对白避让/混音→有歌词时逐句字幕。对白清晰优先；音乐ducking、环境与短混响以场景为准，避免全程轰鸣掩盖轻声。记录来源、许可、BPM、音量和最终选用版本。歌曲/声音/成片不提交本仓库。
