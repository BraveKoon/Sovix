"""SOVIX 런처 메인 윈도우."""

import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from . import services
from . import theme as T
from .config import (DISPLAY_MODES, QUALITIES, REGIONS, RESOLUTIONS, Config)
from .widgets import ScrollFrame, ScrollText, Toggle, ValueSlider

LAUNCHER_VERSION = "1.0.0"
PING_INTERVAL_MS = 30000


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = Config.load()
        self.content = services.load_content()
        self.events = queue.Queue()
        self.busy = False
        self._cancel = False
        self._game_proc = None
        self._ping_job = None

        self.title("SOVIX 런처")
        self.geometry("1100x760")
        self.minsize(980, 700)
        self.configure(bg=T.BG)
        T.apply_styles(self)
        self._set_icon()

        self.vars = self._make_vars()
        self._build_header()
        self._build_footer()  # body(expand)보다 먼저 pack해야 창이 작아져도 잘리지 않는다
        self._build_body()
        self.show_view("home")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Return>", lambda _e: self._on_play())
        self.bind("<F5>", lambda _e: self.refresh_ping())
        self.after(60, self._pump)
        self.after(200, self.refresh_ping)
        self.after(400, self._initial_check)

    # ---------------------------------------------------------------- 공통

    def _set_icon(self):
        """오렌지 바탕에 어두운 사선이 들어간 32x32 엠블럼을 코드로 그린다."""
        size = 32
        rows = []
        for y in range(size):
            pixels = []
            for x in range(size):
                edge = x < 2 or y < 2 or x >= size - 2 or y >= size - 2
                slash = 6 < (x + y) - (size // 2) < 14
                pixels.append(T.BG if (edge or slash) else T.ACCENT)
            rows.append("{" + " ".join(pixels) + "}")
        try:
            self._icon = tk.PhotoImage(width=size, height=size)
            self._icon.put(" ".join(rows))
            self.iconphoto(True, self._icon)
        except tk.TclError:
            pass

    def _make_vars(self):
        c = self.cfg
        return {
            "nickname": tk.StringVar(value=c["nickname"]),
            "region": tk.StringVar(value=c["region"]),
            "resolution": tk.StringVar(value=c["resolution"]),
            "display_mode": tk.StringVar(value=c["display_mode"]),
            "quality": tk.StringVar(value=c["quality"]),
            "max_fps": tk.IntVar(value=int(c["max_fps"])),
            "vsync": tk.BooleanVar(value=bool(c["vsync"])),
            "fov": tk.IntVar(value=int(c["fov"])),
            "sensitivity": tk.DoubleVar(value=float(c["sensitivity"])),
            "game_path": tk.StringVar(value=c["game_path"]),
            "game_args": tk.StringVar(value=c["game_args"]),
            "close_on_launch": tk.BooleanVar(value=bool(c["close_on_launch"])),
            "auto_update": tk.BooleanVar(value=bool(c["auto_update"])),
        }

    def log(self, message, level="info"):
        stamp = datetime.now().strftime("%H:%M:%S")
        tag = {"info": "info", "warn": "warn", "error": "error", "ok": "ok"}[level]
        self.log_box.write("[%s] " % stamp, "time")
        self.log_box.write(message + "\n", tag)
        self.log_box.text.see("end")

    def set_status(self, text, color=T.MUTED):
        self.status_label.configure(text=text, fg=color)

    # ---------------------------------------------------------------- 헤더

    def _build_header(self):
        head = tk.Frame(self, bg=T.PANEL, height=74)
        head.pack(fill="x", side="top")
        head.pack_propagate(False)
        tk.Frame(self, bg=T.ACCENT, height=2).pack(fill="x", side="top")

        logo = tk.Canvas(head, width=190, height=74, bg=T.PANEL,
                         highlightthickness=0)
        logo.pack(side="left", padx=(22, 10))
        logo.create_polygon(0, 54, 12, 22, 20, 22, 8, 54,
                            fill=T.ACCENT, outline=T.ACCENT)
        logo.create_text(26, 34, text="SOVIX", anchor="w", fill=T.TEXT,
                         font=T.font(26, "bold", "display"))
        logo.create_text(28, 55, text="T A C T I C A L   F P S", anchor="w",
                         fill=T.MUTED, font=T.font(7, "bold"))

        self.nav_buttons = {}
        nav = tk.Frame(head, bg=T.PANEL)
        nav.pack(side="left", padx=18)
        for key, text in (("home", "홈"), ("settings", "설정"),
                          ("patch", "패치노트"), ("log", "로그")):
            btn = T.HoverButton(nav, text, command=lambda k=key: self.show_view(k),
                                bg=T.PANEL, hover=T.PANEL_HI, fg=T.MUTED,
                                hover_fg=T.TEXT, pad=(16, 10),
                                font_=T.font(11, "bold"))
            btn.pack(side="left", padx=2)
            self.nav_buttons[key] = btn

        right = tk.Frame(head, bg=T.PANEL)
        right.pack(side="right", padx=22)
        T.label(right, "접속 계정", size=8, fg=T.MUTED).pack(anchor="e")
        self.header_nick = T.label(right, self.cfg["nickname"], size=12,
                                   weight="bold", fg=T.CYAN)
        self.header_nick.pack(anchor="e")

    # ---------------------------------------------------------------- 본문

    def _build_body(self):
        self.body = tk.Frame(self, bg=T.BG)
        self.body.pack(fill="both", expand=True)
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)

        self.views = {
            "home": self._build_home(),
            "settings": self._build_settings(),
            "patch": self._build_patch(),
            "log": self._build_log(),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, key):
        self.views[key].tkraise()
        for name, btn in self.nav_buttons.items():
            if name == key:
                btn.set_colors(bg=T.PANEL_HI, hover=T.PANEL_HI, fg=T.ACCENT,
                               hover_fg=T.ACCENT)
            else:
                btn.set_colors(bg=T.PANEL, hover=T.PANEL_HI, fg=T.MUTED,
                               hover_fg=T.TEXT)

    # ------------------------------------------------------------ 홈 화면

    def _build_home(self):
        page = tk.Frame(self.body, bg=T.BG)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, minsize=320)
        page.rowconfigure(0, weight=1)

        news = T.card(page)
        news.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(18, 10))
        self._fill_news(news.inner)

        side = tk.Frame(page, bg=T.BG)
        side.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=(18, 10))
        self._fill_sidebar(side)

        bar = T.card(page)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew",
                 padx=20, pady=(0, 18))
        self._fill_launchbar(bar.inner)
        return page

    def _fill_news(self, box):
        header = tk.Frame(box, bg=T.PANEL)
        header.pack(fill="x", padx=20, pady=(16, 6))
        T.label(header, "소식", size=14, weight="bold").pack(side="left")
        T.label(header, "sovix.gg/news", size=9, fg=T.MUTED).pack(side="right")
        tk.Frame(box, bg=T.LINE, height=1).pack(fill="x", padx=20)

        wrap = tk.Frame(box, bg=T.PANEL)
        wrap.pack(fill="both", expand=True, padx=20, pady=(4, 16))
        colors = {"시즌": T.ACCENT, "밸런스": T.CYAN,
                  "대회": T.YELLOW, "점검": T.MUTED}
        for item in self.content["news"][:4]:
            row = tk.Frame(wrap, bg=T.PANEL)
            row.pack(fill="x", pady=9, anchor="w")
            tag = item.get("tag", "소식")
            chip = T.label(row, " %s " % tag, size=8, weight="bold",
                           fg=T.BG, bg=colors.get(tag, T.ACCENT))
            chip.pack(side="left", anchor="n", pady=2)
            body = tk.Frame(row, bg=T.PANEL)
            body.pack(side="left", fill="x", expand=True, padx=(10, 0))
            line = tk.Frame(body, bg=T.PANEL)
            line.pack(fill="x")
            T.label(line, item["title"], size=11, weight="bold").pack(side="left")
            T.label(line, item.get("date", ""), size=9,
                    fg=T.MUTED).pack(side="right")
            T.label(body, item.get("body", ""), size=9, fg=T.MUTED,
                    justify="left", wraplength=520).pack(anchor="w", pady=(2, 0))

    def _fill_sidebar(self, side):
        server = T.card(side)
        server.pack(fill="x")
        box = server.inner
        T.label(box, "서버", size=12, weight="bold").pack(anchor="w", padx=18,
                                                          pady=(14, 8))
        region = ttk.Combobox(box, textvariable=self.vars["region"],
                              values=list(REGIONS), state="readonly",
                              font=T.font(10))
        region.pack(fill="x", padx=18)
        region.bind("<<ComboboxSelected>>",
                    lambda _e: (self._persist(), self.refresh_ping()))

        ping_row = tk.Frame(box, bg=T.PANEL)
        ping_row.pack(fill="x", padx=18, pady=(12, 4))
        self.ping_dot = tk.Canvas(ping_row, width=10, height=10, bg=T.PANEL,
                                  highlightthickness=0)
        self.ping_dot.pack(side="left", pady=4)
        self.ping_dot.create_oval(1, 1, 9, 9, fill=T.MUTED, outline="")
        self.ping_label = T.label(ping_row, "상태 확인 중...", size=10, fg=T.MUTED)
        self.ping_label.pack(side="left", padx=8)
        T.HoverButton(ping_row, "새로고침", command=self.refresh_ping,
                      bg=T.PANEL, hover=T.PANEL_HI, fg=T.MUTED, hover_fg=T.CYAN,
                      pad=(8, 3), font_=T.font(9)).pack(side="right")
        T.label(box, "", size=2).pack()

        account = T.card(side)
        account.pack(fill="x", pady=(12, 0))
        box = account.inner
        T.label(box, "플레이어", size=12, weight="bold").pack(anchor="w", padx=18,
                                                              pady=(14, 8))
        entry = tk.Entry(box, textvariable=self.vars["nickname"],
                         font=T.font(11, "bold"), bg=T.PANEL_HI, fg=T.TEXT,
                         insertbackground=T.ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=T.LINE,
                         highlightcolor=T.ACCENT)
        entry.pack(fill="x", padx=18, ipady=7)
        entry.bind("<FocusOut>", lambda _e: self._persist())
        entry.bind("<Return>", lambda _e: self._persist())
        T.label(box, "게임에 표시될 이름입니다.", size=9,
                fg=T.MUTED).pack(anchor="w", padx=18, pady=(6, 14))

        spec = T.card(side)
        spec.pack(fill="x", pady=(12, 0))
        box = spec.inner
        T.label(box, "현재 설정", size=12, weight="bold").pack(anchor="w",
                                                               padx=18, pady=(14, 8))
        self.spec_rows = {}
        for key, title in (("resolution", "해상도"), ("display_mode", "화면"),
                           ("quality", "그래픽"), ("max_fps", "최대 FPS")):
            row = tk.Frame(box, bg=T.PANEL)
            row.pack(fill="x", padx=18, pady=3)
            T.label(row, title, size=10, fg=T.MUTED).pack(side="left")
            value = T.label(row, "", size=10, weight="bold")
            value.pack(side="right")
            self.spec_rows[key] = value
        T.label(box, "", size=2).pack(pady=4)
        self._refresh_spec()

    def _fill_launchbar(self, box):
        box.columnconfigure(0, weight=1)
        left = tk.Frame(box, bg=T.PANEL)
        left.grid(row=0, column=0, sticky="ew", padx=(22, 16), pady=18)
        self.status_label = T.label(left, "준비 완료", size=11, weight="bold",
                                    fg=T.MUTED)
        self.status_label.pack(anchor="w")
        self.progress = ttk.Progressbar(left, style="Sovix.Horizontal.TProgressbar",
                                        mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(10, 6))
        self.detail_label = T.label(left, "설치 버전 v%s" % self.cfg["installed_version"],
                                    size=9, fg=T.MUTED)
        self.detail_label.pack(anchor="w")

        self.play_button = T.HoverButton(box, "게임 시작", command=self._on_play,
                                         bg=T.ACCENT, hover=T.ACCENT_HI,
                                         fg="#140800", hover_fg="#140800",
                                         pad=(54, 20),
                                         font_=T.font(17, "bold", "display"))
        self.play_button.grid(row=0, column=1, padx=(0, 22), pady=18)

    # ---------------------------------------------------------- 설정 화면

    def _build_settings(self):
        scroller = ScrollFrame(self.body)
        page = scroller.inner
        page.columnconfigure(0, weight=1, uniform="col")
        page.columnconfigure(1, weight=1, uniform="col")

        display = T.card(page)
        display.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(18, 10))
        self._fill_display_settings(display.inner)

        gameplay = T.card(page)
        gameplay.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=(18, 10))
        self._fill_gameplay_settings(gameplay.inner)

        bottom = T.card(page)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew",
                    padx=20, pady=(0, 18))
        self._fill_path_settings(bottom.inner)
        return scroller

    def _section(self, box, title):
        T.label(box, title, size=13, weight="bold").pack(anchor="w", padx=20,
                                                         pady=(16, 10))
        tk.Frame(box, bg=T.LINE, height=1).pack(fill="x", padx=20)

    def _combo_row(self, box, title, var, values):
        row = tk.Frame(box, bg=T.PANEL)
        row.pack(fill="x", padx=20, pady=8)
        T.label(row, title, size=10, fg=T.MUTED).pack(anchor="w")
        combo = ttk.Combobox(row, textvariable=var, values=values,
                             state="readonly", font=T.font(10))
        combo.pack(fill="x", pady=(4, 0))
        combo.bind("<<ComboboxSelected>>", lambda _e: self._persist())
        return combo

    def _toggle_row(self, box, title, desc, var):
        row = tk.Frame(box, bg=T.PANEL)
        row.pack(fill="x", padx=20, pady=8)
        text = tk.Frame(row, bg=T.PANEL)
        text.pack(side="left", fill="x", expand=True)
        T.label(text, title, size=10, weight="bold").pack(anchor="w")
        T.label(text, desc, size=9, fg=T.MUTED).pack(anchor="w")
        Toggle(row, var, command=self._persist).pack(side="right")

    def _fill_display_settings(self, box):
        self._section(box, "디스플레이")
        self._combo_row(box, "해상도", self.vars["resolution"], RESOLUTIONS)
        self._combo_row(box, "화면 모드", self.vars["display_mode"], DISPLAY_MODES)
        self._combo_row(box, "그래픽 품질", self.vars["quality"], QUALITIES)
        ValueSlider(box, "최대 FPS", self.vars["max_fps"], 30, 360, step=1,
                    command=self._persist).pack(fill="x", padx=20, pady=(10, 4))
        self._toggle_row(box, "수직 동기화", "화면 찢어짐을 줄이지만 입력 지연이 늘어납니다.",
                         self.vars["vsync"])
        T.label(box, "", size=2).pack(pady=6)

    def _fill_gameplay_settings(self, box):
        self._section(box, "게임플레이")
        ValueSlider(box, "시야각 (FOV)", self.vars["fov"], 70, 120, step=1,
                    command=self._persist).pack(fill="x", padx=20, pady=(14, 4))
        ValueSlider(box, "마우스 감도", self.vars["sensitivity"], 0.1, 10.0,
                    step=0.1, fmt="{:.1f}",
                    command=self._persist).pack(fill="x", padx=20, pady=(10, 4))
        self._toggle_row(box, "자동 업데이트", "실행 전에 새 패치를 자동으로 내려받습니다.",
                         self.vars["auto_update"])
        self._toggle_row(box, "실행 후 런처 닫기", "게임이 시작되면 런처를 종료합니다.",
                         self.vars["close_on_launch"])
        T.label(box, "", size=2).pack(pady=6)

    def _fill_path_settings(self, box):
        self._section(box, "실행 설정")
        row = tk.Frame(box, bg=T.PANEL)
        row.pack(fill="x", padx=20, pady=(10, 4))
        T.label(row, "게임 실행 파일", size=10, fg=T.MUTED).pack(anchor="w")
        picker = tk.Frame(row, bg=T.PANEL)
        picker.pack(fill="x", pady=(4, 0))
        entry = tk.Entry(picker, textvariable=self.vars["game_path"],
                         font=T.font(10, kind="mono"), bg=T.PANEL_HI, fg=T.TEXT,
                         insertbackground=T.ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=T.LINE,
                         highlightcolor=T.ACCENT)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<FocusOut>", lambda _e: self._persist())
        T.HoverButton(picker, "찾아보기", command=self._browse_game,
                      bg=T.PANEL_HI, hover=T.LINE, pad=(14, 7),
                      font_=T.font(9, "bold")).pack(side="left", padx=(8, 0))
        T.label(row, "비워두면 동봉된 데모 빌드(demo_game.py)가 실행됩니다.",
                size=9, fg=T.MUTED).pack(anchor="w", pady=(5, 0))

        args_row = tk.Frame(box, bg=T.PANEL)
        args_row.pack(fill="x", padx=20, pady=(8, 4))
        T.label(args_row, "추가 실행 인자", size=10, fg=T.MUTED).pack(anchor="w")
        args_entry = tk.Entry(args_row, textvariable=self.vars["game_args"],
                              font=T.font(10, kind="mono"), bg=T.PANEL_HI,
                              fg=T.TEXT, insertbackground=T.ACCENT, relief="flat",
                              highlightthickness=1, highlightbackground=T.LINE,
                              highlightcolor=T.ACCENT)
        args_entry.pack(fill="x", pady=(4, 0), ipady=6)
        args_entry.bind("<FocusOut>", lambda _e: self._persist())

        T.label(box, "실행 명령 미리보기", size=10, fg=T.MUTED).pack(anchor="w",
                                                                     padx=20,
                                                                     pady=(10, 4))
        self.preview = T.label(box, "", size=9, fg=T.CYAN, bg=T.PANEL_HI,
                               justify="left", wraplength=940, anchor="w",
                               font=T.font(9, kind="mono"))
        self.preview.pack(fill="x", padx=20, ipady=10, ipadx=10)
        self.preview.bind("<Configure>", lambda e: self.preview.configure(
            wraplength=max(200, e.width - 24)))

        actions = tk.Frame(box, bg=T.PANEL)
        actions.pack(fill="x", padx=20, pady=14)
        T.label(actions, "설정 파일: %s" % self.cfg.path, size=9,
                fg=T.MUTED).pack(side="left")
        T.HoverButton(actions, "기본값으로", command=self._reset_defaults,
                      bg=T.PANEL_HI, hover=T.LINE, fg=T.MUTED, hover_fg=T.TEXT,
                      pad=(14, 8), font_=T.font(9, "bold")).pack(side="right")
        T.HoverButton(actions, "저장", command=lambda: self._persist(toast=True),
                      bg=T.CYAN, hover="#5af0e3", fg="#06201d", hover_fg="#06201d",
                      pad=(22, 8), font_=T.font(9, "bold")).pack(side="right",
                                                                 padx=8)
        self._refresh_preview()

    # ------------------------------------------------------ 패치노트 / 로그

    def _build_patch(self):
        page = tk.Frame(self.body, bg=T.BG)
        holder = T.card(page)
        holder.pack(fill="both", expand=True, padx=20, pady=18)
        box = holder.inner
        self._section(box, "패치노트")
        view = ScrollText(box)
        view.pack(fill="both", expand=True, padx=6, pady=(6, 10))
        txt = view.text
        txt.tag_configure("ver", foreground=T.ACCENT,
                          font=T.font(15, "bold", "display"), spacing3=2)
        txt.tag_configure("date", foreground=T.MUTED, font=T.font(9), spacing3=10)
        txt.tag_configure("sec", foreground=T.CYAN, font=T.font(11, "bold"),
                          spacing1=10, spacing3=4)
        txt.tag_configure("item", foreground=T.TEXT, font=T.font(10),
                          lmargin1=16, lmargin2=30, spacing3=2)

        for note in self.content["patch_notes"]:
            view.write("v%s\n" % note["version"], "ver")
            view.write("%s 적용\n" % note.get("date", ""), "date")
            for title, items in note.get("sections", []):
                view.write("%s\n" % title, "sec")
                for line in items:
                    view.write("•  %s\n" % line, "item")
            view.write("\n" + "─" * 70 + "\n\n", "date")
        return page

    def _build_log(self):
        page = tk.Frame(self.body, bg=T.BG)
        holder = T.card(page)
        holder.pack(fill="both", expand=True, padx=20, pady=18)
        box = holder.inner
        head = tk.Frame(box, bg=T.PANEL)
        head.pack(fill="x", padx=20, pady=(16, 10))
        T.label(head, "실행 로그", size=13, weight="bold").pack(side="left")
        T.HoverButton(head, "지우기", command=lambda: self.log_box.clear(),
                      bg=T.PANEL_HI, hover=T.LINE, fg=T.MUTED, hover_fg=T.TEXT,
                      pad=(12, 5), font_=T.font(9, "bold")).pack(side="right")
        tk.Frame(box, bg=T.LINE, height=1).pack(fill="x", padx=20)

        self.log_box = ScrollText(box, bg=T.PANEL, font_=T.font(9, kind="mono"))
        self.log_box.pack(fill="both", expand=True, padx=6, pady=(6, 10))
        txt = self.log_box.text
        txt.tag_configure("time", foreground=T.LINE)
        txt.tag_configure("info", foreground=T.TEXT)
        txt.tag_configure("ok", foreground=T.GREEN)
        txt.tag_configure("warn", foreground=T.YELLOW)
        txt.tag_configure("error", foreground=T.RED)
        return page

    # ---------------------------------------------------------------- 푸터

    def _build_footer(self):
        foot = tk.Frame(self, bg=T.PANEL, height=30)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        self.foot_left = T.label(foot, "SOVIX Launcher v%s" % LAUNCHER_VERSION,
                                 size=9, fg=T.MUTED)
        self.foot_left.pack(side="left", padx=20)
        self.foot_right = T.label(foot, "", size=9, fg=T.MUTED)
        self.foot_right.pack(side="right", padx=20)
        self._refresh_footer()

    def _refresh_footer(self):
        self.foot_right.configure(
            text="클라이언트 v%s   ·   최신 v%s"
                 % (self.cfg["installed_version"], self.content["latest_version"]))

    # ---------------------------------------------------------- 설정 반영

    def _persist(self, toast=False):
        for key, var in self.vars.items():
            self.cfg[key] = var.get()
        try:
            self.cfg.save()
        except OSError as exc:
            self.log("설정 저장 실패: %s" % exc, "error")
            return
        self.header_nick.configure(text=self.cfg["nickname"] or "Operator")
        self._refresh_spec()
        self._refresh_preview()
        if toast:
            self.log("설정을 저장했습니다.", "ok")
            self.set_status("설정 저장됨", T.GREEN)
            self.after(1800, lambda: self.set_status("준비 완료", T.MUTED))

    def _refresh_spec(self):
        if not hasattr(self, "spec_rows"):
            return
        self.spec_rows["resolution"].configure(text=self.vars["resolution"].get())
        self.spec_rows["display_mode"].configure(text=self.vars["display_mode"].get())
        self.spec_rows["quality"].configure(text=self.vars["quality"].get())
        self.spec_rows["max_fps"].configure(
            text="%d%s" % (self.vars["max_fps"].get(),
                           " · VSync" if self.vars["vsync"].get() else ""))

    def _refresh_preview(self):
        if not hasattr(self, "preview"):
            return
        try:
            command, is_demo = services.resolve_executable(self.cfg)
            target = "데모 빌드" if is_demo else command[0]
        except FileNotFoundError as exc:
            target = "(경로 없음: %s)" % exc
        args = " ".join(services.build_launch_args(self.cfg))
        self.preview.configure(text="%s %s" % (target, args))

    def _browse_game(self):
        path = filedialog.askopenfilename(
            title="SOVIX 실행 파일 선택",
            filetypes=[("실행 파일", "*.exe *.app *.sh *.x86_64 *"), ("모든 파일", "*")])
        if path:
            self.vars["game_path"].set(path)
            self._persist()
            self.log("게임 경로 설정: %s" % path)

    def _reset_defaults(self):
        if not messagebox.askyesno("기본값 복원", "모든 설정을 기본값으로 되돌릴까요?"):
            return
        from .config import DEFAULTS
        keep = self.cfg["installed_version"]
        for key, value in DEFAULTS.items():
            if key in self.vars:
                self.vars[key].set(value)
        self.cfg["installed_version"] = keep
        self._persist(toast=True)

    # ------------------------------------------------------------ 백그라운드

    def _pump(self):
        """워커 스레드가 넣은 이벤트를 UI 스레드에서 처리한다."""
        try:
            while True:
                kind, payload = self.events.get_nowait()
                handler = getattr(self, "_on_" + kind, None)
                if handler:
                    handler(payload)
        except queue.Empty:
            pass
        self.after(60, self._pump)

    def post(self, kind, payload=None):
        self.events.put((kind, payload))

    def refresh_ping(self):
        if self._ping_job:
            self.after_cancel(self._ping_job)
        region = self.vars["region"].get()
        self.ping_label.configure(text="%s 확인 중..." % region, fg=T.MUTED)
        threading.Thread(target=self._ping_worker, args=(region,),
                         daemon=True).start()
        self._ping_job = self.after(PING_INTERVAL_MS, self.refresh_ping)

    def _ping_worker(self, region):
        ms = services.tcp_ping(region)
        self.post("ping", (region, ms))

    def _on_ping(self, payload):
        region, ms = payload
        if region != self.vars["region"].get():
            return
        self.ping_dot.delete("all")
        if ms is None:
            color, text = T.RED, "%s · 응답 없음" % region
        elif ms < 60:
            color, text = T.GREEN, "%s · %d ms" % (region, ms)
        elif ms < 140:
            color, text = T.YELLOW, "%s · %d ms" % (region, ms)
        else:
            color, text = T.RED, "%s · %d ms" % (region, ms)
        self.ping_dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        self.ping_label.configure(text=text, fg=color)

    def _on_log(self, payload):
        message, level = payload
        self.log(message, level)

    def _on_progress(self, payload):
        percent, detail = payload
        self.progress["value"] = percent
        self.detail_label.configure(text=detail)

    def _on_phase(self, payload):
        text, color = payload
        self.set_status(text, color)

    def _on_finished(self, payload):
        ok, message = payload
        self.busy = False
        self.play_button.configure(text="게임 시작")
        self.play_button.set_enabled(True)
        self.progress["value"] = 0
        self._refresh_footer()
        if ok:
            self.set_status("실행됨", T.GREEN)
            self.detail_label.configure(text=message)
            if self.vars["close_on_launch"].get():
                self.after(1200, self.destroy)
        else:
            self.set_status("실행 실패", T.RED)
            self.detail_label.configure(text=message)

    # ------------------------------------------------------------ 실행 흐름

    def _initial_check(self):
        self.log("SOVIX 런처 v%s 시작" % LAUNCHER_VERSION)
        self.log("설정 파일: %s" % self.cfg.path)
        latest = self.content["latest_version"]
        if services.needs_update(self.cfg["installed_version"], latest):
            self.set_status("업데이트 필요", T.YELLOW)
            self.detail_label.configure(
                text="v%s → v%s  (%d MB)" % (self.cfg["installed_version"], latest,
                                             self.content["patch_size_mb"]))
            self.play_button.configure(text="업데이트")
            self.log("새 패치 v%s 를 찾았습니다." % latest, "warn")
        else:
            self.set_status("준비 완료", T.GREEN)
            self.log("클라이언트가 최신 버전입니다. (v%s)" % latest, "ok")

    def _on_play(self):
        if self.busy:
            return
        self._persist()
        self.busy = True
        self._cancel = False
        self.play_button.set_enabled(False)
        self.play_button.configure(text="진행 중")
        threading.Thread(target=self._play_worker, daemon=True).start()

    def _play_worker(self):
        latest = self.content["latest_version"]
        if (self.vars["auto_update"].get()
                and services.needs_update(self.cfg["installed_version"], latest)):
            self.post("phase", ("업데이트 중", T.YELLOW))
            self.post("log", ("패치 v%s 적용 시작" % latest, "info"))
            ok = services.run_patch(
                latest, self.content["patch_size_mb"],
                lambda pct, text: self.post("progress", (pct, text)),
                lambda: self._cancel)
            if not ok:
                self.post("finished", (False, "업데이트가 취소되었습니다."))
                return
            self.cfg["installed_version"] = latest
            try:
                self.cfg.save()
            except OSError as exc:
                self.post("log", ("버전 기록 실패: %s" % exc, "warn"))
            self.post("log", ("패치 완료 — v%s" % latest, "ok"))

        self.post("phase", ("게임 실행 중", T.CYAN))
        self.post("progress", (100, "클라이언트를 실행하는 중..."))
        try:
            proc, command, is_demo = services.launch_game(self.cfg)
        except FileNotFoundError as exc:
            self.post("log", ("실행 파일을 찾을 수 없습니다: %s" % exc, "error"))
            self.post("finished", (False, "실행 파일 경로를 확인하세요."))
            return
        except PermissionError as exc:
            self.post("log", ("실행 권한이 없습니다: %s" % exc, "error"))
            self.post("finished", (False, "실행 권한을 확인하세요. (chmod +x)"))
            return
        except OSError as exc:
            self.post("log", ("실행 실패: %s" % exc, "error"))
            self.post("finished", (False, str(exc)))
            return

        self._game_proc = proc
        self.post("log", ("실행: %s" % " ".join(command), "ok"))
        time.sleep(0.6)
        if proc.poll() not in (None, 0):
            self.post("log", ("게임이 코드 %s 로 즉시 종료됐습니다." % proc.poll(), "error"))
            self.post("finished", (False, "게임이 바로 종료됐습니다. 로그를 확인하세요."))
            return
        label = "데모 빌드 실행 중 (PID %d)" if is_demo else "게임 실행 중 (PID %d)"
        self.post("finished", (True, label % proc.pid))

    def _on_close(self):
        self._cancel = True
        try:
            self._persist()
        except Exception:
            pass
        self.destroy()


def main():
    app = LauncherApp()
    app.mainloop()
