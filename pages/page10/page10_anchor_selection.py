import tkinter as tk
from tkinter import ttk, messagebox

from inventory.inventory_tracker import (
    recompute_usage_from_plan,
    compute_overages,
    format_overage_messages,
)

from inventory.inventory_loader import (
    load_inventory_sql,
    validate_inventory_data,
)

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)


class Page10AnchorSelection:
    def __init__(self, app):
        self.app = app

        self.levels_frame = None
        self.btn_remove_top = None
        self.btn_remove_bottom = None

        self.level_vars = []
        self.level_combos = []

        self.inventory_status_label = None

        self.row_models = []

        # Allowed spine levels for dropdown
        self.all_levels = (
            [f"C{i}" for i in range(2, 8)] +
            [f"T{i}" for i in range(1, 13)] +
            [f"L{i}" for i in range(1, 6)] +
            ["S1", "S2AI"]
        )

        # anchor options
        self.anchor_types_general = ["None", "Screw", "Hook", "Tape"]

        self.hook_types = ["Laminar Hook", "Pedicle Hook", "Transverse Process Hook", "Other"]
        self.tape_types = ["Nile Alternative Fixation", "BandLoc", "Other"]

        self.screw_types_general = ["Monoaxial", "Uniaxial", "Polyaxial", "Cannulated"]

        self._last_overage_keys = set()
        self._popup_after_id = None
        self._popup_in_progress = False

        self.level_rows = []
        self._loading_state = False
        self._last_changed_side = None  # tracks (row_model_index, side) of last selection


    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Anchor Selection",
            back_command=self.app.setup_page_6,
            next_command=self._next_to_page_11_soft_stop
        )

        ttk.Label(
            scrollable,
            text="Select levels and use Add to insert another level row.",
            font=FONT,
            background=WHITE,
            justify="left"
        ).pack(anchor="w", pady=(6, 10))

        btn_row = ttk.Frame(scrollable)
        btn_row.pack(fill="x", pady=(0, 10))

        ttk.Button(
            btn_row,
            text="Add Level",
            style="Green.TButton",
            command=self.add_level_row
        ).pack(side="left", padx=(0, 8))

        self.btn_remove_top = ttk.Button(
            btn_row,
            text="Remove Top",
            style="Light.TButton",
            command=self.remove_top_row
        )
        self.btn_remove_top.pack(side="left", padx=(12, 8))

        self.btn_remove_bottom = ttk.Button(
            btn_row,
            text="Remove Bottom",
            style="Light.TButton",
            command=self.remove_bottom_row
        )
        self.btn_remove_bottom.pack(side="left")

        container = ttk.LabelFrame(scrollable, text="Levels and Anchor Planning")
        container.pack(fill="x", pady=(0, 10))

        self.levels_frame = ttk.Frame(container)
        self.levels_frame.pack(fill="x", padx=10, pady=10)

        # reset state each time
        self.level_vars = []
        self.level_combos = []
        self.row_models = []
        self.level_rows = []

        self._restore_from_plan_data()
        self._update_remove_buttons()

        # Inventory section
        inv_frame = ttk.LabelFrame(scrollable, text="Hospital Inventory")
        inv_frame.pack(fill="x", pady=(10, 10))

        ttk.Button(
            inv_frame,
            text="Reload Inventory from Database",
            style="Green.TButton",
            command=self._on_reload_inventory
        ).pack(anchor="w", padx=10, pady=10)

        self.inventory_status_label = tk.Label(
            inv_frame,
            text="Inventory not loaded.",
            font=("Segoe UI", 10),
            bg=WHITE
        )
        self.inventory_status_label.pack(anchor="w", padx=10, pady=(0, 10))

        self._try_load_inventory()

    # -------------------------
    # Navigation
    # -------------------------
    def _next_to_page_11_soft_stop(self):
        selected_levels = [v.get().strip() for v in self.level_vars if v.get().strip()]
        if len(selected_levels) < 2:
            messagebox.showwarning("Incomplete", "Please select at least 2 levels before continuing.")
            return

        missing = self._get_missing_required_fields()
        if missing:
            msg = (
                "Accurately entering the requested data allows:\n"
                "• Level Selection Recommendation\n"
                "• Rod Length Prediction\n"
                "• Rod Bending Instructions\n\n"
                "Missing fields:\n"
                + "\n".join(f"• {m}" for m in missing)
                + "\n\nContinue anyway?"
            )
            go_on = messagebox.askyesno("Incomplete Anchor Selection", msg)
            if not go_on:
                return

        self.app.setup_page_11()

    # -------------------------
    # Row management
    # -------------------------
    def add_level_row(self, preset_level: str = ""):
        var = tk.StringVar(value=preset_level)
        self.level_vars.append(var)

        row = ttk.Frame(self.levels_frame)
        row.pack(fill="x", pady=6)
        self.level_rows.append(row)

        idx = len(self.level_vars)

        ttk.Label(row, text=f"Level {idx}:", font=FONT).grid(row=0, column=0, sticky="w", padx=(0, 10))

        combo = ttk.Combobox(
            row,
            textvariable=var,
            values=self.all_levels,
            state="readonly",
            width=8
        )
        combo.grid(row=0, column=1, sticky="w")
        self._bind_mousewheel_combo(combo)
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_level_change())

        self.level_combos.append(combo)

        model = self._build_side_planners(row)
        self.row_models.append(model)

        btn_remove = ttk.Button(
            row,
            text="Remove",
            style="Light.TButton",
            command=lambda r=row: self.remove_specific_row(r)
        )
        btn_remove.grid(row=0, column=3, sticky="e", padx=(12, 0))

        row.grid_columnconfigure(0, weight=0)
        row.grid_columnconfigure(1, weight=0)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=0)

        self._update_remove_buttons()

        if not self._loading_state:
            self._persist_levels_and_anchors()

    def remove_top_row(self):
        if len(self.level_vars) <= 1:
            return

        first_combo = self.level_combos[0]
        first_combo.master.destroy()

        self.level_vars.pop(0)
        self.level_combos.pop(0)
        self.row_models.pop(0)
        self.level_rows.pop(0)

        self._relabel_rows()
        self._on_level_change()
        self._update_remove_buttons()
        self._persist_levels_and_anchors()

    def remove_bottom_row(self):
        if len(self.level_vars) <= 1:
            return

        last_combo = self.level_combos[-1]
        last_combo.master.destroy()

        self.level_vars.pop()
        self.level_combos.pop()
        self.row_models.pop()
        self.level_rows.pop()

        self._relabel_rows()
        self._on_level_change()
        self._update_remove_buttons()
        self._persist_levels_and_anchors()

    def _relabel_rows(self):
        for i, combo in enumerate(self.level_combos, start=1):
            row = combo.master
            for w in row.winfo_children():
                if isinstance(w, ttk.Label) and w.cget("text").startswith("Level "):
                    w.configure(text=f"Level {i}:")
                    break

    def remove_specific_row(self, row_frame: ttk.Frame):
        if len(self.level_vars) <= 1:
            return

        try:
            idx = self.level_rows.index(row_frame)
        except ValueError:
            return

        row_frame.destroy()

        self.level_rows.pop(idx)
        self.level_vars.pop(idx)
        self.level_combos.pop(idx)
        self.row_models.pop(idx)

        self._relabel_rows()
        self._on_level_change()
        self._update_remove_buttons()

        if not self._loading_state:
            self._persist_levels_and_anchors()

    # -------------------------
    # Validation: levels
    # -------------------------
    def _on_level_change(self):
        seen = set()
        for i, var in enumerate(self.level_vars):
            v = var.get().strip()
            if not v:
                continue
            if v in seen:
                if not self._loading_state:
                    messagebox.showwarning("Duplicate Level", f"{v} is already selected.")
                var.set("")
                break
            seen.add(v)

        for i, level_var in enumerate(self.level_vars):
            level = level_var.get().strip()
            if i < len(self.row_models):
                self._apply_level_constraints_to_row(self.row_models[i], level)

        self._persist_levels_and_anchors()

    def _update_remove_buttons(self):
        state = "normal" if len(self.level_vars) > 1 else "disabled"
        if self.btn_remove_top is not None:
            self.btn_remove_top.configure(state=state)
        if self.btn_remove_bottom is not None:
            self.btn_remove_bottom.configure(state=state)

    # -------------------------
    # Mousewheel support
    # -------------------------
    def _bind_mousewheel_combo(self, combo: ttk.Combobox):
        def on_wheel(event):
            vals = list(combo["values"])
            if not vals:
                return "break"
            cur = combo.get().strip()
            try:
                i = vals.index(cur)
            except ValueError:
                i = 0
            step = -1 if getattr(event, "delta", 0) > 0 else 1
            new_i = max(0, min(len(vals) - 1, i + step))
            combo.set(vals[new_i])
            self._on_level_change()
            return "break"

        combo.bind("<MouseWheel>", on_wheel)
        combo.bind("<Button-4>", lambda e: on_wheel(type("E", (), {"delta": 120})()))
        combo.bind("<Button-5>", lambda e: on_wheel(type("E", (), {"delta": -120})()))

    # -------------------------
    # Anchor planners per row
    # -------------------------
    def _build_side_planners(self, parent_row: ttk.Frame):
        block = ttk.Frame(parent_row)
        block.grid(row=0, column=2, sticky="ew", padx=(16, 0))

        ttk.Label(block, text="Left", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(block, text="Right", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(0, 10))

        left = self._build_one_side(block, col=0)
        right = self._build_one_side(block, col=1)

        block.grid_columnconfigure(0, weight=1)
        block.grid_columnconfigure(1, weight=1)

        return {"left": left, "right": right}

    def _build_one_side(self, parent: ttk.Frame, col: int):
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=col, sticky="ew", padx=(0, 14))

        anchor_var = tk.StringVar(value="None")
        ttk.Label(frame, text="Anchor", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        anchor_combo = ttk.Combobox(frame, textvariable=anchor_var, values=self.anchor_types_general, state="readonly", width=10)
        anchor_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        anchor_combo.bind("<<ComboboxSelected>>", lambda e: self._on_anchor_type_change())

        screw_type_var = tk.StringVar(value="")
        dia_var = tk.StringVar(value="")
        len_var = tk.StringVar(value="")
        tap_var = tk.BooleanVar(value=False)

        screw_frame = ttk.Frame(frame)
        screw_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        ttk.Label(screw_frame, text="Screw Type", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        screw_type_combo = ttk.Combobox(
            screw_frame,
            textvariable=screw_type_var,
            values=self.screw_types_general,
            state="readonly",
            width=12
        )
        screw_type_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        screw_type_combo.bind("<<ComboboxSelected>>", lambda e: self._on_screw_type_change(frame))

        ttk.Label(screw_frame, text="Diameter", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 0))
        dia_combo = ttk.Combobox(screw_frame, textvariable=dia_var, values=[], state="readonly", width=12)
        dia_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        dia_combo.bind("<<ComboboxSelected>>", lambda e: self._on_diameter_change(frame))

        ttk.Label(screw_frame, text="Length", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=(4, 0))
        len_combo = ttk.Combobox(screw_frame, textvariable=len_var, values=[], state="readonly", width=12)
        len_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        len_combo.bind("<<ComboboxSelected>>", lambda e: self._on_length_change(frame))

        tap_frame = ttk.Frame(frame)
        tap_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        def on_tap_toggle():
            sm2 = self._find_side_model_by_frame(frame)
            if sm2 is None:
                return
            self._update_tap_label(sm2)
            self._persist_levels_and_anchors()

        tap_check = ttk.Checkbutton(tap_frame, text="Tap", variable=tap_var, command=on_tap_toggle)
        tap_check.grid(row=0, column=0, sticky="w")

        tap_label = ttk.Label(tap_frame, text="", font=("Segoe UI", 10))
        tap_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        hook_var = tk.StringVar(value="")
        hook_frame = ttk.Frame(frame)
        hook_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(hook_frame, text="Hook Type", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        hook_combo = ttk.Combobox(hook_frame, textvariable=hook_var, values=self.hook_types, state="readonly", width=18)
        hook_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        hook_combo.bind("<<ComboboxSelected>>", lambda e: self._persist_levels_and_anchors())

        tape_var = tk.StringVar(value="")
        tape_frame = ttk.Frame(frame)
        tape_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(tape_frame, text="Tape Type", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        tape_combo = ttk.Combobox(tape_frame, textvariable=tape_var, values=self.tape_types, state="readonly", width=22)
        tape_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        tape_combo.bind("<<ComboboxSelected>>", lambda e: self._persist_levels_and_anchors())

        notes = tk.Text(frame, width=28, height=3, font=("Segoe UI", 10))
        ttk.Label(frame, text="Notes", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        notes.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        notes.bind("<KeyRelease>", lambda e: self._persist_levels_and_anchors())

        screw_frame.grid_remove()
        hook_frame.grid_remove()
        tape_frame.grid_remove()
        tap_frame.grid_remove()

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)

        return {
            "frame": frame,
            "anchor_var": anchor_var,
            "anchor_combo": anchor_combo,
            "screw_frame": screw_frame,
            "screw_type_var": screw_type_var,
            "screw_type_combo": screw_type_combo,
            "dia_var": dia_var,
            "dia_combo": dia_combo,
            "len_var": len_var,
            "len_combo": len_combo,
            "tap_frame": tap_frame,
            "tap_var": tap_var,
            "tap_check": tap_check,
            "tap_label": tap_label,
            "hook_frame": hook_frame,
            "hook_var": hook_var,
            "hook_combo": hook_combo,
            "tape_frame": tape_frame,
            "tape_var": tape_var,
            "tape_combo": tape_combo,
            "notes": notes,
        }

    def _on_anchor_type_change(self):
        for model in self.row_models:
            for side in ("left", "right"):
                sm = model[side]
                anchor = sm["anchor_var"].get().strip()

                sm["screw_frame"].grid_remove()
                sm["hook_frame"].grid_remove()
                sm["tape_frame"].grid_remove()
                sm["tap_frame"].grid_remove()

                if anchor == "Screw":
                    sm["screw_frame"].grid()
                    self._refresh_screw_type_and_dims_for_side(sm)
                    self._update_tap_visibility(sm)
                elif anchor == "Hook":
                    sm["hook_frame"].grid()
                elif anchor == "Tape":
                    sm["tape_frame"].grid()

        self._persist_levels_and_anchors()

    def _apply_level_constraints_to_row(self, row_model: dict, level: str):
        is_s2ai = (level == "S2AI")
        for side in ("left", "right"):
            sm = row_model[side]

            if is_s2ai:
                sm["anchor_combo"].configure(values=["Screw"], state="readonly")
                sm["anchor_var"].set("Screw")

                sm["screw_type_combo"].configure(values=["Polyaxial", "Cannulated"], state="readonly")
                if sm["screw_type_var"].get().strip() not in ("Polyaxial", "Cannulated"):
                    sm["screw_type_var"].set("Polyaxial")

                sm["screw_frame"].grid()
                sm["hook_frame"].grid_remove()
                sm["tape_frame"].grid_remove()

                self._refresh_diams_for_side(sm)
                self._refresh_lengths_for_side(sm)
                self._update_tap_visibility(sm)
            else:
                sm["anchor_combo"].configure(values=self.anchor_types_general, state="readonly")
                sm["screw_type_combo"].configure(values=self.screw_types_general, state="readonly")

    # -------------------------
    # Screw filtering (uses inventory if loaded)
    # -------------------------
    def _inventory_loaded(self) -> bool:
        return hasattr(self.app, "inventory_totals") and isinstance(self.app.inventory_totals, dict) and len(self.app.inventory_totals) > 0

    def _get_available_diameters(self, screw_type: str):
        if not self._inventory_loaded():
            return []
        out = set()
        for (t, dia, length), total in self.app.inventory_totals.items():
            if t == screw_type:
                out.add(dia)
        return sorted(out)

    def _get_available_lengths(self, screw_type: str, diameter: float):
        if not self._inventory_loaded():
            return []
        out = set()
        for (t, dia, length), total in self.app.inventory_totals.items():
            if t == screw_type and float(dia) == float(diameter):
                out.add(int(length))
        return sorted(out)

    def _refresh_screw_type_and_dims_for_side(self, sm: dict):
        if not self._inventory_loaded():
            sm["dia_combo"].configure(values=[])
            sm["len_combo"].configure(values=[])
            return

        cur_type = sm["screw_type_var"].get().strip()
        if not cur_type:
            sm["screw_type_var"].set("Polyaxial")

        self._refresh_diams_for_side(sm)
        self._refresh_lengths_for_side(sm)

    def _refresh_diams_for_side(self, sm: dict):
        st = sm["screw_type_var"].get().strip()
        if not st or not self._inventory_loaded():
            sm["dia_combo"].configure(values=[])
            sm["dia_var"].set("")
            sm["len_combo"].configure(values=[])
            sm["len_var"].set("")
            return

        diams = self._get_available_diameters(st)
        sm["dia_combo"].configure(values=[str(d) for d in diams])

        cur_d = sm["dia_var"].get().strip()
        if cur_d:
            try:
                if float(cur_d) not in diams:
                    sm["dia_var"].set("")
            except Exception:
                sm["dia_var"].set("")

        if sm["dia_var"].get().strip() == "":
            sm["len_combo"].configure(values=[])
            sm["len_var"].set("")

    def _refresh_lengths_for_side(self, sm: dict):
        st = sm["screw_type_var"].get().strip()
        d = sm["dia_var"].get().strip()
        if not st or not d or not self._inventory_loaded():
            sm["len_combo"].configure(values=[])
            sm["len_var"].set("")
            return

        try:
            dia = float(d)
        except Exception:
            sm["len_combo"].configure(values=[])
            sm["len_var"].set("")
            return

        lengths = self._get_available_lengths(st, dia)
        sm["len_combo"].configure(values=[str(L) for L in lengths])

        cur_L = sm["len_var"].get().strip()
        if cur_L:
            try:
                if int(float(cur_L)) not in lengths:
                    sm["len_var"].set("")
            except Exception:
                sm["len_var"].set("")

    def _on_screw_type_change(self, side_frame: ttk.Frame):
        sm = self._find_side_model_by_frame(side_frame)
        if sm is None:
            return
        sm["dia_var"].set("")
        sm["len_var"].set("")
        sm["tap_var"].set(False)
        sm["tap_label"].configure(text="")
        self._refresh_diams_for_side(sm)
        self._refresh_lengths_for_side(sm)
        self._update_tap_visibility(sm)
        self._persist_levels_and_anchors()

    def _on_diameter_change(self, side_frame: ttk.Frame):
        sm = self._find_side_model_by_frame(side_frame)
        if sm is None:
            return
        sm["len_var"].set("")
        sm["tap_var"].set(False)
        sm["tap_label"].configure(text="")
        self._refresh_lengths_for_side(sm)
        self._update_tap_visibility(sm)
        self._persist_levels_and_anchors()

    def _on_length_change(self, side_frame: ttk.Frame):
        sm = self._find_side_model_by_frame(side_frame)
        if sm is None:
            return
        self._update_tap_visibility(sm)
        self._update_tap_label(sm)
        # Record this as the last side touched
        self._last_changed_side = sm
        self._persist_levels_and_anchors()

    def _update_tap_visibility(self, sm: dict):
        st = sm["screw_type_var"].get().strip()
        d = sm["dia_var"].get().strip()
        L = sm["len_var"].get().strip()

        if st and d and L:
            sm["tap_frame"].grid()
        else:
            sm["tap_var"].set(False)
            sm["tap_label"].configure(text="")
            sm["tap_frame"].grid_remove()

    def _update_tap_label(self, sm: dict):
        if not sm["tap_var"].get():
            sm["tap_label"].configure(text="")
            return
        d = sm["dia_var"].get().strip()
        try:
            dia = float(d)
        except Exception:
            sm["tap_label"].configure(text="")
            return
        sm["tap_label"].configure(text=f"Tap diameter = {dia - 1.0:.1f} mm")

    def _find_side_model_by_frame(self, frame: ttk.Frame):
        for rm in self.row_models:
            for side in ("left", "right"):
                if rm[side]["frame"] == frame:
                    return rm[side]
        return None

    # -------------------------
    # Persist page state
    # -------------------------
    def _persist_levels_and_anchors(self):
        self.app.plan_data.setdefault("anchor_planning", {})
        ap = self.app.plan_data["anchor_planning"]

        levels = [v.get().strip() for v in self.level_vars if v.get().strip() != ""]
        ap["levels"] = levels

        anchors = {}
        for i, level_var in enumerate(self.level_vars):
            level = level_var.get().strip()
            if not level or i >= len(self.row_models):
                continue
            rm = self.row_models[i]
            anchors[level] = {
                "left": self._serialize_side(rm["left"]),
                "right": self._serialize_side(rm["right"]),
            }

        ap["anchors"] = anchors
        self.app.is_dirty = True
        if not self._loading_state:
            self._update_inventory_warnings()

    def _serialize_side(self, sm: dict):
        anchor = sm["anchor_var"].get().strip()
        notes = sm["notes"].get("1.0", "end").strip()

        if anchor == "Screw":
            return {
                "anchor_type": "Screw",
                "screw_type": sm["screw_type_var"].get().strip(),
                "diameter_mm": sm["dia_var"].get().strip(),
                "length_mm": sm["len_var"].get().strip(),
                "tap": bool(sm["tap_var"].get()),
                "notes": notes,
            }
        if anchor == "Hook":
            return {
                "anchor_type": "Hook",
                "hook_type": sm["hook_var"].get().strip(),
                "notes": notes,
            }
        if anchor == "Tape":
            return {
                "anchor_type": "Tape",
                "tape_type": sm["tape_var"].get().strip(),
                "notes": notes,
            }

        return {"anchor_type": "None", "notes": notes}

    def _restore_from_plan_data(self):
        ap = self.app.plan_data.get("anchor_planning", {})
        saved_levels = ap.get("levels", [])
        saved_anchors = ap.get("anchors", {})

        if not isinstance(saved_levels, list):
            saved_levels = []
        if not isinstance(saved_anchors, dict):
            saved_anchors = {}

        if len(saved_levels) == 0:
            self.add_level_row()
            self._persist_levels_and_anchors()
            return

        self._loading_state = True
        try:
            for lvl in saved_levels:
                self.add_level_row(preset_level=str(lvl).strip())

            for i, level_var in enumerate(self.level_vars):
                level = level_var.get().strip()
                if not level or i >= len(self.row_models):
                    continue

                rm = self.row_models[i]
                level_data = saved_anchors.get(level, {})

                self._apply_side_data(rm["left"], level_data.get("left", {}))
                self._apply_side_data(rm["right"], level_data.get("right", {}))
                self._apply_level_constraints_to_row(rm, level)

            self._on_level_change()
        finally:
            self._loading_state = False

        self._persist_levels_and_anchors()

    def _apply_side_data(self, sm: dict, data: dict):
        if not isinstance(data, dict):
            data = {}

        anchor_type = (data.get("anchor_type") or "None").strip()
        if anchor_type not in self.anchor_types_general:
            anchor_type = "None"

        sm["anchor_var"].set(anchor_type)

        notes = data.get("notes", "")
        try:
            sm["notes"].delete("1.0", "end")
            sm["notes"].insert("1.0", str(notes))
        except Exception:
            pass

        sm["screw_frame"].grid_remove()
        sm["hook_frame"].grid_remove()
        sm["tape_frame"].grid_remove()
        sm["tap_frame"].grid_remove()

        if anchor_type == "Screw":
            sm["screw_frame"].grid()
            sm["screw_type_var"].set((data.get("screw_type") or "").strip())
            sm["dia_var"].set(str(data.get("diameter_mm") or "").strip())
            sm["len_var"].set(str(data.get("length_mm") or "").strip())
            sm["tap_var"].set(bool(data.get("tap", False)))
            self._refresh_diams_for_side(sm)
            self._refresh_lengths_for_side(sm)
            self._update_tap_visibility(sm)
            self._update_tap_label(sm)

        elif anchor_type == "Hook":
            sm["hook_frame"].grid()
            sm["hook_var"].set((data.get("hook_type") or "").strip())

        elif anchor_type == "Tape":
            sm["tape_frame"].grid()
            sm["tape_var"].set((data.get("tape_type") or "").strip())

    # -------------------------
    # Inventory warnings
    # -------------------------
    def _update_inventory_warnings(self):
        if not hasattr(self.app, "inventory_totals") or not isinstance(self.app.inventory_totals, dict):
            return
        if len(self.app.inventory_totals) == 0:
            return

        root = None
        try:
            if self.levels_frame is not None:
                root = self.levels_frame.winfo_toplevel()
        except Exception:
            root = None
        if root is None:
            root = getattr(self.app, "root", None)

        usage = recompute_usage_from_plan(self.app.plan_data)
        over = compute_overages(usage, self.app.inventory_totals)
        msgs = format_overage_messages(over)

        print("\n=== INVENTORY OVERAGE CHECK ===")

        if not over:
            print("No overages detected.")
            self.app.inventory_overage_messages = []
            self._last_overage_keys = set()
            if self._popup_after_id is not None and root is not None:
                try:
                    root.after_cancel(self._popup_after_id)
                except Exception:
                    pass
                self._popup_after_id = None
            return

        for m in msgs:
            print(m)

        self.app.inventory_overage_messages = msgs

        current_keys = {tuple(o["key"]) for o in over}
        new_keys = current_keys - self._last_overage_keys

        if new_keys and root is not None:
            popup_msgs = []
            for o in over:
                if tuple(o["key"]) in new_keys:
                    t, d, L = o["key"]
                    popup_msgs.append(
                        f"⚠️ Warning: {o['used']} screws of type {d} × {L} mm {t} exceed stock ({o['available']} available)"
                    )

            popup_text = "\n".join(popup_msgs)

            if self._popup_after_id is not None:
                try:
                    root.after_cancel(self._popup_after_id)
                except Exception:
                    pass
                self._popup_after_id = None

            captured_side = self._last_changed_side

            def _show_popup(new_keys=new_keys, over=over, captured_side=captured_side):
                self._popup_after_id = None
                if self._popup_in_progress:
                    return
                self._popup_in_progress = True
                try:
                    keep = self._ask_overage(popup_text)
                    if not keep:
                        self._last_changed_side = captured_side
                        self._clear_overage_selections(new_keys, over)
                finally:
                    self._popup_in_progress = False

            self._popup_after_id = root.after(150, _show_popup)

        self._last_overage_keys = current_keys

    def _ask_overage(self, message: str) -> bool:
        """
        Custom dialog replacing askyesno so we can label the buttons ourselves.
        Returns True = keep selection, False = clear selection.
        """
        result = [True]  # default: keep

        dlg = tk.Toplevel()
        dlg.title("Inventory Overage Detected")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text=message, justify="left", wraplength=420,
                 font=("Segoe UI", 10), padx=20, pady=16).pack()

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=(0, 16))

        def on_keep():
            result[0] = True
            dlg.destroy()

        def on_clear():
            result[0] = False
            dlg.destroy()

        tk.Button(btn_frame, text="Keep & Contact Supplier",
                  width=24, command=on_keep).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Clear Selection",
                  width=18, command=on_clear).pack(side="left", padx=8)

        dlg.update_idletasks()
        w, h = dlg.winfo_width(), dlg.winfo_height()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        dlg.wait_window()
        return result[0]

    def _clear_overage_selections(self, overage_keys: set, over: list):
        """
        Clears only the most recently changed screw selection that caused the overage.
        """
        sm = self._last_changed_side
        if sm is None:
            return

        self._loading_state = True
        try:
            sm["screw_type_var"].set("")
            sm["dia_var"].set("")
            sm["len_var"].set("")
            sm["tap_var"].set(False)
            sm["tap_label"].configure(text="")
            sm["tap_frame"].grid_remove()
            sm["anchor_var"].set("None")
            sm["screw_frame"].grid_remove()
            self._refresh_diams_for_side(sm)
            self._refresh_lengths_for_side(sm)
        finally:
            self._loading_state = False

        self._last_changed_side = None
        self._persist_levels_and_anchors()

    # -------------------------
    # Inventory loading (SQL)
    # -------------------------
    def _load_inventory(self):
        """Load inventory directly from SQL Server. No file needed."""
        totals, rows = load_inventory_sql()
        ok, msg, _stats = validate_inventory_data(totals, rows)
        if not ok:
            raise ValueError(msg)

        self.app.inventory_totals = totals
        self.app.inventory_rows = rows

        if self.inventory_status_label is not None:
            self.inventory_status_label.configure(text=msg)

        # Refresh dropdowns for already-selected screw blocks
        for rm in self.row_models:
            for side in ("left", "right"):
                sm = rm[side]
                if sm["anchor_var"].get().strip() == "Screw":
                    self._refresh_screw_type_and_dims_for_side(sm)
                    self._update_tap_visibility(sm)
                    self._update_tap_label(sm)

        self.app.is_dirty = True
        self._last_overage_keys = set()
        self._persist_levels_and_anchors()

    def _try_load_inventory(self):
        """Silently attempt to load inventory on page open."""
        try:
            if self.inventory_status_label is not None:
                self.inventory_status_label.configure(text="Connecting to database...")
            self._load_inventory()
        except Exception as e:
            if self.inventory_status_label is not None:
                self.inventory_status_label.configure(
                    text=f"Inventory load failed: {e}"
                )

    def _on_reload_inventory(self):
        """Called when user clicks 'Reload Inventory from Database'."""
        try:
            self._load_inventory()
        except Exception as e:
            messagebox.showerror("Inventory Load Failed", str(e))

    # -------------------------
    # Missing fields check
    # -------------------------
    def _get_missing_required_fields(self):
        missing = []

        for i, level_var in enumerate(self.level_vars):
            level = level_var.get().strip()
            if not level or i >= len(self.row_models):
                continue

            rm = self.row_models[i]
            for side_name in ("left", "right"):
                sm = rm[side_name]
                anchor = sm["anchor_var"].get().strip()

                if anchor == "None":
                    missing.append(f"{level} [{side_name}]: Anchor type not selected")
                    continue

                if anchor == "Screw":
                    if not sm["screw_type_var"].get().strip():
                        missing.append(f"{level} [{side_name}]: Screw type missing")
                    if not sm["dia_var"].get().strip():
                        missing.append(f"{level} [{side_name}]: Diameter missing")
                    if not sm["len_var"].get().strip():
                        missing.append(f"{level} [{side_name}]: Length missing")

                if anchor == "Hook":
                    if not sm["hook_var"].get().strip():
                        missing.append(f"{level} [{side_name}]: Hook type missing")

                if anchor == "Tape":
                    if not sm["tape_var"].get().strip():
                        missing.append(f"{level} [{side_name}]: Tape type missing")

        return missing