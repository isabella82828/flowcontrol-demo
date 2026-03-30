import tkinter as tk
from tkinter import ttk
from typing import Optional

from PIL import Image, ImageTk

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)

def show_help_popup(
    parent,
    title: str,
    body: str,
    width: int = 520,
    height: int = 360,
    image_path: Optional[str] = None,
    image_max_width: int = 480,
):
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=WHITE)
    win.resizable(True, True)

    # Center 
    try:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw // 2) - (width // 2)
        y = py + (ph // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        win.geometry(f"{width}x{height}")

    win.transient(parent)
    win.grab_set()

    win.minsize(480, 240)

    header = tk.Label(
        win,
        text=title,
        bg=WHITE,
        fg=LOGO_GREEN,
        font=("Segoe UI", 13, "bold"),
        anchor="w"
    )
    header.pack(fill="x", padx=14, pady=(12, 6))

    frame = tk.Frame(win, bg=WHITE)
    frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    scrollbar = ttk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    # Canvas + inner frame, so image + text scroll together
    canvas = tk.Canvas(frame, bg=WHITE, highlightthickness=0, bd=0)
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)

    inner = tk.Frame(canvas, bg=WHITE)
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    # Keep the inner frame width synced to the canvas width
    def _on_canvas_configure(event):
        canvas.itemconfigure(window_id, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)

    # Update scrollregion when inner content changes
    def _update_scrollregion(_evt=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner.bind("<Configure>", _update_scrollregion)

    # Text content (read-only)
    body_lbl = tk.Label(
        inner,
        text=body,
        bg=WHITE,
        font=FONT,
        justify="left",
        anchor="w",
        wraplength=width - 60,
        padx=10,
        pady=10,
    )
    body_lbl.pack(anchor="w", fill="x")

    # Optional image below text
    if image_path:
        try:
            img = Image.open(image_path)

            if img.width > image_max_width:
                scale = image_max_width / float(img.width)
                new_w = int(img.width * scale)
                new_h = int(img.height * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            img_lbl = tk.Label(inner, image=photo, bg=WHITE)
            img_lbl.image = photo  # prevent GC
            img_lbl.pack(anchor="w", padx=10, pady=(6, 10))
        except Exception as e:
            err = tk.Label(
                inner,
                text=f"[Image failed to load: {e}]",
                bg=WHITE,
                fg="gray",
                font=("Segoe UI", 10)
            )
            err.pack(anchor="w", padx=10, pady=(6, 10))


    # Mousewheel scrolling (Windows + macOS)
    def _on_mousewheel(event):
        # Windows: event.delta is multiples of 120
        # macOS: event.delta is small increments
        delta = event.delta
        if delta == 0:
            return
        step = -1 if delta > 0 else 1
        canvas.yview_scroll(step, "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    btn_row = tk.Frame(win, bg=WHITE)
    btn_row.pack(fill="x", padx=14, pady=(0, 12))

    ok = ttk.Button(btn_row, text="OK", command=win.destroy)
    ok.pack(side="right")

    win.bind("<Escape>", lambda _e: win.destroy())
    win.focus_set()
    ok.focus_set()

    def _cleanup(_evt=None):
        try:
            canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    win.protocol("WM_DELETE_WINDOW", lambda: ( _cleanup(), win.destroy() ))
    win.bind("<Destroy>", _cleanup)
    ok.config(command=lambda: (_cleanup(), win.destroy()))
    win.bind("<Escape>", lambda _e: (_cleanup(), win.destroy()))

    win.wait_window(win)