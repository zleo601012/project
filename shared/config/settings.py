from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    project_root: Path = Path(__file__).resolve().parents[2]
    models_dir: Path = project_root / "models" / "trained"
    default_edge_node_id: str = "edge-node-local"
    default_deadline_ms: int = 3000
    replay_interval_seconds: int = 5
    trigger_interval_seconds: int = 10
    idle_container_ttl_seconds: int = 120

@lru_cache
def get_settings() -> Settings:
    return Settings()
