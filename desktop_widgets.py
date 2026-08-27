#!/usr/bin/env python3
"""Frameless always-on-top desktop widgets for Windows (tkinter + Pillow)."""

from __future__ import annotations

import json
import math
import sys
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    sys.stderr.write(
        "Pillow is missing.\n"
        "In this folder run:\n"
        "  py -3 -m pip install pillow\n"
        "then double-click start-widgets.bat again.\n"
    )
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STORE = Path.home() / "AppData" / "Local" / "HelloDolly" / "layout.json"
if sys.platform != "win32":
    STORE = ROOT / "layout.json"

MAGENTA = "#ff00aa"
PLAY_DIR = ASSETS / "play"
FASTBACK_DIR = ASSETS / "fastback"
STILLS = [
    ASSETS / "dolly-glam.png",
    ASSETS / "dolly-dance.png",
]
LOOK_NAMES = ["Guitar", "Glam", "Cowgirl"]
QUOTES = [
    "If you want the rainbow, you gotta put up with the rain.",
    "Find out who you are and do it on purpose.",
    "It costs a lot of money to look this cheap.",
    "Don't get so busy making a living that you forget to make a life.",
    "If you don't like the road you're walking, start paving another one.",
    "We cannot direct the wind, but we can adjust the sails.",
    "You'll never do a whole lot unless you're brave enough to try.",
    "Storms make trees take deeper roots.",
]
NOTE_COLORS = ["#f7f1e6", "#e8dcc8", "#d4c4b0", "#f3e6ea"]


def load_layout() -> dict:
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_layout(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class DragMixin:
    _dx = 0
    _dy = 0
    dragging = False

    def enable_drag(self, *widgets: tk.Misc) -> None:
        for widget in widgets + (self,):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<ButtonRelease-1>", self._drag_end)

    def _drag_start(self, event: tk.Event) -> None:
        self.dragging = True
        self._dx = event.x_root - self.winfo_x()
        self._dy = event.y_root - self.winfo_y()

    def _drag_move(self, event: tk.Event) -> None:
        self.geometry(f"+{event.x_root - self._dx}+{event.y_root - self._dy}")

    def _drag_end(self, _event: tk.Event) -> None:
        self.dragging = False
        if hasattr(self, "persist"):
            self.persist()


class WidgetWindow(tk.Toplevel, DragMixin):
    key: str = "widget"

    def __init__(self, master: tk.Tk, x: int = 80, y: int = 80) -> None:
        super().__init__(master)
        self.master = master
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.geometry(f"+{x}+{y}")
        self.bind("<Escape>", lambda _e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def persist(self) -> None:
        data = load_layout()
        data[self.key] = {"x": self.winfo_x(), "y": self.winfo_y()}
        extra = getattr(self, "persist_extra", None)
        if extra:
            data[self.key].update(extra())
        save_layout(data)


class DollyWidget(WidgetWindow):
    key = "dolly"

    def __init__(self, master: tk.Tk, x: int = 200, y: int = 80, look: int = 0) -> None:
        super().__init__(master, x, y)
        self.look = look % len(LOOK_NAMES)
        self._t = 0.0
        self._frame = 0
        self._photo = None
        self._play: list[ImageTk.PhotoImage] = []
        self.configure(bg=MAGENTA)
        if sys.platform == "win32":
            self.wm_attributes("-transparentcolor", MAGENTA)
        self.label = tk.Label(self, bd=0, highlightthickness=0, bg=MAGENTA)
        self.label.pack()
        self.enable_drag(self.label)
        self.label.bind("<Button-3>", self._menu)
        self.bind("<Button-3>", self._menu)
        self.label.bind("<Double-Button-1>", lambda _e: self.destroy())
        self._load_play()
        self._paint()
        self.after(120, self._tick)

    def persist_extra(self) -> dict:
        return {"look": self.look}

    def _load_play(self) -> None:
        frames = sorted(PLAY_DIR.glob("*.png"))
        self._play = [ImageTk.PhotoImage(Image.open(p).convert("RGB")) for p in frames]

    def _paint(self) -> None:
        if self.look == 0 and self._play:
            self._photo = self._play[self._frame % len(self._play)]
            self.label.configure(image=self._photo)
            return
        stills = [p for p in STILLS if p.exists()]
        idx = max(0, self.look - 1) % max(1, len(stills))
        path = stills[idx] if stills else None
        if path is None:
            return
        self._photo = ImageTk.PhotoImage(Image.open(path).convert("RGB"))
        self.label.configure(image=self._photo)

    def _cycle(self) -> None:
        self.look = (self.look + 1) % len(LOOK_NAMES)
        self._frame = 0
        self._paint()
        self.persist()

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label=f"Switch look ({LOOK_NAMES[self.look]})",
            command=self._cycle,
        )
        menu.add_command(label="Close Dolly", command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def _tick(self) -> None:
        if not self.winfo_exists():
            return
        if self.look == 0 and self._play:
            self._frame = (self._frame + 1) % len(self._play)
            self._photo = self._play[self._frame]
            self.label.configure(image=self._photo)
        elif not self.dragging:
            self._t += 0.18
            y = self.winfo_y()
            if not hasattr(self, "_base_y"):
                self._base_y = y
            if abs(y - self._base_y) < 12:
                ny = self._base_y + int(round(3 * math.sin(self._t)))
                self.geometry(f"+{self.winfo_x()}+{ny}")
            else:
                self._base_y = y
        else:
            self._base_y = self.winfo_y()
        self.after(120, self._tick)


class FastbackWidget(WidgetWindow):
    key = "fastback"

    def __init__(self, master: tk.Tk, x: int = 80, y: int = 360) -> None:
        super().__init__(master, x, y)
        self._frame = 0
        self._photo = None
        self._play: list[ImageTk.PhotoImage] = []
        self.configure(bg=MAGENTA)
        if sys.platform == "win32":
            self.wm_attributes("-transparentcolor", MAGENTA)
        self.label = tk.Label(self, bd=0, highlightthickness=0, bg=MAGENTA)
        self.label.pack()
        self.enable_drag(self.label)
        self.label.bind("<Button-3>", self._menu)
        self.bind("<Button-3>", self._menu)
        self.label.bind("<Double-Button-1>", lambda _e: self.destroy())
        frames = sorted(FASTBACK_DIR.glob("*.png"))
        self._play = [ImageTk.PhotoImage(Image.open(p).convert("RGB")) for p in frames]
        if self._play:
            self._photo = self._play[0]
            self.label.configure(image=self._photo)
        self.after(90, self._tick)

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Close Fastback", command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def _tick(self) -> None:
        if not self.winfo_exists() or not self._play:
            return
        self._frame = (self._frame + 1) % len(self._play)
        self._photo = self._play[self._frame]
        self.label.configure(image=self._photo)
        self.after(90, self._tick)


class ClockWidget(WidgetWindow):
    key = "clock"

    def __init__(self, master: tk.Tk, x: int = 40, y: int = 40) -> None:
        super().__init__(master, x, y)
        self.configure(bg="#1e1b24")
        frame = tk.Frame(self, bg="#1e1b24", padx=16, pady=12)
        frame.pack()
        self.time_lbl = tk.Label(
            frame, text="", fg="#f4f0e8", bg="#1e1b24",
            font=("Segoe UI", 22, "bold"),
        )
        self.date_lbl = tk.Label(
            frame, text="", fg="#b7b0a6", bg="#1e1b24", font=("Segoe UI", 10)
        )
        self.time_lbl.pack()
        self.date_lbl.pack()
        self.enable_drag(frame, self.time_lbl, self.date_lbl)
        self.bind("<Button-3>", self._menu)
        self._tick()

    def _tick(self) -> None:
        if not self.winfo_exists():
            return
        import datetime as dt

        now = dt.datetime.now()
        self.time_lbl.configure(text=now.strftime("%I:%M %p").lstrip("0"))
        self.date_lbl.configure(text=now.strftime("%A, %b %d"))
        self.after(1000, self._tick)

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Close clock", command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)


class NoteWidget(WidgetWindow):
    key = "note"

    def __init__(self, master: tk.Tk, x: int = 520, y: int = 80, color: int = 0, text: str = "") -> None:
        super().__init__(master, x, y)
        self.color_i = color % len(NOTE_COLORS)
        self.text = tk.Text(
            self, width=22, height=8, wrap="word", bd=0, padx=12, pady=12,
            font=("Segoe UI", 11), fg="#2a241c",
        )
        self.text.insert("1.0", text or "Leave the guitar in A.\nBoots stay on.")
        self.text.pack()
        self._skin()
        self.enable_drag()
        self.text.bind("<ButtonPress-1>", self._drag_start)
        self.text.bind("<B1-Motion>", self._drag_move)
        self.text.bind("<ButtonRelease-1>", self._drag_end)
        self.text.bind("<KeyRelease>", lambda _e: self.persist())
        self.bind("<Button-3>", self._menu)
        self.text.bind("<Button-3>", self._menu)

    def persist_extra(self) -> dict:
        return {"color": self.color_i, "text": self.text.get("1.0", "end-1c")}

    def _skin(self) -> None:
        c = NOTE_COLORS[self.color_i]
        self.configure(bg=c)
        self.text.configure(bg=c)

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Next color", command=self._next_color)
        menu.add_command(label="Close note", command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def _next_color(self) -> None:
        self.color_i = (self.color_i + 1) % len(NOTE_COLORS)
        self._skin()
        self.persist()


class QuoteWidget(WidgetWindow):
    key = "quote"
    index = 0

    def __init__(self, master: tk.Tk, x: int = 80, y: int = 420) -> None:
        super().__init__(master, x, y)
        self.configure(bg="#f7f1e6")
        self.lbl = tk.Label(
            self, text=QUOTES[0], wraplength=220, justify="left",
            bg="#f7f1e6", fg="#2a241c", padx=14, pady=12,
            font=("Georgia", 11, "italic"),
        )
        self.lbl.pack()
        self.enable_drag(self.lbl)
        self.bind("<Button-3>", self._menu)
        self.lbl.bind("<Button-1>", self._next)
        self.after(12000, self._auto)

    def _next(self, _event: tk.Event | None = None) -> None:
        QuoteWidget.index = (QuoteWidget.index + 1) % len(QUOTES)
        self.lbl.configure(text=QUOTES[QuoteWidget.index])

    def _auto(self) -> None:
        if not self.winfo_exists():
            return
        self._next()
        self.after(12000, self._auto)

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Next quote", command=self._next)
        menu.add_command(label="Close quote", command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)


class Launcher(tk.Tk, DragMixin):
    def __init__(self) -> None:
        super().__init__()
        self.title("Hello, Dolly")
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg="#1e1b24")
        self.geometry("+40+40")
        bar = tk.Frame(self, bg="#1e1b24", padx=10, pady=8)
        bar.pack()
        tk.Label(
            bar, text="HELLO, DOLLY", fg="#d4c4b0", bg="#1e1b24",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        for label, fn in (
            ("Dolly", self.spawn_dolly),
            ("Fastback", self.spawn_fastback),
            ("Clock", self.spawn_clock),
            ("Sticky note", self.spawn_note),
            ("Quote", self.spawn_quote),
        ):
            tk.Button(
                bar, text=label, command=fn, bd=0, padx=8, pady=4,
                bg="#2a2630", fg="#f4f0e8", activebackground="#d4c4b0",
                activeforeground="#1a1714", font=("Segoe UI", 9),
            ).pack(fill="x", pady=2)
        tk.Button(
            bar, text="Quit all", command=self.destroy, bd=0, padx=8, pady=4,
            bg="#2a2630", fg="#b7b0a6", font=("Segoe UI", 9),
        ).pack(fill="x", pady=(8, 0))
        self.enable_drag(bar)
        self.bind("<Escape>", lambda _e: self.destroy())
        self.dolly: DollyWidget | None = None
        self.fastback: FastbackWidget | None = None
        self._restore()

    def _restore(self) -> None:
        data = load_layout()
        self.spawn_dolly()
        self.spawn_fastback()
        if "clock" in data:
            self.spawn_clock()
        if "note" in data:
            self.spawn_note()
        if "quote" in data:
            self.spawn_quote()

    def _pos(self, key: str, default: tuple[int, int]) -> tuple[int, int]:
        item = load_layout().get(key) or {}
        return int(item.get("x", default[0])), int(item.get("y", default[1]))

    def spawn_dolly(self) -> None:
        if self.dolly is not None and self.dolly.winfo_exists():
            self.dolly.lift()
            return
        x, y = self._pos("dolly", (240, 80))
        look = int(load_layout().get("dolly", {}).get("look", 0))
        self.dolly = DollyWidget(self, x, y, look)

    def spawn_fastback(self) -> None:
        if self.fastback is not None and self.fastback.winfo_exists():
            self.fastback.lift()
            return
        x, y = self._pos("fastback", (80, 360))
        self.fastback = FastbackWidget(self, x, y)

    def spawn_clock(self) -> None:
        x, y = self._pos("clock", (40, 120))
        ClockWidget(self, x, y)

    def spawn_note(self) -> None:
        saved = load_layout().get("note") or {}
        x, y = self._pos("note", (520, 80))
        NoteWidget(self, x, y, int(saved.get("color", 0)), saved.get("text", ""))

    def spawn_quote(self) -> None:
        x, y = self._pos("quote", (40, 280))
        QuoteWidget(self, x, y)


def main() -> None:
    if not PLAY_DIR.exists() or not any(PLAY_DIR.glob("*.png")):
        sys.stderr.write("Missing animated Dolly frames in assets/play/\n")
        raise SystemExit(1)
    if not FASTBACK_DIR.exists() or not any(FASTBACK_DIR.glob("*.png")):
        sys.stderr.write("Missing Fastback frames in assets/fastback/\n")
        raise SystemExit(1)
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
