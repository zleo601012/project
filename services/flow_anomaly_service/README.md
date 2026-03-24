# flow_anomaly_service

基于 **Python + FastAPI + PyTorch(LSTM Autoencoder)** 的流量异常检测微服务。

## 1. 项目简介

该服务用于处理长度为 12 的多变量时间窗口（3个特征：`flow_m3s`、`rain_intensity_mmph`、`temp_C`），通过 LSTM Autoencoder 重构误差进行异常检测。

- 输入形状：`[batch, 12, 3]`
- 异常分数：窗口整体 MSE 重构误差
- 异常判定：`reconstruction_error > threshold`

## 2. 目录结构

```text
flow_anomaly_service/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── model.py
│   ├── schemas.py
│   └── service.py
├── artifacts/                # 训练输出目录（model.pt / scaler.pkl / threshold.json）
├── train.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 3. 安装方式

```bash
cd services/flow_anomaly_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. 训练命令

### 使用真实 CSV 训练

```bash
python train.py --train-csv ../../dataset/node_1.csv --epochs 30 --threshold-quantile 0.95
```

### 使用 mock 数据快速验证

```bash
python train.py --use-mock-data --mock-rows 1200 --epochs 5
```

训练完成后会输出到 `artifacts/`：

- `model.pt`
- `scaler.pkl`
- `threshold.json`

## 5. 启动命令

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 6. curl 调用示例

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 异常检测

```bash
curl -X POST "http://127.0.0.1:8000/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "window": [
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.4, "rain_intensity_mmph": 0.1, "temp_C": 22.9},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.1, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
      {"flow_m3s": 1.0, "rain_intensity_mmph": 0.2, "temp_C": 22.8},
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.4, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.5, "rain_intensity_mmph": 0.0, "temp_C": 23.2},
      {"flow_m3s": 1.6, "rain_intensity_mmph": 0.0, "temp_C": 23.3}
    ]
  }'
```

## 7. 输入输出说明

### 输入

`POST /detect` 请求体：

- `window`：长度必须等于 `12`
- 每个时间步必须包含且仅依赖以下数值字段：
  - `flow_m3s`
  - `rain_intensity_mmph`
  - `temp_C`

### 输出

```json
{
  "is_anomaly": true,
  "anomaly_score": 0.8421,
  "threshold": 0.5000,
  "reconstruction_error": 0.8421,
  "model_name": "lstm_autoencoder",
  "window_length": 12
}
```

---

## 运行步骤（最小可运行流程）

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 训练模型
   ```bash
   python train.py --use-mock-data --epochs 5
   ```
3. 启动服务
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. 测试接口
   ```bash
   curl http://127.0.0.1:8000/health
   curl -X POST "http://127.0.0.1:8000/detect" -H "Content-Type: application/json" -d '{"window": [...12条记录...]}'
   ```


## 8. 如何测试（同时输出结果和运行时间）

### 方法 A：curl 一次性输出返回体 + 总耗时

```bash
curl -s -X POST "http://127.0.0.1:8000/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "window": [
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.4, "rain_intensity_mmph": 0.1, "temp_C": 22.9},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.1, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
      {"flow_m3s": 1.0, "rain_intensity_mmph": 0.2, "temp_C": 22.8},
      {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
      {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
      {"flow_m3s": 1.4, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
      {"flow_m3s": 1.5, "rain_intensity_mmph": 0.0, "temp_C": 23.2},
      {"flow_m3s": 1.6, "rain_intensity_mmph": 0.0, "temp_C": 23.3}
    ]
  }' \
  -w "\ntime_total_s=%{time_total}\n"
```

### 方法 B：Python 脚本输出每次耗时、平均耗时和结果

```bash
python test_client.py --url http://127.0.0.1:8000/detect --repeat 10
```

示例输出：

```text
request=1, runtime_ms=42.31
request=2, runtime_ms=39.28
...
result_json=
{
  "is_anomaly": false,
  "anomaly_score": 0.1234,
  "threshold": 0.5000,
  "reconstruction_error": 0.1234,
  "model_name": "lstm_autoencoder",
  "window_length": 12
}
avg_runtime_ms=40.76
```
