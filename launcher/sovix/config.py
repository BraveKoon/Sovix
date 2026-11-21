"""런처 설정 저장/불러오기."""

import json
import os
import sys
from pathlib import Path

APP_NAME = "SOVIX"

DEFAULTS = {
    "nickname": "Operator",
    "game_path": "",
    "game_args": "",
    "region": "KR-Seoul",
    "resolution": "1920x1080",
    "display_mode": "전체화면",
    "quality": "높음",
    "max_fps": 144,
    "vsync": False,
    "fov": 95,
    "sensitivity": 2.5,
    "installed_version": "0.0.0",
    "close_on_launch": True,
    "auto_update": True,
}

REGIONS = {
    "KR-Seoul": ("kr.sovix.gg", 7777),
    "JP-Tokyo": ("jp.sovix.gg", 7777),
    "US-West": ("usw.sovix.gg", 7777),
    "EU-Frankfurt": ("eu.sovix.gg", 7777),
    "로컬 서버": ("127.0.0.1", 7777),
}

RESOLUTIONS = [
    "1280x720", "1600x900", "1920x1080",
    "2560x1080", "2560x1440", "3440x1440", "3840x2160",
]

DISPLAY_MODES = ["전체화면", "테두리 없는 창", "창 모드"]
QUALITIES = ["낮음", "보통", "높음", "최상"]


def config_dir() -> Path:
    """OS별 사용자 설정 폴더."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / APP_NAME


class Config:
    """JSON 파일 하나로 관리되는 평평한 설정 객체."""

    def __init__(self, data=None, path=None):
        self.path = path or (config_dir() / "launcher.json")
        self._data = dict(DEFAULTS)
        if data:
            self._data.update({k: v for k, v in data.items() if k in DEFAULTS})

    @classmethod
    def load(cls, path=None):
        path = path or (config_dir() / "launcher.json")
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return cls(json.load(fp), path)
        except (OSError, ValueError):
            return cls(None, path)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(self._data, fp, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def __getitem__(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def as_dict(self):
        return dict(self._data)
