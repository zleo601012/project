# deployment/docker

本目录的约定是：**每个业务微服务在各自目录下维护独立 `Dockerfile`**，例如：

```bash
docker build -f services/flow_anomaly_service/Dockerfile -t edge-offload/flow-anomaly-service:local .
```

镜像内默认通过 `python -m services.<service>.server` 启动基于标准库 HTTP Server 的推理服务，暴露 `8000` 端口。
# deployment/docker/README.md
