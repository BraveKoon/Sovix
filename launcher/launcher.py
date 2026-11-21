#!/usr/bin/env python3
"""SOVIX 런처 실행 진입점."""

import sys

if sys.version_info < (3, 8):
    sys.exit("SOVIX 런처는 Python 3.8 이상이 필요합니다.")

try:
    import tkinter  # noqa: F401
except ImportError:
    sys.exit("tkinter가 없습니다. Linux라면 'sudo apt install python3-tk'로 설치하세요.")

if __name__ == "__main__":
    if "--demo-game" in sys.argv:
        # exe로 빌드된 경우 런처 자신이 데모 클라이언트 역할을 한다.
        sys.argv.remove("--demo-game")
        import demo_game
        demo_game.main()
    else:
        from sovix.app import main
        main()
