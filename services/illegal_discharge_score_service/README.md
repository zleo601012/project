# illegal_discharge_score_service

## 1. 服务定位

- **作用**：偷排漏排嫌疑评分
- **任务类型**：`risk_score`
- **默认模型**：`XGBoostClassifier`
- **窗口长度**：`12` 条记录
- **适用场景**：用于对偷排漏排嫌疑进行风险评分，可供后续巡检、复核与联动处置使用。

该服务属于去中心化边缘协同系统中的正式业务微服务，适合被多个边缘节点按需拉起、复用和回收。服务本身只负责模型推理，不负责调度、卸载和发现邻居节点。

## 2. 输入字段

本服务实际建模重点字段如下：

- `flow_m3s`
- `pH`
- `DO_mgL`
- `EC_uScm`
- `COD_mgL`
- `NH3N_mgL`
- `TN_mgL`
- `TP_mgL`
- `TSS_mgL`
- `turbidity_NTU`

> 说明：为了保证全项目接口统一，`POST /infer` 仍然接收完整的统一 `features` 结构；服务内部只会提取本服务所需字段做特征工程与推理。

## 3. 时间与窗口规则

- 数据采样间隔：`5s`
- 任务触发建议：`10s`
- 默认窗口长度：`12` 条
- 输入方式：完整滑动窗口
- 单次任务语义：一个服务处理一个窗口

## 4. HTTP 接口

### 4.1 `GET /health`

用于健康检查。

**示例返回**：

```json
{
  "status": "ok",
  "service_name": "illegal_discharge_score_service"
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
  "service_name": "illegal_discharge_score_service",
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
  "service_name": "illegal_discharge_score_service",
  "result_type": "risk_score",
  "risk_score": 0.68,
  "label": "low_medium_high_or_binary",
  "model_name": "XGBoostClassifier",
  "model_version": "v1",
  "inference_ms": 8
}
```

## 5. 训练方式

对应训练入口位于：`training/illegal_discharge_score/train.py`

训练命令示例：

```bash
python training/illegal_discharge_score/train.py --dataset dataset/node_1.csv
```

如果需要一口气训练所有业务微服务，可以执行：

```bash
python scripts/train_all_services.py --dataset dataset/node_1.csv
```

## 6. 本地运行方式

如果运行环境已安装 `uvicorn` / `fastapi`，可以直接本地启动：

```bash
uvicorn services.illegal_discharge_score_service.app:app --host 0.0.0.0 --port 8302
```

启动后可访问：

- `http://127.0.0.1:8302/health`
- `http://127.0.0.1:8302/meta`
- `http://127.0.0.1:8302/infer`

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
