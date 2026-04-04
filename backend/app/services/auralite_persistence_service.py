import json
import os
from datetime import datetime
from ..config import Config


class AuralitePersistenceService:
    BASE_DIR = os.path.join(Config.UPLOAD_FOLDER, 'auralite', 'worlds')
    SNAPSHOT_DIR = os.path.join(Config.UPLOAD_FOLDER, 'auralite', 'snapshots')

    @classmethod
    def ensure_dir(cls):
        os.makedirs(cls.BASE_DIR, exist_ok=True)
        os.makedirs(cls.SNAPSHOT_DIR, exist_ok=True)

    @classmethod
    def world_path(cls, world_id: str) -> str:
        cls.ensure_dir()
        return os.path.join(cls.BASE_DIR, f'{world_id}.json')

    @classmethod
    def snapshot_path(cls, world_id: str, snapshot_id: str) -> str:
        cls.ensure_dir()
        return os.path.join(cls.SNAPSHOT_DIR, f'{world_id}_{snapshot_id}.json')

    @classmethod
    def save_world(cls, world_id: str, payload: dict):
        path = cls.world_path(world_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_world(cls, world_id: str) -> dict | None:
        path = cls.world_path(world_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def save_snapshot(cls, world_id: str, payload: dict, snapshot_id: str | None = None) -> str:
        snapshot_id = snapshot_id or datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        path = cls.snapshot_path(world_id, snapshot_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return snapshot_id

    @classmethod
    def load_snapshot(cls, world_id: str, snapshot_id: str) -> dict | None:
        path = cls.snapshot_path(world_id, snapshot_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
