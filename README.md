# 去中心化边缘计算任务卸载原型系统

本仓库当前已补齐 **12 个正式业务微服务**，并把每个业务服务都整理到了**可直接打包成独立容器镜像**的程度。当前实现重点是：

- 使用 `dataset/` 中的数据集进行回放、窗口构建、训练与推理。
- 所有业务任务都使用统一 HTTP JSON 接口。
- 每个业务微服务都带有独立 `Dockerfile`、可启动的 `server.py`，可单独构建镜像。
- 每个业务微服务现在都拥有自己的 `logic.py`，由服务自身定义训练策略、特征字段和预测入口，不再只依赖单个中心化训练函数。
- `deployment/compose/docker-compose.services.yml` 提供了 12 个业务服务的本地编排样例。
- 模型二进制产物不入库，统一通过训练脚本本地生成后再随镜像打包或挂载。

## 已实现的 12 个业务微服务

1. `flow_anomaly_service`
2. `water_quality_anomaly_service`
3. `cod_anomaly_service`
4. `nh3n_anomaly_service`
5. `tss_turbidity_anomaly_service`
6. `do_anomaly_service`
7. `flow_forecast_service`
8. `cod_forecast_service`
9. `nh3n_forecast_service`
10. `tss_turbidity_forecast_service`
11. `mixed_sewage_rain_score_service`
12. `illegal_discharge_score_service`

## 快速开始

```bash
python scripts/train_all_services.py --dataset dataset/node_1.csv
python scripts/run_all_services_demo.py --dataset dataset/node_1.csv --limit 80
python -m pytest -q
```

## 镜像构建与运行

### 构建单个服务镜像

```bash
docker build -f services/flow_anomaly_service/Dockerfile -t edge-offload/flow-anomaly-service:local .
```

### 运行单个服务镜像

```bash
docker run --rm -p 8000:8000 edge-offload/flow-anomaly-service:local
```

### 启动全部业务服务样例编排

```bash
docker compose -f deployment/compose/docker-compose.services.yml up --build
```

> 说明：容器运行推理前需要存在对应的 `models/trained/*.joblib` 模型文件；可先执行训练脚本生成，再选择将模型打包进镜像或运行时挂载。

> 说明：当前执行环境无法联网安装依赖，因此仓库内提供了极简兼容层；容器内默认仍可直接运行这些服务，但如果你在真实环境部署，建议切换到正式依赖并接入真实 ASGI/WSGI 运行栈。
