#!/usr/bin/env python3
"""실제 게임 빌드가 나오기 전까지 런처 연동을 확인하는 데모 클라이언트.

런처가 넘긴 실행 인자를 화면에 보여준다. ESC로 종료.
"""

import sys
import tkinter as tk


def parse_args(argv):
    opts = {}
    for arg in argv:
        if arg.startswith("-"):
            key, _, value = arg[1:].partition("=")
            opts[key] = value or "on"
    return opts


def main():
    opts = parse_args(sys.argv[1:])
    root = tk.Tk()
    root.title("SOVIX")
    root.configure(bg="#05070a")
    w, h = int(opts.get("ResX", 1280)), int(opts.get("ResY", 720))
    w, h = min(w, root.winfo_screenwidth()), min(h, root.winfo_screenheight())
    root.geometry("%dx%d" % (min(w, 1280), min(h, 720)))
    root.bind("<Escape>", lambda _e: root.destroy())

    canvas = tk.Canvas(root, bg="#05070a", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    def draw(_e=None):
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        cx, cy = cw // 2, ch // 2
        for x in range(0, cw, 40):
            canvas.create_line(x, 0, x, ch, fill="#0d1218")
        for y in range(0, ch, 40):
            canvas.create_line(0, y, cw, y, fill="#0d1218")
        canvas.create_text(cx, cy - 70, text="SOVIX", fill="#e8edf4",
                           font=("Arial", 54, "bold"))
        canvas.create_text(cx, cy - 22, text="DEMO CLIENT — 런처 연동 확인용",
                           fill="#ff5a1f", font=("Arial", 12, "bold"))
        # 조준점
        for dx, dy in ((-18, 0), (18, 0), (0, -18), (0, 18)):
            canvas.create_line(cx + dx * 0.4, cy + 40 + dy * 0.4,
                               cx + dx, cy + 40 + dy, fill="#2ee6d6", width=2)
        lines = ["%s = %s" % (k, v) for k, v in opts.items()]
        canvas.create_text(24, ch - 24, anchor="sw", fill="#7d8899",
                           font=("Courier", 10), text="\n".join(lines))
        canvas.create_text(cw - 24, ch - 24, anchor="se", fill="#7d8899",
                           font=("Arial", 10), text="ESC 로 종료")

    canvas.bind("<Configure>", draw)
    root.mainloop()


if __name__ == "__main__":
    main()
