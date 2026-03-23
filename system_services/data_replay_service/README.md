# data_replay_service

阶段1实现：

- `POST /replay`：按数据集时间顺序读取记录。
- 支持 `limit`、`speedup`、`emit_sleep` 参数。
- 语义上保持 5 秒采样节拍；演示脚本默认关闭真实 sleep，便于快速验证。
