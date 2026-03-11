import tkinter as tk
from tkinter import ttk

from ..page04.tab_standing_coronal import _get_plan, _set_both, _help_icon, WHITE, FONT

SV_GRADE_HELP = (
    "SV Grade definition:\n\n"
    "0: LIV = SV\n"
    "-1: LIV = 1 level cranial to SV\n"
    "-2: LIV = 2 levels cranial to SV\n"
    "-3: LIV = 3 levels cranial to SV"
)

NV_GRADE_HELP = (
    "NV Grade definition:\n\n"
    "0: LIV = NV\n"
    "-1: LIV = 1 level cranial to NV\n"
    "-2: LIV = 2 levels cranial to NV\n"
    "-3: LIV = 3 levels cranial to NV"
)


def add_sv_nv_grade_combo(parent, app, tab_name, label, key, help_text):
    r = tk.Frame(parent, bg=WHITE)
    r.pack(fill="x", pady=6)

    tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")

    # If _help_icon ever crashes due to an image/path issue, don’t take the whole page down
    try:
        _help_icon(r, label, help_text).pack(side="left", padx=8)
    except Exception:
        pass

    v = tk.StringVar(value=_get_plan(app, key, "0"))
    cb = ttk.Combobox(r, textvariable=v, state="readonly", width=6, values=["0", "-1", "-2", "-3"])
    cb.pack(side="right")

    def _persist():
        field_key = key.split(".", 1)[1] if "." in key else key
        _set_both(app, key, tab_name, field_key, v.get())

    cb.bind("<<ComboboxSelected>>", lambda _evt: _persist())

    try:
        _persist()
    except Exception:
        pass


class Page5_5:
    def __init__(self, app):
        self.app = app

    def setup(self):
        TAB_NAME = "standing_coronal"  # change if needed

        scrollable = self.app.create_standard_page(
            title_text="SV / NV Grades",
            back_command=self.app.setup_page_5,     # change to your actual back page
            next_command=self.app.setup_page_6      # change to your actual next page
        )

        ttk.Label(
            scrollable,
            text="Select SV and NV grades.",
            font=FONT,
            background=WHITE,
            justify="left"
        ).pack(anchor="w", pady=(6, 10))

        sec = tk.Frame(scrollable, bg=WHITE)
        sec.pack(fill="x", padx=10, pady=10)

        # Use your real keys here
        add_sv_nv_grade_combo(sec, self.app, TAB_NAME, "SV Grade", "standing_coronal.sv_grade", SV_GRADE_HELP)
        add_sv_nv_grade_combo(sec, self.app, TAB_NAME, "NV Grade", "standing_coronal.nv_grade", NV_GRADE_HELP)
