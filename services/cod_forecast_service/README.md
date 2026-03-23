# cod_forecast_service

## 1. 服务定位

- **作用**：COD短时预测
- **任务类型**：`forecast`
- **默认模型**：`LightGBMRegressor`
- **窗口长度**：`24` 条记录
- **适用场景**：基于最近 120 秒窗口预测下一时刻 COD 变化趋势，用于短时趋势感知。

该服务属于去中心化边缘协同系统中的正式业务微服务，适合被多个边缘节点按需拉起、复用和回收。服务本身只负责模型推理，不负责调度、卸载和发现邻居节点。

## 2. 输入字段

本服务实际建模重点字段如下：

- `COD_mgL`
- `flow_m3s`
- `rain_intensity_mmph`
- `temp_C`

> 说明：为了保证全项目接口统一，`POST /infer` 仍然接收完整的统一 `features` 结构；服务内部只会提取本服务所需字段做特征工程与推理。

## 3. 时间与窗口规则

- 数据采样间隔：`5s`
- 任务触发建议：`10s`
- 默认窗口长度：`24` 条
- 输入方式：完整滑动窗口
- 单次任务语义：一个服务处理一个窗口

## 4. HTTP 接口

### 4.1 `GET /health`

用于健康检查。

**示例返回**：

```json
{
  "status": "ok",
  "service_name": "cod_forecast_service"
}
```

### 4.2 `GET /meta`

用于获取服务元信息，包括服务名、模型名、模型版本、任务类型、窗口长度和输入字段。

### 4.3 `POST /infer`

用于提交一个窗口任务并返回推理结果。

**示例请求**：

```json
{
  "task_id": "demo-task-001",
  "service_name": "cod_forecast_service",
  "source_edge_node": "edge-node-a",
  "source_data_node": "data-node-1",
  "window_start": "2026-01-01 00:00:00",
  "window_end": "2026-01-01 00:00:55",
  "deadline_ms": 3000,
  "features": {
    "ts": ["2026-01-01 00:00:00", "2026-01-01 00:00:05", "..."],
    "slot": [0, 1, 2],
    "node_id": ["1", "1", "1"],
    "rain_intensity_mmph": [0.0, 0.0, 0.5],
    "flow_m3s": [0.13, 0.14, 0.16],
    "temp_C": [15.2, 15.0, 14.9],
    "pH": [7.1, 7.2, 7.1],
    "DO_mgL": [1.5, 1.4, 1.3],
    "EC_uScm": [936.3, 923.2, 940.1],
    "COD_mgL": [159.9, 121.2, 140.0],
    "NH3N_mgL": [8.3, 9.5, 8.9],
    "TN_mgL": [19.3, 17.4, 18.0],
    "TP_mgL": [2.5, 2.3, 2.0],
    "TSS_mgL": [56.2, 70.1, 72.0],
    "turbidity_NTU": [22.3, 19.4, 23.1]
  }
}
```

**示例响应**：

```json
{
  "task_id": "demo-task-001",
  "service_name": "cod_forecast_service",
  "result_type": "forecast",
  "prediction": 0.52,
  "model_name": "LightGBMRegressor",
  "model_version": "v1",
  "inference_ms": 8
}
```

## 5. 训练方式

对应训练入口位于：`training/cod_forecast/train.py`

训练命令示例：

```bash
python training/cod_forecast/train.py --dataset dataset/node_1.csv
```

如果需要一口气训练所有业务微服务，可以执行：

```bash
python scripts/train_all_services.py --dataset dataset/node_1.csv
```

## 6. 本地运行方式

如果运行环境已安装 `uvicorn` / `fastapi`，可以直接本地启动：

```bash
uvicorn services.cod_forecast_service.app:app --host 0.0.0.0 --port 8202
```

启动后可访问：

- `http://127.0.0.1:8202/health`
- `http://127.0.0.1:8202/meta`
- `http://127.0.0.1:8202/infer`

## 7. 在多边缘节点测试中的建议用法

- 高优先级节点可以预热该服务镜像与模型文件。
- 低频节点可以只保留镜像缓存，在任务到来时按需启动。
- 调度层可以先通过 `/meta` 确认窗口长度、输入字段和模型版本，再决定是否本地执行或卸载到其他边缘节点。
- 若需要回放测试，可结合：
  - `system_services/data_replay_service`
  - `system_services/window_builder_service`
  - `scripts/run_all_services_demo.py`

## 8. 当前实现说明

- 当前版本号：`v1`
- 当前以“先跑通完整链路”为目标
- 模型精度不是第一优先级，后续可以替换为更强模型或更精细的弱标签策略
- 模型二进制文件默认不入库，由训练脚本在本地生成

## 9. 容器镜像构建

本服务目录已补齐独立 `Dockerfile` 与可直接启动的 `server.py`，可以单独构建为镜像：

```bash
docker build -f services/cod_forecast_service/Dockerfile -t edge-offload/cod_forecast_service:local .
docker run --rm -p 8000:8000 edge-offload/cod_forecast_service:local
```

> 如果需要在容器内执行推理，请先在宿主机生成 `models/trained/cod_forecast_service.joblib`，或在镜像构建前将训练产物放入构建上下文。

