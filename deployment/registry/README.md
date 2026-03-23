# deployment/registry

当各微服务镜像本地验证通过后，可以按服务粒度推送到私有镜像仓库，例如：

```bash
docker tag edge-offload/flow-anomaly-service:local registry.example.com/edge-offload/flow-anomaly-service:v1
docker push registry.example.com/edge-offload/flow-anomaly-service:v1
```

建议保持“一服务一镜像一标签”的发布策略，便于后续做镜像缓存和调度实验。
# deployment/registry/README.md
