# models/trained

该目录只保留可文本审查的元数据文件与占位文件，不再提交 `.joblib` 等二进制模型产物。

请使用以下命令在本地重新生成阶段1模型：

```bash
python scripts/train_phase1_models.py --dataset dataset/node_1.csv
```

生成后的二进制模型文件会写入当前目录，但默认被 `.gitignore` 忽略，避免再次导致 PR 因二进制文件被阻塞。
