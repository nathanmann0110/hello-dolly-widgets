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
STORE = Path.home() / "AppData" / "Local" / "HelloDolly" / "layout-v15.json"
if sys.platform != "win32":
    STORE = ROOT / "layout-v15.json"

MAGENTA = "#ff00aa"
BLACK = "#000000"
PLAY_DIR = ASSETS / "play"
FASTBACK_DIR = ASSETS / "fastback"
VAN_DIR = ASSETS / "van"
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
        self.after(240, self._tick)

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
        self.after(240, self._tick)


class ZoomSpinWidget(WidgetWindow):
    folder: Path = FASTBACK_DIR
    close_label = "Close"
    tick_ms = 33
    display_scale = 1.25
    chroma = BLACK

    def __init__(self, master: tk.Tk, x: int = 80, y: int = 360) -> None:
        super().__init__(master, x, y)
        self._frame = 0
        self._photo = None
        self._paths = sorted(p for p in self.folder.glob("*.png") if p.parent == self.folder)
        self._nw, self._nh = (960, 600)
        if self._paths:
            with Image.open(self._paths[0]) as im:
                self._nw, self._nh = im.size
        key = self.chroma
        self.configure(bg=key)
        if sys.platform == "win32":
            self.wm_attributes("-transparentcolor", key)
        self.label = tk.Label(self, bd=0, highlightthickness=0, bg=key)
        self.label.pack()
        self.enable_drag(self.label)
        self.label.bind("<Button-3>", self._menu)
        self.bind("<Button-3>", self._menu)
        self.label.bind("<Double-Button-1>", lambda _e: self.destroy())
        self._show()
        self.after(self.tick_ms, self._tick)

    def _display_size(self) -> tuple[int, int]:
        return (
            max(1, round(self._nw * self.display_scale)),
            max(1, round(self._nh * self.display_scale)),
        )

    def _show(self) -> None:
        if not self._paths:
            return
        path = self._paths[self._frame % len(self._paths)]
        with Image.open(path) as src:
            im = src.convert("RGB")
        size = self._display_size()
        if im.size != size:
            im = im.resize(size, Image.Resampling.BILINEAR)
        self._photo = ImageTk.PhotoImage(im)
        self.label.configure(image=self._photo)

    def _menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.close_label, command=self.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def _tick(self) -> None:
        if not self.winfo_exists() or not self._paths:
            return
        self._frame = (self._frame + 1) % len(self._paths)
        self._show()
        self.after(self.tick_ms, self._tick)


class FastbackWidget(ZoomSpinWidget):
    key = "fastback"
    folder = FASTBACK_DIR
    close_label = "Close Fastback"


class VanWidget(ZoomSpinWidget):
    key = "van"
    folder = VAN_DIR
    close_label = "Close Van"


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
            ("Van", self.spawn_van),
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
        self.van: VanWidget | None = None
        self._restore()

    def _restore(self) -> None:
        self.spawn_dolly()
        self.after(80, self.spawn_fastback)
        self.after(160, self.spawn_van)

    def _pos(self, key: str, default: tuple[int, int]) -> tuple[int, int]:
        item = load_layout().get(key) or {}
        try:
            x = int(item.get("x", default[0]))
            y = int(item.get("y", default[1]))
        except Exception:
            x, y = default
        try:
            sw = max(320, self.winfo_screenwidth())
            sh = max(240, self.winfo_screenheight())
        except Exception:
            sw, sh = 1920, 1080
        return max(0, min(x, sw - 120)), max(0, min(y, sh - 120))

    def spawn_dolly(self) -> None:
        if self.dolly is not None and self.dolly.winfo_exists():
            self.dolly.lift()
            return
        x, y = self._pos("dolly", (200, 80))
        look = int(load_layout().get("dolly", {}).get("look", 0))
        self.dolly = DollyWidget(self, x, y, look)

    def spawn_fastback(self) -> None:
        if self.fastback is not None and self.fastback.winfo_exists():
            self.fastback.lift()
            return
        x, y = self._pos("fastback", (480, 220))
        self.fastback = FastbackWidget(self, x, y)
        self._raise_dolly()

    def spawn_van(self) -> None:
        if self.van is not None and self.van.winfo_exists():
            self.van.lift()
            return
        x, y = self._pos("van", (60, 360))
        self.van = VanWidget(self, x, y)
        self._raise_dolly()

    def _raise_dolly(self) -> None:
        if self.dolly is not None and self.dolly.winfo_exists():
            self.dolly.lift()


def main() -> None:
    if not PLAY_DIR.exists() or not any(PLAY_DIR.glob("*.png")):
        sys.stderr.write("Missing animated Dolly frames in assets/play/\n")
        raise SystemExit(1)
    if not FASTBACK_DIR.exists() or not any(FASTBACK_DIR.glob("*.png")):
        sys.stderr.write("Missing Fastback frames in assets/fastback/\n")
        raise SystemExit(1)
    if not VAN_DIR.exists() or not any(VAN_DIR.glob("*.png")):
        sys.stderr.write("Missing Van frames in assets/van/\n")
        raise SystemExit(1)
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            input("Press Enter to close...")
        except Exception:
            pass
