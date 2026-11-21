"""런처 백엔드: 서버 핑, 패치 확인, 게임 실행."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from .config import REGIONS

FROZEN = getattr(sys, "frozen", False)
# PyInstaller로 묶였을 때는 데이터 파일이 _MEIPASS 아래에 풀린다.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
CONTENT_FILE = ROOT / "content.json"

_FALLBACK_CONTENT = {
    "latest_version": "1.0.0",
    "patch_size_mb": 0,
    "news": [],
    "patch_notes": [],
}


def load_content():
    """뉴스/패치노트 데이터. 실제 서비스에서는 이 함수만 HTTP로 바꾸면 된다."""
    try:
        with open(CONTENT_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        merged = dict(_FALLBACK_CONTENT)
        merged.update(data)
        return merged
    except (OSError, ValueError):
        return dict(_FALLBACK_CONTENT)


def tcp_ping(region, timeout=2.0):
    """지역 서버에 TCP 연결을 시도하고 왕복 시간(ms)을 돌려준다. 실패하면 None."""
    host, port = REGIONS.get(region, ("127.0.0.1", 7777))
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return None
    return (time.perf_counter() - started) * 1000.0


def version_tuple(text):
    parts = []
    for chunk in str(text).split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def needs_update(installed, latest):
    return version_tuple(installed) < version_tuple(latest)


def build_launch_args(cfg):
    """설정값을 실행 인자로 변환한다 (언리얼/유니티 계열 관례)."""
    width, _, height = cfg["resolution"].partition("x")
    host, port = REGIONS.get(cfg["region"], ("127.0.0.1", 7777))
    args = [
        "-ResX=%s" % width,
        "-ResY=%s" % height,
        {"전체화면": "-fullscreen",
         "테두리 없는 창": "-borderless",
         "창 모드": "-windowed"}[cfg["display_mode"]],
        "-quality=%s" % {"낮음": "low", "보통": "medium",
                         "높음": "high", "최상": "epic"}[cfg["quality"]],
        "-maxfps=%d" % int(cfg["max_fps"]),
        "-vsync=%d" % (1 if cfg["vsync"] else 0),
        "-fov=%d" % int(cfg["fov"]),
        "-sens=%.2f" % float(cfg["sensitivity"]),
        "-name=%s" % (cfg["nickname"] or "Operator"),
        "-server=%s:%d" % (host, port),
    ]
    extra = (cfg["game_args"] or "").split()
    return args + extra


def resolve_executable(cfg):
    """실행할 대상을 고른다. 게임 경로가 비어 있으면 동봉된 데모 빌드를 쓴다."""
    path = (cfg["game_path"] or "").strip()
    if path:
        exe = Path(path).expanduser()
        if not exe.exists():
            raise FileNotFoundError(str(exe))
        return [str(exe)], False
    if FROZEN:
        return [sys.executable, "--demo-game"], True
    return [sys.executable, str(ROOT / "demo_game.py")], True


def launch_game(cfg):
    """게임 프로세스를 띄우고 (Popen, 명령줄, 데모여부)를 돌려준다."""
    command, is_demo = resolve_executable(cfg)
    full = command + build_launch_args(cfg)
    workdir = str(Path(full[0]).parent) if not is_demo else str(ROOT)
    kwargs = {"cwd": workdir}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0)
    else:
        kwargs["start_new_session"] = True
    if not os.access(full[0], os.X_OK) and not is_demo and not sys.platform.startswith("win"):
        raise PermissionError(full[0])
    return subprocess.Popen(full, **kwargs), full, is_demo


def run_patch(latest_version, total_mb, progress_cb, cancelled):
    """패치를 적용한다.

    실제 CDN이 생기면 이 함수 본문만 다운로드/검증 코드로 교체하면 되고,
    UI 쪽은 progress_cb(백분율, 메시지)만 그대로 받으면 된다.
    """
    steps = [
        (6, "패치 서버 접속"),
        (14, "매니페스트 비교"),
        (78, "패치 파일 내려받기"),
        (94, "파일 무결성 검사"),
        (100, "설치 마무리"),
    ]
    done = 0.0
    for target, message in steps:
        while done < target:
            if cancelled():
                return False
            done = min(target, done + 1.7)
            mb = total_mb * done / 100.0
            detail = message
            if message == "패치 파일 내려받기" and total_mb:
                detail = "%s  %.0f / %.0f MB" % (message, mb, total_mb)
            progress_cb(done, detail)
            time.sleep(0.02)
    progress_cb(100, "v%s 설치 완료" % latest_version)
    return True
