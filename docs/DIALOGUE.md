# 自然对白：编剧、表演、声线和交互节奏一起处理

## 先把台词变成聊天

先看人物正在做什么、想说什么、为何此刻说。用短句、承接和少量自然犹豫；不机械添加“嗯”和呼吸，不把书面稿按标点切碎。每句的方向写“刚听到了什么、轻重在哪、说完如何收住”，多数日常对白保持松弛，仅关键字加重。

每个角色固定独立参考声线，年龄/音高/说话习惯拉开差距。成熟女性、老年女性和少女不能共用同一女声。先各做正常一句和情绪一句，再进全场。普通预制声线或克隆都不自动有表演能力。

## 本地 CosyVoice2

用独立环境安装 [CosyVoice 官方源码](https://github.com/QwenAudio/CosyVoice)，锁定 [upstreams.lock.json](../configs/upstreams.lock.json) 的 CosyVoice commit，并递归初始化子模块。不要把三代模型文档当成二代接口。

```bash
python tools/install_upstreams.py --name CosyVoice --destination /your/tools/CosyVoice
# 在单独的 CosyVoice 环境内执行：
python -m pip install -r /your/tools/CosyVoice/requirements.txt
```

从 [CosyVoice2-0.5B](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) 下载完整模型目录（包含 tokenizer/frontend 文件），按上游 README 安装系统依赖；不要只拿一个权重文件。在下载准备环境先安装 `python -m pip install huggingface_hub`，再用 `huggingface_hub.snapshot_download(repo_id='FunAudioLLM/CosyVoice2-0.5B', revision='eec1ae6c79877dbd9379285cf8789c9e0879293d', local_dir='/your/models/CosyVoice2-0.5B')`，随后保存目录清单/SHA/模型卡。此公开快照版本在发布打包时解析，见 configs/cosyvoice2-snapshot.json；不是原私人听审记录的替代。模型、引用声音和许可不随本仓库提供。

1. 复制 `examples/voices.template.json`，每个角色给自己拥有或获授权的参考WAV、精确转录和 `consent_confirmed=true`。不要替别人勾授权。参考最好自然聊天，不朗诵；避免嘈杂、多说话人或过度表演。
2. 用 `python tools/lock_inputs.py voices.template.json --output voices.locked.json` 固定参考SHA。
3. 按 [dialogue.plan](../examples/dialogue.plan.json) 写场景和短句，每句稳定ID、role、text、direction、rate、hold。

```bash
/your/cosy-python tools/cosyvoice2_batch.py --cosy-root /your/tools/CosyVoice --model /your/models/CosyVoice2-0.5B --plan /your/metadata/dialogue.plan.json --voices /your/metadata/voices.locked.json --output /your/media/takes-v1 --device cpu
```

默认逐句zero-shot，输出每句WAV及记录。`--device cuda` 可在支持的环境使用；CPU是本地低显存选项，不是保证更快。`--mode directed` 使用历史版本内部 `frontend_instruct2` 组合，是实验功能；必须核当前接口、检查有没有把指导语读出来，并做短试听。CosyVoice2不接受任意SSML；不能把 `stability`、`similarity` 等其它厂商参数硬塞进接口。生成时HF/Transformers离线标志开启，模型必须本地就绪。

## 接话和混音

在自然完整发声的基础上安排接话：顺接约0.15–0.35秒，迟疑约0.4–0.7秒；数值是编导起点，不是每句统一阈值。很少量重叠须保证双方词尾清楚，不为“像真人”到处抢话。先选择自然take，再剪时序，不能先规定时长硬拉声音。

```bash
localvideo dialogue-mix --plan /your/metadata/dialogue.plan.json --takes /your/media/takes-v1 --output /your/work/audition-v1 --ffmpeg /your/tools/ffmpeg
localvideo dialogue-check /your/work/audition-v1/dialogue-audition.wav /your/work/audition-v1/dialogue-audition.srt
```

`role_levels` 调角色目标电平，`role_profiles` 显式指定电话滤波/高通/反射，场景可给 `reflection_gain`、`reflection_delay_ms`、`room_rms`；不按旧作品角色字母/场景编号套处理。`gain_db` 仅改指定一句。`reference-mix` 可用同场安静片段作为房间声；没有合法底声就不叠，不伪造呼吸。程序输出WAV、MP3、逐场SRT和timeline；试听通过后音频归媒体根，字幕/JSON归元数据根，读回SHA绑定。

## 听审通过才贴画

技术检查：非空、无NaN/削波、时钟/字幕覆盖、掉字/指导语/读音（可用本地Whisper辅助）。**ASR正确不证明自然**。独立技术审核不能代替人耳；缺听觉能力就写待听审。

批准版WAV作为时间主线：先标说话者/听者、远端电话声和手部镜头，句首/转折/句尾逐处对齐。说完后头嘴不应乱动，眼睛可自然反应。字幕来自最终对白，不从旧视频时间硬贴。换词很多时用反打/侧脸/道具插镜，按授权使用本地对口型工具，别靠时间拉伸修整段。
