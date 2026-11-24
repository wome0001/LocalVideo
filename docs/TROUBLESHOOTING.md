# 常见问题

|现象|先检查|处理|
|---|---|---|
|`gh`/云端API不可用|本项目是否需要它|生成主线不需要GitHub登录或付费生成API；GitHub只用于下载源码|
|FFmpeg找不到/字幕滤镜缺失|`localvideo doctor`、`ffmpeg -filters`|安装含libass/libx264的构建，设置工具环境变量；安装字体|
|中文字幕变方块|字体安装和实际fontconfig|Windows可用微软雅黑，Linux安装Noto Sans CJK；不要把字体当作仓库自有资产上传|
|`No module named localvideo`|是否在克隆根editable安装|`python -m pip install -e .`，确认当前Python和CLI属于同环境|
|模型未下载/校验失败|模型目录、catalog相对文件名、SHA|先仅检查，再显式下载；保留坏/不完整文件，不覆盖已审模型|
|Comfy节点缺失/schema错误|commit、插件路径、`/object_info`|按锁文件安装版本；不把另一版本图当可互换JSON|
|模型服务退出|本次work/logs，不猜原因|核torch/CUDA/Sage ABI和离线资源；修后用新attempt|
|Sampler快得不合理|history与进度事件、缓存节点|没有新prompt_id+实际步骤就不算新推理|
|声音机器味|场景意图、口语稿、参考声线和接话|先做短试听，改表演和句子；不要只调全局速度/响度|
|指导语被读出来|CosyVoice2 directed实验模式|退回zero-shot、核接口/参考，人工听审，勿把任意SSML塞入|
|听者嘴在动/说完仍抖|镜头说话者标签、音轨末尾和模型运动|修分镜/反打/本地局部口型；保留眼神反应；逐镜审，不整集重生成|
|合成拒绝缺音/区间越界|源WAV实际PCM样本、`frames/fps`|修剪辑计划或重新导出完整批准音频；不加静音绕过缺字检查|
|显存/内存不足|原生帧数、分辨率、量化、offload和其它GPU进程|先缩代表小样、按官方成熟profile；模型参数量小不保证快|
|hot盘空间不够|永久原件和热副本额外空间|换足够空间的新hot根或减少本次模型集合；不删分页文件|
|Windows路径转义|JSON中的反斜杠、PowerShell调用|JSON优先正斜杠；可执行路径带空格用`& '完整路径'`|

出错保留原回执、prompt_id、模型/代码SHA、步骤和日志。别同时升级torch/换量化/调步数再称“同条件修复”。不要把私人视频、声音或包含令牌的日志上传公开issue。
