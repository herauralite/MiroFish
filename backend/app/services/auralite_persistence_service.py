import json
import os
from ..config import Config


class AuralitePersistenceService:
    BASE_DIR = os.path.join(Config.UPLOAD_FOLDER, 'auralite', 'worlds')

    @classmethod
    def ensure_dir(cls):
        os.makedirs(cls.BASE_DIR, exist_ok=True)

    @classmethod
    def world_path(cls, world_id: str) -> str:
        cls.ensure_dir()
        return os.path.join(cls.BASE_DIR, f'{world_id}.json')

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
