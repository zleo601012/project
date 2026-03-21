# window_builder_service

阶段1实现：

- `POST /build`：按 10 秒触发规则（即每两条 5 秒记录触发一次）构造窗口任务。
- 当前支持 `flow_anomaly_service` 与 `flow_forecast_service`。
- 使用完整滑动窗口，不做增量同步。
