# LTX 与 ContentV：分清联合AV、音频条件和纯T2V

## LTX

[官方LTX-2](https://github.com/Lightricks/LTX-2)、[Comfy LTX-2.3示例](https://docs.comfy.org/tutorials/video/ltx/ltx-2-3)。这份历史记录测的是2.3 distilled FP8v1.0+GemmaFP4，不是对当前所有LTX版本的结论。

1. 按对应版本官方步骤，在单独环境装节点和完整video/audio VAE、文本编码器、采样/放大组件；导入官方workflow。
2. 用同一自有参考、短台词，分别测原生生成声音与已有音轨条件。记录是否产生新的声音，不能把原音贴回当作原生联合对白。
3. 保存导出的API图与节点schema，再通过通用Comfy客户端异步提交。相同的本地客户端能管任务，但不能替代版本专属图适配。
4. 检查每帧伪字幕、台词是否读全、嘴型/句尾、声音自然度。历史4条虽技术链路能跑，但均伪字幕失败；末控制样闭口而音频继续，未生产通过。

## ContentV-8B

[官方仓库](https://github.com/bytedance/ContentV)。先读README/demo参数和模型卡。历史公开接口只支持T2V，没有指定参考图或音轨输入和原生音轨输出；因此不能用它直接复现“指定人物图+已审对白”的任务。

可在独立环境按官方demo安装下载，固定prompt/seed/steps/尺寸后生成5秒静音样本，保存命令与版本；第二预定seed/更复杂动作复核。历史832×480、125帧24fps、50步、CFG6、INT8threshold0/DiT Sage/FFN分块约24–26分钟，第二动作门槛未稳定通过。

本仓库提供能力/验证流程，**没有**声称为LTX/ContentV写好了通用一键适配器。新版本接入应提交自己的API模板/源锁与失效样例测试，不复制私人项目工作流或把旧性能数字套到新模型。
