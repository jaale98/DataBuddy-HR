from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    storage_root: Path


def load_settings() -> Settings:
    root = Path(os.getenv("DATABUDDY_STORAGE_ROOT", "./storage"))
    return Settings(storage_root=root)


SETTINGS = load_settings()
