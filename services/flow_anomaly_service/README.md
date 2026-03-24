# flow_anomaly_service（可独立运行）

这个目录现在可以独立运行，不依赖仓库里的 `shared/*`、`system_services/*`、其他业务服务。

## 独立运行方式

> 假设你把本目录单独拷贝到目标机器，目录名为 `flow_anomaly_service/`。

### 1) 训练模型

```bash
python -m flow_anomaly_service.train --dataset /path/to/node_1.csv
```

### 2) 启动服务

```bash
python -m flow_anomaly_service.server
```

默认监听 `0.0.0.0:8000`，支持：

- `GET /health`
- `GET /meta`
- `POST /train`
- `POST /infer`

## 推理请求要求

`POST /infer` 的 `features` 必须包含以下字段，并且长度一致、且长度必须是 `12`：

- `ts`
- `slot`
- `node_id`
- `flow_m3s`
- `rain_intensity_mmph`
- `temp_C`

这保证了每个任务都携带完整窗口，不依赖目标节点缓存历史数据。

## Docker（独立目录作为构建上下文）

在 `flow_anomaly_service/` 目录下执行：

```bash
docker build -t flow-anomaly-standalone .
docker run --rm -p 8101:8000 flow-anomaly-standalone
```
