"""색상 팔레트, 폰트, ttk 스타일, 공용 위젯."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

BG = "#0a0d12"
PANEL = "#12171f"
PANEL_HI = "#1a212c"
LINE = "#242d3a"
TEXT = "#e8edf4"
MUTED = "#7d8899"
ACCENT = "#ff5a1f"
ACCENT_HI = "#ff7a44"
CYAN = "#2ee6d6"
GREEN = "#43d17c"
RED = "#ef4b55"
YELLOW = "#f5b73d"

_FAMILIES = {"display": "Arial", "ui": "Arial", "mono": "Courier"}


def init_fonts(root):
    """설치된 폰트 중 가장 보기 좋은 조합을 고른다."""
    available = {f.lower() for f in tkfont.families(root)}

    def pick(candidates, fallback):
        for name in candidates:
            if name.lower() in available:
                return name
        return fallback

    _FAMILIES["display"] = pick(
        ["Bahnschrift", "Oswald", "Impact", "DejaVu Sans", "Segoe UI", "Helvetica"], "Arial")
    _FAMILIES["ui"] = pick(
        ["Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans CJK KR", "NanumGothic",
         "Segoe UI", "DejaVu Sans", "Helvetica"], "Arial")
    _FAMILIES["mono"] = pick(
        ["Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"], "Courier")


def font(size=10, weight="normal", kind="ui"):
    return (_FAMILIES[kind], size, weight)


def apply_styles(root):
    """다크 테마용 ttk 스타일 등록."""
    init_fonts(root)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TCombobox", fieldbackground=PANEL_HI, background=PANEL_HI,
                    foreground=TEXT, arrowcolor=MUTED, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, selectbackground=PANEL_HI,
                    selectforeground=TEXT, padding=6)
    style.map("TCombobox",
              fieldbackground=[("readonly", PANEL_HI)],
              bordercolor=[("focus", ACCENT)],
              arrowcolor=[("active", ACCENT)])
    root.option_add("*TCombobox*Listbox.background", PANEL_HI)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#0a0d12")
    root.option_add("*TCombobox*Listbox.font", font(10))

    style.configure("Sovix.Horizontal.TProgressbar", troughcolor=PANEL_HI,
                    background=ACCENT, bordercolor=PANEL_HI,
                    lightcolor=ACCENT, darkcolor=ACCENT, thickness=6)

    style.configure("Sovix.Horizontal.TScale", troughcolor=PANEL_HI,
                    background=ACCENT, bordercolor=PANEL, lightcolor=ACCENT,
                    darkcolor=ACCENT, sliderlength=14, sliderthickness=14,
                    troughrelief="flat", gripcount=0)
    style.map("Sovix.Horizontal.TScale", background=[("active", ACCENT_HI)])

    style.configure("Sovix.Vertical.TScrollbar", troughcolor=BG, background=LINE,
                    bordercolor=BG, arrowcolor=MUTED, lightcolor=LINE, darkcolor=LINE)
    style.map("Sovix.Vertical.TScrollbar", background=[("active", MUTED)])
    return style


class HoverButton(tk.Label):
    """Label 기반 커스텀 버튼 — 색을 완전히 제어하기 위해 tk.Button 대신 사용."""

    def __init__(self, master, text, command=None, *, bg=PANEL_HI, hover=LINE,
                 fg=TEXT, hover_fg=None, pad=(16, 9), font_=None, **kw):
        super().__init__(master, text=text, bg=bg, fg=fg,
                         font=font_ or font(10, "bold"),
                         padx=pad[0], pady=pad[1], cursor="hand2", **kw)
        self._bg, self._hover = bg, hover
        self._fg, self._hover_fg = fg, hover_fg or fg
        self._command = command
        self._enabled = True
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, _=None):
        if self._enabled:
            self.configure(bg=self._hover, fg=self._hover_fg)

    def _on_leave(self, _=None):
        if self._enabled:
            self.configure(bg=self._bg, fg=self._fg)

    def _on_click(self, _=None):
        if self._enabled and self._command:
            self._command()

    def set_colors(self, bg=None, hover=None, fg=None, hover_fg=None):
        self._bg = bg or self._bg
        self._hover = hover or self._hover
        self._fg = fg or self._fg
        self._hover_fg = hover_fg or self._hover_fg
        self.configure(bg=self._bg, fg=self._fg)

    def set_enabled(self, flag):
        self._enabled = flag
        self.configure(bg=self._bg if flag else PANEL_HI,
                       fg=self._fg if flag else MUTED,
                       cursor="hand2" if flag else "arrow")


def card(master, **kw):
    """패널 배경 + 얇은 테두리를 가진 프레임."""
    outer = tk.Frame(master, bg=LINE, **kw)
    inner = tk.Frame(outer, bg=PANEL)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    outer.inner = inner
    return outer


def label(master, text, size=10, weight="normal", fg=TEXT, bg=PANEL, **kw):
    kw.setdefault("font", font(size, weight))
    return tk.Label(master, text=text, fg=fg, bg=bg, **kw)
