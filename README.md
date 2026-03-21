# 去中心化边缘计算任务卸载原型系统

本仓库当前已补齐**第一批 12 个正式业务微服务**，可用于你在多边缘设备上的批量部署测试。当前实现重点是：

- 使用 `dataset/` 中的数据集进行回放、窗口构建、训练与推理。
- 所有业务任务都使用统一 HTTP JSON 接口。
- 已补齐 12 个业务微服务的目录、推理服务、训练脚本与模型元数据。
- 仍保留阶段化扩展思路：当前优先完成“服务完整可测”，后续再继续强化容器化、多节点卸载与镜像感知调度。
- 模型二进制产物不入库，统一通过训练脚本本地生成。

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
pytest
```

> 说明：`.joblib` 模型文件属于二进制文件，仓库只提交训练脚本、元数据与说明，不提交模型二进制。

> 说明：当前执行环境无法联网安装依赖，因此仓库内提供了极简的 `fastapi` / `pydantic` / `sklearn` / `lightgbm` / `xgboost` 兼容层，保证原型在离线沙箱中可运行；后续可替换为正式依赖。
