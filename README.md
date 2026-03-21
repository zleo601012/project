# 去中心化边缘计算任务卸载原型系统（阶段1）

本仓库当前交付**阶段1：单机可运行版本**，重点完成以下能力：

- 统一共享 schema、配置、特征工程、模型加载与结构化日志。
- `data_replay_service`：按数据集顺序回放记录，支持 5 秒采样语义。
- `window_builder_service`：按 10 秒节拍构建检测/预测窗口任务。
- `flow_anomaly_service`：基于 IsolationForest 的流量异常检测。
- `flow_forecast_service`：基于 LightGBM 的流量短时预测。
- 训练脚本、模型导出脚本、单机演示脚本、基础单元测试。
- 模型二进制产物不入库，统一通过训练脚本本地生成。

## 快速开始

```bash
python scripts/train_phase1_models.py --dataset dataset/node_1.csv
python scripts/run_phase1_demo.py --dataset dataset/node_1.csv --limit 30
pytest
```

> 说明：`.joblib` 模型文件属于二进制文件，容易导致代码审查/PR 工具拒绝展示或直接拦截，因此仓库只提交训练脚本与元数据，不提交模型二进制。

> 说明：当前执行环境无法联网安装依赖，因此仓库内提供了极简的 `fastapi` / `pydantic` / `sklearn` / `lightgbm` 兼容层，保证阶段1原型在离线沙箱中可运行。后续接入真实容器化部署时，可直接替换为正式依赖。

## 阶段1目录

- `shared/`：共享 schema、日志、配置、ML 工具。
- `system_services/data_replay_service/`：数据回放服务。
- `system_services/window_builder_service/`：窗口构建服务。
- `services/flow_anomaly_service/`：异常检测微服务。
- `services/flow_forecast_service/`：预测微服务。
- `training/flow_anomaly/` 与 `training/flow_forecast/`：训练脚本。
- `scripts/run_phase1_demo.py`：最小可运行演示。

## 阶段边界

本次提交**只实现阶段1**，其余 10 个业务微服务与多节点卸载服务先提供骨架目录和 README，占位留待阶段2/3/4 继续扩展。
