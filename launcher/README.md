# SOVIX 런처

SOVIX FPS용 데스크톱 런처입니다. 파이썬 표준 라이브러리(tkinter)만 사용하므로 **Windows / macOS / Linux**에서 추가 패키지 없이 실행됩니다.

## 실행 방법

**Windows**: [Python 3.8 이상](https://www.python.org/downloads/)을 설치("Add to PATH" 체크)한 뒤 `run.bat`을 더블클릭합니다.

**macOS / Linux**:
```bash
./run.sh
```
(Linux에서 tkinter 오류가 나면 `sudo apt install python3-tk`)

## Windows용 .exe 만들기

`build_exe.bat`을 실행하면 `dist\SOVIX Launcher\SOVIX Launcher.exe`가 생성됩니다. 폴더째로 배포하면 플레이어 PC에 파이썬이 없어도 실행됩니다.

## 기능

| 화면 | 내용 |
|---|---|
| 홈 | 소식, 서버 지역 선택 + 실시간 핑, 닉네임, 현재 설정 요약, **게임 시작 / 업데이트** 버튼 |
| 설정 | 해상도, 화면 모드, 그래픽 품질, 최대 FPS, 수직 동기화, 시야각, 마우스 감도, 자동 업데이트, 실행 후 런처 닫기, 게임 실행 파일 경로, 추가 실행 인자, 실행 명령 미리보기 |
| 패치노트 | 버전별 변경 사항 |
| 로그 | 패치·실행·오류 기록 |

- 설정은 자동 저장됩니다: Windows `%APPDATA%\SOVIX\launcher.json`, Linux `~/.config/SOVIX/launcher.json`, macOS `~/Library/Application Support/SOVIX/`
- 단축키: `Enter` = 게임 시작, `F5` = 서버 상태 새로고침

## 실제 게임과 연결하기

1. **실행 파일**: 설정 → "게임 실행 파일"에서 `SOVIX.exe`를 선택합니다. 비워두면 `demo_game.py`가 실행되어 전달받은 인자를 화면에 보여줍니다.
2. **실행 인자**: 게임은 아래 인자를 받습니다 (형식 변경: `sovix/services.py` → `build_launch_args`)
   ```
   -ResX=1920 -ResY=1080 -fullscreen|-borderless|-windowed -quality=low|medium|high|epic
   -maxfps=144 -vsync=0 -fov=95 -sens=2.50 -name=<닉네임> -server=<호스트>:<포트>
   ```
3. **서버 주소**: `sovix/config.py`의 `REGIONS`를 수정합니다. 핑은 해당 호스트:포트로 TCP 연결을 시도해 측정합니다.
4. **소식 / 패치노트 / 최신 버전**: `content.json`을 수정합니다. `latest_version`을 올리면 런처에 "업데이트" 버튼이 뜹니다. 나중에 서버에서 받아오려면 `load_content()`만 HTTP 요청으로 바꾸면 됩니다.
5. **패치 다운로드**: 지금 `sovix/services.py`의 `run_patch()`는 진행 바만 움직이는 **시뮬레이션**입니다. CDN이 준비되면 이 함수 본문을 실제 다운로드/검증 코드로 교체하세요. `progress_cb(백분율, 메시지)`만 계속 호출하면 UI는 그대로 동작합니다.

## 구조

```
launcher.py        실행 진입점
demo_game.py       런처 연동 확인용 데모 클라이언트
content.json       소식, 패치노트, 최신 버전
sovix/
  app.py           메인 창과 각 화면
  services.py      핑, 패치, 게임 실행
  config.py        설정 저장/불러오기, 서버·해상도 목록
  theme.py         색상, 폰트, 스타일
  widgets.py       토글, 슬라이더, 스크롤 위젯
```
