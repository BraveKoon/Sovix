"""런처 전용 복합 위젯."""

import tkinter as tk
from tkinter import ttk

from . import theme as T


class Toggle(tk.Frame):
    """ON/OFF 스위치. tk.Checkbutton 대신 색을 직접 제어한다."""

    def __init__(self, master, variable, command=None, bg=T.PANEL):
        super().__init__(master, bg=bg)
        self.var = variable
        self.command = command
        self.canvas = tk.Canvas(self, width=46, height=24, bg=bg,
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._toggle)
        self.var.trace_add("write", lambda *_: self._redraw())
        self._redraw()

    def _toggle(self, _=None):
        self.var.set(not self.var.get())
        if self.command:
            self.command()

    def _redraw(self):
        on = bool(self.var.get())
        c = self.canvas
        c.delete("all")
        track = T.ACCENT if on else T.LINE
        c.create_oval(1, 3, 19, 21, fill=track, outline=track)
        c.create_oval(25, 3, 43, 21, fill=track, outline=track)
        c.create_rectangle(10, 3, 34, 21, fill=track, outline=track)
        x = 34 if on else 10
        knob = "#0a0d12" if on else T.MUTED
        c.create_oval(x - 8, 4, x + 8, 20, fill=knob, outline=knob)


class ValueSlider(tk.Frame):
    """제목 + 현재값 + 슬라이더를 묶은 행."""

    def __init__(self, master, text, variable, lo, hi, *, fmt="{:.0f}",
                 step=1, command=None, bg=T.PANEL):
        super().__init__(master, bg=bg)
        self.var = variable
        self.fmt = fmt
        self.step = step
        self.command = command
        # ttk.Scale은 실수를 쓰므로 내부 DoubleVar로 받고 step 단위로 반올림해 넘긴다.
        self._raw = tk.DoubleVar(value=variable.get())

        head = tk.Frame(self, bg=bg)
        head.pack(fill="x")
        T.label(head, text, size=10, fg=T.MUTED, bg=bg).pack(side="left")
        self.value_label = T.label(head, "", size=10, weight="bold",
                                   fg=T.TEXT, bg=bg)
        self.value_label.pack(side="right")

        self.scale = ttk.Scale(self, from_=lo, to=hi, orient="horizontal",
                               variable=self._raw, command=self._on_move,
                               style="Sovix.Horizontal.TScale")
        self.scale.pack(fill="x", pady=(6, 0))
        self.var.trace_add("write", lambda *_: self._sync_from_var())
        self._refresh()

    def _on_move(self, _value):
        value = round(self._raw.get() / self.step) * self.step
        value = int(round(value)) if isinstance(self.var, tk.IntVar) else round(value, 2)
        if value != self.var.get():
            self.var.set(value)
            if self.command:
                self.command()

    def _sync_from_var(self):
        if abs(self._raw.get() - self.var.get()) >= self.step:
            self._raw.set(self.var.get())
        self._refresh()

    def _refresh(self):
        self.value_label.configure(text=self.fmt.format(self.var.get()))


class ScrollFrame(tk.Frame):
    """세로 스크롤 가능한 컨테이너. 자식은 .inner 에 넣는다."""

    def __init__(self, master, bg=T.BG):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                            style="Sovix.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window(0, 0, window=self.inner,
                                                 anchor="nw")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._window, width=e.width))
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)

    def _bind_wheel(self, _=None):
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.bind_all("<Button-4>", lambda _e: self._scroll(-1))
        self.bind_all("<Button-5>", lambda _e: self._scroll(1))

    def _unbind_wheel(self, _=None):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.unbind_all(seq)

    def _on_wheel(self, event):
        step = -1 if event.delta > 0 else 1
        self._scroll(step if abs(event.delta) < 120 else step * (abs(event.delta) // 120))

    def _scroll(self, units):
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(units) * 3, "units")


class ScrollText(tk.Frame):
    """스크롤바가 붙은 읽기 전용 텍스트 영역."""

    def __init__(self, master, bg=T.PANEL, font_=None, padx=18, pady=14):
        super().__init__(master, bg=bg)
        self.text = tk.Text(self, bg=bg, fg=T.TEXT, bd=0, highlightthickness=0,
                            wrap="word", padx=padx, pady=pady, spacing1=2,
                            spacing3=4, font=font_ or T.font(10),
                            insertbackground=T.ACCENT, cursor="arrow")
        bar = tk.Scrollbar(self, command=self.text.yview, bg=T.PANEL_HI,
                           troughcolor=bg, activebackground=T.MUTED,
                           bd=0, highlightthickness=0, width=10,
                           relief="flat", elementborderwidth=0)
        self.text.configure(yscrollcommand=bar.set)
        self.text.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

    def write(self, content, tag=None):
        self.text.configure(state="normal")
        self.text.insert("end", content, tag or ())
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
