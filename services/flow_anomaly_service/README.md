# flow_anomaly_service

## 定位

`flow_anomaly_service` 现在是一个**自包含的独立流量异常检测服务**：

- 训练逻辑、模型持久化、HTTP 服务、运行时都在本目录内。
- 不依赖 `shared/*` 才能启动或推理。
- 可以单独构建成镜像，只需要本服务目录作为 Docker build context。

当前模型信息：

- `task_type`: `anomaly`
- `model_name`: `FlowAnomalyBaseline`
- `model_version`: `v2`
- `window_length`: `12`
- `input_fields`: `flow_m3s`, `rain_intensity_mmph`, `temp_C`

## HTTP 接口

### `GET /health`
返回服务健康状态。

### `GET /meta`
返回服务静态元信息、模型是否已训练、当前 artifact 目录。

### `POST /train`
使用数据集直接在服务内部训练模型。

请求示例：

```json
{
  "dataset_path": "dataset/node_1.csv",
  "limit": 200
}
```

### `POST /infer`
提交一个完整窗口并返回异常检测结果。

请求中的 `features` 至少需要：

- `ts`
- `slot`
- `node_id`
- `flow_m3s`
- `rain_intensity_mmph`
- `temp_C`

## 本地运行

### 方式 1：直接训练

```bash
python3 -m services.flow_anomaly_service.train --dataset dataset/node_1.csv
```

### 方式 2：启动 HTTP 服务

```bash
python3 -m services.flow_anomaly_service.server
```

### 方式 3：从仓库根目录跑独立 smoke test

```bash
./scripts/test_flow_services.sh --dataset dataset/node_1.csv
```

## 模型产物

默认情况下，服务会把模型写到：

- `services/flow_anomaly_service/artifacts/flow_anomaly_service.joblib`
- `services/flow_anomaly_service/artifacts/flow_anomaly_service.metadata.json`

也可以通过环境变量覆盖：

```bash
MODEL_DIR=/data/models python3 -m services.flow_anomaly_service.server
```

## 单独构建镜像

从仓库根目录执行：

```bash
docker build -f services/flow_anomaly_service/Dockerfile services/flow_anomaly_service -t edge-offload/flow-anomaly-service:standalone
```

运行：

```bash
docker run --rm -p 8101:8000 -e MODEL_DIR=/app/services/flow_anomaly_service/artifacts edge-offload/flow-anomaly-service:standalone
```

如果需要在容器里训练，可以挂载数据集后调用 `/train`，或者在容器里执行：

```bash
python -m services.flow_anomaly_service.train --dataset /data/node_1.csv --output-dir /app/services/flow_anomaly_service/artifacts
```
