# 课件、界面与程序动画

## 课件讲解

使用自己的PPT/讲义，不上传内容到仓库。安装 [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) 后先导PDF：

```bash
soffice --headless --convert-to pdf --outdir /your/work/slides /your/inputs/lecture.pptx
```

在独立环境安装 [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/installation.html)，逐页render为832×480画幅内的清晰图片。讲解稿按“解释概念、举简单例子、过渡下一页”改成口语，不逐字照读；成熟女性声线用scene-dialogue先试听。每页图片持续时间来自批准讲解音轨，FFmpeg合成并加字幕。静态PPT讲解不应浪费图生视频采样。

## 67.js与界面动画

官方 [67.js](https://github.com/codepawl/67.js) / [文档](https://67js.codepawl.com)。历史npm版本为 `@codepawlhq/67js@0.19.0`，使用独立Node项目安装；API/渲染按该版本官方说明。记录Node/浏览器/GPU版本和逐帧时钟。

适合图形、UI、图表和可控镜头示意；不保证能生成高质量真人脸/手。按键动作移动手和键帽，不能让整个屏幕晃；镜头转换用真实动作接点与稳定时钟，先做5–10秒检查转场卡顿。界面内容自己生成，产品真实截图需另有授权，不随本仓库提供。

本仓库不提供67.js或PPT上游引擎的重实现，仅记录资源、方法和与对白/剪辑主线的衔接；与可执行Wan/CPU烟测入口分别标注。
