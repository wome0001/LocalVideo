---
name: scene-dialogue
description: Direct natural scene dialogue, cast distinct local voices, generate per-line takes, build listening cuts, align approved audio to footage and update dialogue subtitles. Use whenever video work includes dialogue.
---

# 对话技能

先判断本轮是写录、听审、已审贴画还是局部返修。已有批准版本时锁定词、声线、有效气口和音轨字节。

- 先看人物关系、动作和场景意图，再改口语稿。短句与半句承接，少量自然犹豫；不用小说书面段落硬朗读，不到处加“嗯”和喘气。
- 每个角色独立声线与年龄/关系特征。正常一句+情绪一句先对照，再进全场；成熟女性、老人、少女不共用同一女声。参考仅用获授权声音。
- 按完整一句/话轮生成，指导写“刚听到了什么、正在做什么、哪个字加重、怎么收”。日常以松弛中性为主，不全程激昂。不能把其它厂商SSML/stability参数当CosyVoice2通用接口。
- 先选自然take，再设计接话。顺接约0.15–0.35秒，迟疑约0.4–0.7秒仅作起点；少量重叠须保词尾。保有效呼吸，不为了旧口型强拉语速。
- 根据场景轻调增益、尖峰、高通、电话距离和微量房间反射；用明确角色/场景配置，不按旧项目角色字母/场次号猜处理。无合法环境声就不叠。
- 输出分句/分场试听、最终连听、SRT、角色与时间轴。ASR辅助掉字和读音，不证明自然。独立技术审查和人耳听审分开；用户要求先听审时未批准就不贴画。
- 批准WAV作为时钟：标说话者/听者/远端声、句首/转折/句尾/静听。改词多时用反打/侧脸/道具镜头；按授权修嘴型，不换声线或整片重生成人物。
- 重算字幕、完整解码、核台词/镜头/环境和音乐；没有实际听/看就写未验证。

随附 `scripts/compose_audition.py` 与 `scripts/validate_audition.py`；合成需要Python/NumPy/SciPy/SoundFile/FFmpeg。`--output` 必须新目录。音频进媒体根，字幕/JSON进元数据根，迁移读回SHA，不能因此重置听审批准。完整本地CosyVoice2录制和示例在 LocalVideo 克隆的 `docs/DIALOGUE.md`、`tools/cosyvoice2_batch.py`；保留仓库并按INSTALL准备独立环境。
