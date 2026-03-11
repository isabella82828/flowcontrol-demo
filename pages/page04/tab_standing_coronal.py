import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

from matplotlib import container

from .help_popup import show_help_popup

WHITE = "#FFFFFF"
FONT = ("Segoe UI", 12)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELP_ICON_PATH = os.path.join(BASE_DIR, "assets", "question-mark.png")

def _set_plan(app, key, value):
    if not hasattr(app, "plan_data") or app.plan_data is None:
        app.plan_data = {}
    app.plan_data[key] = value

def _get_plan(app, key, default=""):
    if not hasattr(app, "plan_data") or app.plan_data is None:
        return default
    return app.plan_data.get(key, default)

def _ensure_dict(d, key):
    if key not in d or not isinstance(d[key], dict):
        d[key] = {}
    return d[key]

def _set_radiographic(app, tab_name: str, field_key: str, value):
    if not hasattr(app, "plan_data") or app.plan_data is None:
        app.plan_data = {}

    rp = _ensure_dict(app.plan_data, "radiographic_parameters")
    tab = _ensure_dict(rp, tab_name)

    tab[field_key] = value

def _set_both(app, flat_key: str, tab_name: str, field_key: str, value):
    _set_plan(app, flat_key, value)
    _set_radiographic(app, tab_name, field_key, value)

def _only_numeric_decimal(P: str) -> bool:
    if P == "":
        return True
    if P == "-":
        return True
    try:
        float(P)
    except ValueError:
        return False
    return P.count(".") <= 1


def _format_one_decimal(value: str) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s in ("", "-"):
        return s
    try:
        return f"{float(s):.1f}"
    except ValueError:
        return s


def _help_icon(parent, title: str, help_text: str, size: int = 20):
    img = Image.open(HELP_ICON_PATH).resize((size, size), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)

    lbl = tk.Label(parent, image=photo, bg=WHITE, cursor="hand2")
    lbl.image = photo  # prevent GC

    def _open(_evt=None):
        show_help_popup(parent, title, help_text)

    lbl.bind("<Button-1>", _open)
    return lbl


def build_tab(app, parent):
   
    TAB_NAME = "standing_coronal"
    TRUNK_SHIFT_VALUES = ["Left", "Neutral", "Right"]
    CSVL_TLL_APEX_VALUES = [
        "Touches apical body",
        "Between Pedicles",
        "Completely medial"
    ]

    L4_TILT_VALUES = ["Left", "Neutral", "Right"]

    container = tk.Frame(parent, bg=WHITE)
    container.pack(fill="both", expand=True, padx=20, pady=15)

    vcmd = (container.register(_only_numeric_decimal), "%P")

    tk.Label(container, text="Standing Coronal", bg=WHITE, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

    # -------------------------
    # Section 1: Anatomic Variants
    # -------------------------
    sec1 = tk.LabelFrame(container, text="Anatomic Variants", bg=WHITE, font=("Segoe UI", 12, "bold"), padx=10, pady=10)
    sec1.pack(fill="x", pady=(0, 12))

    tk.Label(sec1, text="Number of ribs / thoracic vertebrae", bg=WHITE, font=FONT).grid(
        row=0, column=0, sticky="w"
    )

    thor_choice_var = tk.StringVar(value=_get_plan(app, "anatomy.thoracic_count_choice", "12"))
    thor_other_var = tk.StringVar(value=_get_plan(app, "anatomy.thoracic_count_other", ""))

    def _on_thor_choice_change():
        choice = thor_choice_var.get()
        _set_both(app, "anatomy.thoracic_count_choice", TAB_NAME, "thoracic_count_choice", choice)
        if choice != "Other":
            thor_other_entry.configure(state="disabled")
            thor_other_var.set("")
            _set_both(app, "anatomy.thoracic_count_other", TAB_NAME, "thoracic_count_other", "")
        else:
            thor_other_entry.configure(state="normal")

    rb_frame = tk.Frame(sec1, bg=WHITE)
    rb_frame.grid(row=1, column=0, sticky="w", pady=(6, 0))

    for i, opt in enumerate(["11", "12", "13", "Other"]):
        ttk.Radiobutton(
            rb_frame, text=opt, value=opt, variable=thor_choice_var, command=_on_thor_choice_change
        ).grid(row=0, column=i, padx=(0, 12), sticky="w")

    tk.Label(sec1, text="Other (10 to 14)", bg=WHITE, font=FONT).grid(row=2, column=0, sticky="w", pady=(8, 0))
    thor_other_entry = ttk.Entry(sec1, textvariable=thor_other_var, width=10)
    thor_other_entry.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(8, 0))

    def _on_thor_other_change(*_):
        val = thor_other_var.get().strip()
        _set_both(app, "anatomy.thoracic_count_other", TAB_NAME, "thoracic_count_other", val)

    thor_other_var.trace_add("write", _on_thor_other_change)
    _on_thor_choice_change()

    tk.Label(sec1, text="Number of lumbar vertebrae", bg=WHITE, font=FONT).grid(row=3, column=0, sticky="w", pady=(12, 0))
    lumbar_var = tk.StringVar(value=_get_plan(app, "anatomy.lumbar_count", "5"))

    lumbar_frame = tk.Frame(sec1, bg=WHITE)
    lumbar_frame.grid(row=4, column=0, sticky="w", pady=(6, 0))

    def _on_lumbar_change():
        _set_both(app, "anatomy.lumbar_count", TAB_NAME, "lumbar_count", lumbar_var.get())

    for i, opt in enumerate(["4", "5", "6"]):
        ttk.Radiobutton(
            lumbar_frame, text=opt, value=opt, variable=lumbar_var, command=_on_lumbar_change
        ).grid(row=0, column=i, padx=(0, 12), sticky="w")
    _on_lumbar_change()

    # -------------------------
    # Leg Length Discrepancy 
    # -------------------------

    LLD_DIRECTION_VALUES = [
        "Left longer",
        "Right longer",
        "No clinically significant difference",
        "Not assessed / Unknown",
    ]

    LLD_MAGNITUDE_VALUES = [
        "< 1 cm",
        "≥ 1 cm",
        "Not assessed / Unknown",
    ]

    r_lld = tk.Frame(sec1, bg=WHITE)
    r_lld.grid(row=5, column=0, columnspan=2, sticky="we", pady=(12, 0))
    tk.Label(r_lld, text="Leg Length Discrepancy", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_lld,
        "Leg Length Discrepancy",
        "Direction: which side is longer, or no clinically significant difference.\n"
        "Magnitude: whether the discrepancy is < 1 cm or ≥ 1 cm.\n\n"
        "If not measured, choose Not assessed / Unknown."
    ).pack(side="left", padx=8)

    # Direction row
    r_lld_dir = tk.Frame(sec1, bg=WHITE)
    r_lld_dir.grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 0))
    tk.Label(r_lld_dir, text="Direction", bg=WHITE, font=FONT).pack(side="left")

    lld_dir_var = tk.StringVar(
        value=_get_plan(app, "anatomy.leg_length.direction", "Not assessed / Unknown")
    )
    lld_dir_combo = ttk.Combobox(
        r_lld_dir,
        textvariable=lld_dir_var,
        state="readonly",
        width=34,
        values=LLD_DIRECTION_VALUES,
    )
    lld_dir_combo.pack(side="right")

    # Magnitude row
    r_lld_mag = tk.Frame(sec1, bg=WHITE)
    r_lld_mag.grid(row=7, column=0, columnspan=2, sticky="we", pady=(6, 0))
    tk.Label(r_lld_mag, text="Magnitude", bg=WHITE, font=FONT).pack(side="left")

    lld_mag_var = tk.StringVar(
        value=_get_plan(app, "anatomy.leg_length.magnitude", "Not assessed / Unknown")
    )
    lld_mag_combo = ttk.Combobox(
        r_lld_mag,
        textvariable=lld_mag_var,
        state="readonly",
        width=34,
        values=LLD_MAGNITUDE_VALUES,
    )
    lld_mag_combo.pack(side="right")


    def _apply_lld_rules():
        d = lld_dir_var.get()

        _set_both(app, "anatomy.leg_length.direction", TAB_NAME, "leg_length_direction", d)

        if d == "Not assessed / Unknown":
            lld_mag_combo.configure(state="disabled")
            lld_mag_var.set("Not assessed / Unknown")
            _set_both(app, "anatomy.leg_length.magnitude", TAB_NAME, "leg_length_magnitude", "Not assessed / Unknown")
            return

        if d == "No clinically significant difference":
            lld_mag_combo.configure(state="disabled")
            lld_mag_var.set("< 1 cm")
            _set_both(app, "anatomy.leg_length.magnitude", TAB_NAME, "leg_length_magnitude", "< 1 cm")
            return

        # Left longer or Right longer
        lld_mag_combo.configure(state="readonly")
        _set_both(app, "anatomy.leg_length.magnitude", TAB_NAME, "leg_length_magnitude", lld_mag_var.get())


    def _on_lld_dir(_evt=None):
        _apply_lld_rules()


    def _on_lld_mag(_evt=None):
        _set_both(app, "anatomy.leg_length.magnitude", TAB_NAME, "leg_length_magnitude", lld_mag_var.get())


    lld_dir_combo.bind("<<ComboboxSelected>>", _on_lld_dir)
    lld_mag_combo.bind("<<ComboboxSelected>>", _on_lld_mag)

    _apply_lld_rules()

    lld_dir_combo.bind("<<ComboboxSelected>>", _on_lld_dir)
    lld_mag_combo.bind("<<ComboboxSelected>>", _on_lld_mag)

    # Initialize state based on stored values
    _apply_lld_rules()

    row_ana = tk.Frame(sec1, bg=WHITE)
    row_ana.grid(row=8, column=0, columnspan=2, sticky="we", pady=(12, 0))
    tk.Label(row_ana, text="Other anatomic considerations", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        row_ana,
        "Other anatomic considerations",
        "Please enter any anatomic variants or considerations not captured above."
    ).pack(side="left", padx=8)

    ana_txt = tk.Text(sec1, height=3, font=FONT, wrap="word")
    ana_txt.grid(row=9, column=0, columnspan=2, sticky="we", pady=(6, 0))
    sec1.grid_columnconfigure(0, weight=1)

    ana_txt.insert("1.0", _get_plan(app, "anatomy.other_anatomic_considerations", ""))

    def _save_ana_txt(_event=None):
        _set_both(
            app,
            "anatomy.other_anatomic_considerations",
            TAB_NAME,
            "other_anatomic_considerations",
            ana_txt.get("1.0", "end-1c").strip()
        )

    ana_txt.bind("<KeyRelease>", _save_ana_txt)

    # -------------------------
    # Section 2: Coronal Measurements (Standing)
    # -------------------------
    sec2 = tk.LabelFrame(container, text="Coronal Measurements (Standing)", bg=WHITE, font=("Segoe UI", 12, "bold"), padx=10, pady=10)
    sec2.pack(fill="x", pady=(0, 12))

    def add_angle_row(label, key, help_text, signed_hint=None):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)

        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, help_text).pack(side="left", padx=8)

        var = tk.StringVar(value=_get_plan(app, key, ""))

        ent = ttk.Entry(r, textvariable=var, width=10, validate="key", validatecommand=vcmd)
        ent.pack(side="right")

        def _on_write(*_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, var.get().strip())

        def _on_focus_out(_):
            var.set(_format_one_decimal(var.get()))
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, var.get().strip())

        var.trace_add("write", _on_write)
        ent.bind("<FocusOut>", _on_focus_out)

        if signed_hint:
            tk.Label(r, text=signed_hint, bg=WHITE, font=FONT).pack(side="right", padx=(0, 12))

        return var

    def add_mm_row(label, key, help_text):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)

        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, help_text).pack(side="left", padx=8)

        var = tk.StringVar(value=_get_plan(app, key, ""))
        ent = ttk.Entry(r, textvariable=var, width=10, validate="key", validatecommand=vcmd)
        ent.pack(side="right")

        def _on_write(*_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, var.get().strip())

        def _on_focus_out(_):
            var.set(_format_one_decimal(var.get()))
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, var.get().strip())

        var.trace_add("write", _on_write)
        ent.bind("<FocusOut>", _on_focus_out)
        return var

    add_angle_row(
        "Proximal Thoracic Cobb Angle (deg)",
        "standing.pt_cobb",
        "The coronal angle between the cranial endplate of the most tilted vertebra above the proximal thoracic curve apex and the caudal endplate of the most tilted vertebra below the apex (typically from T1 or T2 to T5)."
    )

    r_apex = tk.Frame(sec2, bg=WHITE)
    r_apex.pack(fill="x", pady=6)

    tk.Label(r_apex, text="Main Thoracic Curve Apex Direction", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_apex,
        "Main Thoracic Curve Apex Direction",
        "Direction of Main Thoracic Curve Convexity."
    ).pack(side="left", padx=8)

    apex_var = tk.StringVar(value=_get_plan(app, "standing.mt_apex_direction", "Right"))

    def _on_apex_change():
        val = apex_var.get()
        _set_both(app, "standing.mt_apex_direction", TAB_NAME, "mt_apex_direction", val)
        if val == "Left":
            messagebox.showwarning(
                title="MRI",
                message="Main thoracic curve convexity is Left. MRI is recommended."
            )

    apex_frame = tk.Frame(sec2, bg=WHITE)
    apex_frame.pack(fill="x", pady=(0, 6))

    ttk.Radiobutton(apex_frame, text="Right", value="Right", variable=apex_var, command=_on_apex_change).pack(side="left", padx=(0, 12))
    ttk.Radiobutton(apex_frame, text="Left", value="Left", variable=apex_var, command=_on_apex_change).pack(side="left", padx=(0, 12))
    _on_apex_change()

    add_angle_row(
        "Main Thoracic Cobb Angle (deg)",
        "standing.mt_cobb",
        "The coronal angle between the upper endplate of the most tilted vertebra above the main thoracic curve apex and the lower endplate of the most tilted vertebra below the apex (usually T4 to T12)."
    )

    add_angle_row(
        "Thoracolumbar / Lumbar Cobb Angle (deg)",
        "standing.tl_l_cobb",
        "The coronal angle between the most tilted vertebra above the apex (often T10 to T12) and the most tilted vertebra below the apex (often L3 to L4)."
    )

    # -------------------------
    # Risser Score
    # -------------------------
    r_risser = tk.Frame(sec2, bg=WHITE)
    r_risser.pack(fill="x", pady=6)
    tk.Label(r_risser, text="Risser Score", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_risser,
        "Risser Score",
        "0 = No ossification of the iliac apophysis\n"
        "1 = Up to 25% ossification (starts at anterolateral crest)\n"
        "2 = 26 to 50% ossification\n"
        "3 = 51 to 75% ossification\n"
        "4 = 76 to 100% ossification\n"
        "5 = Complete ossification and fusion to iliac crest"
    ).pack(side="left", padx=8)

    risser_var = tk.StringVar(value=_get_plan(app, "standing.risser_score", "0"))
    risser_combo = ttk.Combobox(r_risser, textvariable=risser_var, state="readonly", width=6, values=["0", "1", "2", "3", "4", "5"])
    risser_combo.pack(side="right")

    def _on_risser(_):
        _set_both(app, "standing.risser_score", TAB_NAME, "risser_score", risser_var.get())

    risser_combo.bind("<<ComboboxSelected>>", _on_risser)
    _set_both(app, "standing.risser_score", TAB_NAME, "risser_score", risser_var.get())

    vertebra_values = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12",
                       "L1", "L2", "L3", "L4", "L5"]

    def add_vertebra_combo(label, key, help_text, default=""):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)
        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, help_text).pack(side="left", padx=8)

        v = tk.StringVar(value=_get_plan(app, key, default))
        cb = ttk.Combobox(r, textvariable=v, state="readonly", width=6, values=vertebra_values)
        cb.pack(side="right")

        def _on_pick(_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, v.get())

        cb.bind("<<ComboboxSelected>>", _on_pick)
        field_key = key.split(".", 1)[1] if "." in key else key
        _set_both(app, key, TAB_NAME, field_key, v.get())

    touched_values = ["T12", "L1", "L2", "L3", "L4", "L5"]

    def add_touched_combo(label, key, help_text, default="L3"):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)
        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, help_text).pack(side="left", padx=8)

        v = tk.StringVar(value=_get_plan(app, key, default))
        cb = ttk.Combobox(r, textvariable=v, state="readonly", width=6, values=touched_values)
        cb.pack(side="right")

        def _on_pick(_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, v.get())

        cb.bind("<<ComboboxSelected>>", _on_pick)
        field_key = key.split(".", 1)[1] if "." in key else key
        _set_both(app, key, TAB_NAME, field_key, v.get())

    add_touched_combo(
        "Last Substantially Touched Vertebra (LSTV)",
        "standing.last_substantially_touched_vertebra",
        "Last vertebra where the CSVL passes medial to the pedicles on the standing radiograph"
    )

    # -------------------------
    # Lordotic Disc Below LTV of MT Curve
    # -------------------------
    r_ld = tk.Frame(sec2, bg=WHITE)
    r_ld.pack(fill="x", pady=6)

    tk.Label(
        r_ld,
        text="Lordotic Disc Below LTV of MT Curve",
        bg=WHITE,
        font=FONT
    ).pack(side="left")

    _help_icon(
        r_ld,
        "Lordotic Disc Below LTV of MT Curve",
        "Is the disc immediately below the last touched vertebra (LTV) of the main thoracic curve lordotic on standing radiograph?\n\n"
        "Yes = disc is lordotic.\nNo = disc is neutral or kyphotic."
    ).pack(side="left", padx=8)

    ld_var = tk.StringVar(value=_get_plan(app, "standing.lordotic_disc_below_mt_ltv", ""))

    def _on_ld_change():
        _set_both(
            app,
            "standing.lordotic_disc_below_mt_ltv",
            TAB_NAME,
            "lordotic_disc_below_mt_ltv",
            ld_var.get()
        )

    ld_frame = tk.Frame(sec2, bg=WHITE)
    ld_frame.pack(fill="x", pady=(0, 6))

    ttk.Radiobutton(
        ld_frame,
        text="Yes",
        value="Yes",
        variable=ld_var,
        command=_on_ld_change
    ).pack(side="left", padx=(0, 18))

    ttk.Radiobutton(
        ld_frame,
        text="No",
        value="No",
        variable=ld_var,
        command=_on_ld_change
    ).pack(side="left", padx=(0, 18))

    _on_ld_change()

    # Trunk Shift
    r_ts = tk.Frame(sec2, bg=WHITE)
    r_ts.pack(fill="x", pady=6)
    tk.Label(r_ts, text="Trunk Shift", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_ts,
        "Trunk Shift",
        "Trunk shift is calculated by measuring the linear distance in millimeters between the vertical trunk reference line (VTRL) and the CSVL. A trunk shift to the right of the CSVL is a positive value, and to the left of the CSVL a negative value."
    ).pack(side="left", padx=8)

    ts_var = tk.StringVar(value=_get_plan(app, "standing.trunk_shift", "Neutral"))
    ts_combo = ttk.Combobox(r_ts, textvariable=ts_var, state="readonly", width=10, values=TRUNK_SHIFT_VALUES)
    ts_combo.pack(side="right")

    def _on_ts(_):
        _set_both(app, "standing.trunk_shift", TAB_NAME, "trunk_shift", ts_var.get())

    ts_combo.bind("<<ComboboxSelected>>", _on_ts)
    _set_both(app, "standing.trunk_shift", TAB_NAME, "trunk_shift", ts_var.get())

    # CSVL–TL/L Apex Position
    r_csvl = tk.Frame(sec2, bg=WHITE)
    r_csvl.pack(fill="x", pady=6)
    tk.Label(r_csvl, text="CSVL–TL/L Apex Position", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_csvl,
        "CSVL–TL/L Apex Position",
        "Where is Center Sacral Vertical Line situated compared to the Lumbar Apical Vertebra?"
    ).pack(side="left", padx=8)

    csvl_var = tk.StringVar(value=_get_plan(app, "standing.csvl_tll_apex_position", "Between Pedicles"))
    csvl_combo = ttk.Combobox(r_csvl, textvariable=csvl_var, state="readonly", width=10, values=CSVL_TLL_APEX_VALUES)
    csvl_combo.pack(side="right")

    def _on_csvl(_):
        _set_both(app, "standing.csvl_tll_apex_position", TAB_NAME, "csvl_tll_apex_position", csvl_var.get())

    csvl_combo.bind("<<ComboboxSelected>>", _on_csvl)
    _set_both(app, "standing.csvl_tll_apex_position", TAB_NAME, "csvl_tll_apex_position", csvl_var.get())

    # Last Touched Vertebra of MT (MT-LTV)
    r_mtlv = tk.Frame(sec2, bg=WHITE)
    r_mtlv.pack(fill="x", pady=6)
    tk.Label(r_mtlv, text="Last Touched Vertebra of MT (MT-LTV)", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_mtlv,
        "MT-LTV",
        "Last touched vertebra of the main thoracic curve (MT-LTV), measured per the algorithm definition."
    ).pack(side="left", padx=8)

    mtlv_var = tk.StringVar(value=_get_plan(app, "standing.mt_last_touched_vertebra", "T12"))
    mtlv_combo = ttk.Combobox(
        r_mtlv,
        textvariable=mtlv_var,
        state="readonly",
        width=6,
        values=["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12","L1","L2","L3","L4","L5"]
    )
    mtlv_combo.pack(side="right")

    def _on_mtlv(_):
        _set_both(app, "standing.mt_last_touched_vertebra", TAB_NAME, "mt_last_touched_vertebra", mtlv_var.get())

    mtlv_combo.bind("<<ComboboxSelected>>", _on_mtlv)
    _set_both(app, "standing.mt_last_touched_vertebra", TAB_NAME, "mt_last_touched_vertebra", mtlv_var.get())

    # L4 Tilt Direction (standing)
    r_l4 = tk.Frame(sec2, bg=WHITE)
    r_l4.pack(fill="x", pady=6)
    tk.Label(r_l4, text="L4 Tilt Direction", bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_l4,
        "L4 Tilt Direction",
        "Right = L4 endplate slopes down towards right. Left = L4 endplate slopes down towards left"
    ).pack(side="left", padx=8)

    l4_var = tk.StringVar(value=_get_plan(app, "standing.l4_tilt_direction", "Neutral"))
    l4_combo = ttk.Combobox(r_l4, textvariable=l4_var, state="readonly", width=10, values=L4_TILT_VALUES)
    l4_combo.pack(side="right")

    def _on_l4(_):
        _set_both(app, "standing.l4_tilt_direction", TAB_NAME, "l4_tilt_direction", l4_var.get())

    l4_combo.bind("<<ComboboxSelected>>", _on_l4)
    _set_both(app, "standing.l4_tilt_direction", TAB_NAME, "l4_tilt_direction", l4_var.get())

    # Shoulder Elevation
    r_se = tk.Frame(sec2, bg=WHITE)
    r_se.pack(fill="x", pady=6)
    tk.Label(r_se, text="Shoulder Elevation", bg=WHITE, font=FONT).pack(side="left")

    se_var = tk.StringVar(value=_get_plan(app, "standing.shoulder_elevation", "0"))
    se_combo = ttk.Combobox(
        r_se,
        textvariable=se_var,
        state="readonly",
        width=12,
        values=["+1 (Left +)", "0 (Neutral)", "-1 (Right -)"]
    )
    se_combo.pack(side="right")

    def _se_to_val(s):
        if s.startswith("+1"):
            return "+1"
        if s.startswith("-1"):
            return "-1"
        return "0"

    def _on_se_select(_):
        _set_both(app, "standing.shoulder_elevation", TAB_NAME, "shoulder_elevation", _se_to_val(se_var.get()))

    se_combo.bind("<<ComboboxSelected>>", _on_se_select)

    stored_se = _get_plan(app, "standing.shoulder_elevation", "0")
    if stored_se == "+1":
        se_var.set("+1 (Left +)")
    elif stored_se == "-1":
        se_var.set("-1 (Right -)")
    else:
        se_var.set("0 (Neutral)")

    _set_both(app, "standing.shoulder_elevation", TAB_NAME, "shoulder_elevation", stored_se)

    def add_direction_row(label, key, help_text, values, default="Neutral"):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)

        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, help_text).pack(side="left", padx=8)

        v = tk.StringVar(value=_get_plan(app, key, default))
        cb = ttk.Combobox(r, textvariable=v, state="readonly", width=14, values=values)
        cb.pack(side="right")

        def _on_pick(_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, v.get())

        cb.bind("<<ComboboxSelected>>", _on_pick)

        # persist initial value too
        field_key = key.split(".", 1)[1] if "." in key else key
        _set_both(app, key, TAB_NAME, field_key, v.get())

        return v


    # add_direction_row(
    # "Clavicle Angle Direction",
    # "standing.clavicle_angle",
    # "Left means left side higher, Right means right side higher.",
    # values=["Left", "Neutral", "Right"],
    # default="Neutral"
    # )

    # add_direction_row(
    #     "Disc Tilt Direction",
    #     "standing.disc_tilt",
    #     "Select the convexity direction.",
    #     values=["Convex Left", "Neutral", "Convex Right"],
    #     default="Neutral"
    # )

    add_direction_row(
        "T1 Tilt",
        "standing.t1_tilt",
        "Coronal angle between the cranial endplate of the most titled vertebra above the proximal thoracic curve apex and the caudal endplate of the most tilted vertebra below the apex (typically from T1 or T2 to T5).",
        values=["Left", "Neutral", "Right"],
        default="Neutral"
    )


    add_mm_row(
    "MT Apical Translation (mm)",
    "standing.mt_apical_translation_mm",
    "Distance (mm) between centroid of the apical vertebra and the reference line. Use C7 plumbline for main thoraic curve."
    )

    add_mm_row(
        "TL/L Apical Translation (mm)",
        "standing.tll_apical_translation_mm",
        "Distance (mm) between centroid of the apical vertebra and the reference line. Use C7 plumbline for main thoracic curve."
    )

    add_mm_row(
    "L3 Deviation from CSVL (mm)",
    "standing.l3_deviation_csvl_mm",
    "Distance (mm) between the centroid of the L3 vertebra and the CSVL."
    )

    r_lrot = tk.Frame(sec2, bg=WHITE)
    r_lrot.pack(fill="x", pady=6)
    tk.Label(r_lrot, text="L3 Rotation (Nash Moe)",bg=WHITE, font=FONT).pack(side="left")
    _help_icon(
        r_lrot,
        "L3 Rotation (Nash Moe)",
        "Grade 0 Pedicles symmetric\n"
        "Grade 1 Concave pedicle moves toward midline\n"
        "Grade 2 Concave pedicle at midline\n"
        "Grade 3 Convex pedicle begins to disappear\n"
        "Grade 4 Convex pedicle completely disappears"
    ).pack(side="left", padx=8)

    lrot_var = tk.StringVar(value=_get_plan(app, "standing.l3_rotation_grade", "0"))
    lrot_combo = ttk.Combobox(r_lrot, textvariable=lrot_var, state="readonly", width=6, values=["0", "1", "2", "3", "4"])
    lrot_combo.pack(side="right")

    def _on_lrot(_):
        _set_both(app, "standing.l3_rotation_grade", TAB_NAME, "l3_rotation_grade", lrot_var.get())

    lrot_combo.bind("<<ComboboxSelected>>", _on_lrot)
    _set_both(app, "standing.l3_rotation_grade", TAB_NAME, "l3_rotation_grade", lrot_var.get())

    NASH_MOE_HELP = (
    "Nash-Moe rotation grade.\n\n"
    "Grade 0: Pedicles symmetric.\n"
    "Grade 1: Convex pedicle moves toward the midline.\n"
    "Grade 2: Convex pedicle is two-thirds of the way to the midline.\n"
    "Grade 3: Convex pedicle at the midline.\n"
    "Grade 4: Convex pedicle beyond the midline."
    )

    def add_nashmoe_combo(label, key):
        r = tk.Frame(sec2, bg=WHITE)
        r.pack(fill="x", pady=6)
        tk.Label(r, text=label, bg=WHITE, font=FONT).pack(side="left")
        _help_icon(r, label, NASH_MOE_HELP).pack(side="left", padx=8)

        v = tk.StringVar(value=_get_plan(app, key, "0"))
        cb = ttk.Combobox(r, textvariable=v, state="readonly", width=6, values=["0", "1", "2", "3", "4"])
        cb.pack(side="right")

        def _on_pick(_):
            field_key = key.split(".", 1)[1] if "." in key else key
            _set_both(app, key, TAB_NAME, field_key, v.get())

        cb.bind("<<ComboboxSelected>>", _on_pick)

        field_key = key.split(".", 1)[1] if "." in key else key
        _set_both(app, key, TAB_NAME, field_key, v.get())

    add_nashmoe_combo("Main Thoracic Nash-Moe Grade (numeric)", "standing.mt_nashmoe_grade")
    add_nashmoe_combo("TL/L Apical Nash-Moe Grade (numeric)", "standing.tll_nashmoe_grade")

    # -------------------------
    # Selective Thoracic Fusion decision
    # -------------------------
    sec_decision = tk.LabelFrame(
        container,
        text="Clinical Decision",
        bg=WHITE,
        font=("Segoe UI", 12, "bold"),
        padx=10,
        pady=10
    )
    sec_decision.pack(fill="x", pady=(0, 12))

    r_stf = tk.Frame(sec_decision, bg=WHITE)
    r_stf.pack(fill="x", pady=6)

    tk.Label(
        r_stf,
        text="Proceed with Selective Thoracic Fusion?",
        bg=WHITE,
        font=FONT
    ).pack(side="left")

    _help_icon(
        r_stf,
        "Selective Thoracic Fusion",
        "Patient preference: proceed with Selective Thoracic Fusion (Yes or No)."
    ).pack(side="left", padx=8)

    stf_var = tk.StringVar(value=_get_plan(app, "clinical.selective_thoracic_fusion", ""))

    def _on_stf_change():
        _set_plan(app, "clinical.selective_thoracic_fusion", stf_var.get())

    stf_frame = tk.Frame(sec_decision, bg=WHITE)
    stf_frame.pack(fill="x", pady=(0, 6))

    ttk.Radiobutton(
        stf_frame,
        text="Yes",
        value="Yes",
        variable=stf_var,
        command=_on_stf_change
    ).pack(side="left", padx=(0, 18))

    ttk.Radiobutton(
        stf_frame,
        text="No",
        value="No",
        variable=stf_var,
        command=_on_stf_change
    ).pack(side="left", padx=(0, 18))

    _on_stf_change()

