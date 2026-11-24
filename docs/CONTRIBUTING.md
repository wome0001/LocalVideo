# 贡献指南

欢迎带可复现证据的模型适配、速度优化、对白/嘴型修复和文档改进。先提具体问题/模型版本/硬件/复现命令，不提交私人素材、声线、密钥、作品或整个运行目录。

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/check_public_tree.py
```

GPU改动先声明同输入/模型/精度/seed/步数/尺寸/FPS与质量门槛，再做baseline/optimized暖机对照，至少每组两个新任务；保留负结果。修改角色/音轨/镜头时遵循scene-dialogue和审核要求。CI通过只证明对应技术检查，独立审查者审核实际产物后再发布。

新路线上交：官方来源/许可、版本与模型SHA、配置/API图、单镜步骤、真实异步完成/失败、分项耗时、质量限制和至少一项失效测试。不要用更低分辨率/少帧/缓存命中冒充同条件提速。
