# deployment/compose

`docker-compose.services.yml` 提供了 12 个业务微服务的本地编排样例，可用于一次性构建并启动全部业务镜像：

```bash
docker compose -f deployment/compose/docker-compose.services.yml up --build
```

如需让容器真正完成推理，请先生成 `models/trained/*.joblib` 模型文件，并在构建或运行阶段提供给镜像。
# deployment/compose/README.md
