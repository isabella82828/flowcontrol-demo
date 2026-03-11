import tkinter as tk
from tkinter import ttk, messagebox
import os
import openpyxl
import re

from .rodfather.bin_overview import compute_bin_overview

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)

class Page11RodSelection:
    def __init__(self, app):
        self.app = app

        # Rod diameter dropdown vars
        self.left_rod_var = tk.StringVar(value="")
        self.right_rod_var = tk.StringVar(value="")

        # Cross-connector widgets/state
        self.cross_connector_var = tk.BooleanVar(value=False)
        self.cross_options = []  # computed from Page 1 levels
        self.cross_selected = []  # list[str], max len 2

        self.other_rod_var = tk.StringVar(value="")

        # UI refs
        self.cross_section_frame = None
        self.cross_checks_frame = None
        self.cross_summary_label = None

        # Checkbox state
        self.cross_check_vars = {}


        self.rod_options = [
            "Cobalt Chrome 6.0 mm",
            "Cobalt Chrome 5.5 mm",
            "Titanium 5.5 mm",
            "Titanium 6.0 mm",
        ]
        
        # Rod Father Excel path
        self.rodfather_path = os.path.join(
            os.path.dirname(__file__),
            "rodfather",
            "Rod-Father.xlsx"
        )

        # Rod Father data (loaded from Excel)
        self.offcuts = []  # list[dict]
        self.offcuts_load_error = None

        # Query UI vars
        self.q_material_var = tk.StringVar(value="Titanium")
        self.q_shape_var = tk.StringVar(value="Hex")
        self.q_min_len_var = tk.StringVar(value="")

        # Selected offcuts for plan
        self.left_offcut_id_var = tk.StringVar(value="")
        self.right_offcut_id_var = tk.StringVar(value="")

        # UI refs
        self.offcuts_tree = None
        self.offcuts_status_label = None

        # Bin overview UI refs
        self.bin_overview_frame = None
        self.bin_overview_labels = {}  # bin_size -> ttk.Label

        # Request-based allocation UI vars 
        self.req_material_var = tk.StringVar(value="Titanium")
        self.req_shape_var = tk.StringVar(value="Hex")
        self.req_length_var = tk.StringVar(value="")   
        self.req_side_var = tk.StringVar(value="left") 

        self.req_material_var.trace_add("write", lambda *_: (self._update_bin_overview(), self._run_offcut_query()))
        self.req_shape_var.trace_add("write", lambda *_: (self._update_bin_overview(), self._run_offcut_query()))

        # UI refs (new)
        self.alloc_status_label = None

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Rod Selection",
            back_command=self.app.setup_page_10,
            next_command=self.app.setup_page_12  
        )

        ttk.Label(
            scrollable,
            text="Select left and right rod diameters, and optionally add a cross-connector.",
            font=FONT,
            background=WHITE,
            justify="left"
        ).pack(anchor="w", pady=(6, 10))

        # -------------------------
        # Rod selection table-ish layout
        # -------------------------
        table = ttk.LabelFrame(scrollable, text="Rod Selection")
        table.pack(fill="x", pady=(0, 12), padx=0)

        inner = ttk.Frame(table)
        inner.pack(fill="x", padx=12, pady=12)

        ttk.Label(inner, text="", font=FONT).grid(row=0, column=0, sticky="w")
        ttk.Label(inner, text="Left Side", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(inner, text="Right Side", font=("Segoe UI", 11, "bold")).grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Label(inner, text=" ", font=("Segoe UI", 11, "bold")).grid(row=0, column=3, sticky="w", padx=(8, 0))

        ttk.Label(inner, text="Rod Diameter", font=FONT).grid(row=1, column=0, sticky="w", pady=(8, 0))

        left_combo = ttk.Combobox(
            inner,
            textvariable=self.left_rod_var,
            values=self.rod_options,
            state="readonly",
            width=24
        )
        left_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        left_combo.bind("<<ComboboxSelected>>", lambda e: self._persist())

        right_combo = ttk.Combobox(
            inner,
            textvariable=self.right_rod_var,
            values=self.rod_options,
            state="readonly",
            width=24
        )
        right_combo.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
        right_combo.bind("<<ComboboxSelected>>", lambda e: self._persist())

        other_frame = ttk.Frame(inner)
        other_frame.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(other_frame, text="Other:", font=FONT).pack(side="left")

        other_entry = ttk.Entry(other_frame, textvariable=self.other_rod_var, width=18)
        other_entry.pack(side="left", padx=(6, 0))
        other_entry.bind("<KeyRelease>", lambda e: self._persist())

        inner.grid_columnconfigure(0, weight=0)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_columnconfigure(2, weight=1)
        inner.grid_columnconfigure(3, weight=1)

        # -------------------------
        # Cross connector
        # -------------------------
        cc_frame = ttk.LabelFrame(scrollable, text="Cross Connector")
        cc_frame.pack(fill="x", pady=(0, 10))

        cc_inner = ttk.Frame(cc_frame)
        cc_inner.pack(fill="x", padx=12, pady=12)

        cc_check = ttk.Checkbutton(
            cc_inner,
            text="Cross-Connector",
            variable=self.cross_connector_var,
            command=self._on_cross_toggle
        )
        cc_check.pack(anchor="w")

        self.cross_section_frame = ttk.Frame(cc_inner)
        self.cross_section_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            self.cross_section_frame,
            text="Select up to 2 levels for cross-connector placement:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 6))

        # container for dynamic checkboxes
        self.cross_checks_frame = ttk.Frame(self.cross_section_frame)
        self.cross_checks_frame.pack(fill="x")

        self.cross_summary_label = ttk.Label(
            self.cross_section_frame,
            text="Selected: None",
            font=("Segoe UI", 10)
        )
        self.cross_summary_label.pack(anchor="w", pady=(6, 0))

        # restore and apply initial visibility
        self._restore()
        if self.cross_connector_var.get():
            self._refresh_cross_options()
        
        self._apply_cross_visibility()

        # -------------------------
        # Rod Father (offcuts) query
        # -------------------------
        rf_frame = ttk.LabelFrame(scrollable, text="Rod Father Offcuts")
        rf_frame.pack(fill="x", pady=(0, 10))

        rf_inner = ttk.Frame(rf_frame)
        rf_inner.pack(fill="x", padx=12, pady=12)

        self._load_rodfather_excel()

        # Request a rod (bin-based allocation)
        req = ttk.Frame(rf_inner)
        req.pack(fill="x", pady=(0, 8))

        ttk.Label(req, text="Material", font=FONT).grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            req,
            textvariable=self.req_material_var,
            values=["Titanium", "Cobalt Chrome"],
            state="readonly",
            width=16
        ).grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(req, text="Type", font=FONT).grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            req,
            textvariable=self.req_shape_var,
            values=["Hex", "Cylindrical"],
            state="readonly",
            width=16
        ).grid(row=0, column=3, sticky="w", padx=(6, 12))

        ttk.Label(req, text="Required length (mm)", font=FONT).grid(row=0, column=4, sticky="w")
        ttk.Entry(req, textvariable=self.req_length_var, width=10).grid(row=0, column=5, sticky="w", padx=(6, 12))

        ttk.Label(req, text="Side", font=FONT).grid(row=0, column=6, sticky="w")
        ttk.Combobox(
            req,
            textvariable=self.req_side_var,
            values=["left", "right"],
            state="readonly",
            width=8
        ).grid(row=0, column=7, sticky="w", padx=(6, 12))

        ttk.Button(req, text="Search and Allocate", command=self._allocate_requested_rod).grid(row=0, column=8, sticky="w")

        # Status line
        self.offcuts_status_label = ttk.Label(rf_inner, text="", font=("Segoe UI", 10))
        self.offcuts_status_label.pack(anchor="w", pady=(0, 6))

        self.alloc_status_label = ttk.Label(rf_inner, text="", font=("Segoe UI", 10))
        self.alloc_status_label.pack(anchor="w", pady=(0, 6))

        # -------------------------
        # Bin overview (TOTAL only)
        # -------------------------
        bin_frame = ttk.LabelFrame(rf_inner, text="Bin Overview")
        bin_frame.pack(fill="x", pady=(0, 8))

        # bin -> total label
        self.bin_labels = {}

        ttk.Label(bin_frame, text="Bin (mm)", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=8, sticky="w")
        ttk.Label(bin_frame, text="Total", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=8, sticky="e")

        row = 1
        for b in (100, 200, 300, 400, 600):
            ttk.Label(bin_frame, text=str(b)).grid(row=row, column=0, padx=8, sticky="w")

            t = ttk.Label(bin_frame, text="0")
            t.grid(row=row, column=1, padx=8, sticky="e")

            self.bin_labels[b] = t
            row += 1

        self._update_bin_overview()

        # Results table
        cols = ("Offcut ID", "Material", "Shape", "Length", "Status")
        self.offcuts_tree = ttk.Treeview(rf_inner, columns=cols, show="headings", height=6)

        for c in cols:
            self.offcuts_tree.heading(c, text=c)
            self.offcuts_tree.column(c, width=120, anchor="w")

        self.offcuts_tree.column("Length", width=80, anchor="e")
        self.offcuts_tree.column("Status", width=100, anchor="w")
        self.offcuts_tree.pack(fill="x", pady=(0, 8))

        # Actions
        actions = ttk.Frame(rf_inner)
        actions.pack(fill="x")

        ttk.Button(actions, text="Reserve for Left", command=lambda: self._reserve_selected(side="left")).pack(side="left")
        ttk.Button(actions, text="Reserve for Right", command=lambda: self._reserve_selected(side="right")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Reload Excel", command=self._reload_rodfather).pack(side="left", padx=(8, 0))

        chosen = ttk.Frame(rf_inner)
        chosen.pack(fill="x", pady=(8, 0))

        ttk.Label(chosen, text="Chosen Left Offcut:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        ttk.Label(chosen, textvariable=self.left_offcut_id_var, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(chosen, text="Chosen Right Offcut:", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w")
        ttk.Label(chosen, textvariable=self.right_offcut_id_var, font=("Segoe UI", 10, "bold")).grid(row=0, column=3, sticky="w", padx=(6, 0))

        # Initial query fill
        self._run_offcut_query()


    # -------------------------
    # Page data access
    # -------------------------
    
    def _get_construct_levels(self):
        """
        Pull construct levels from Page 10 anchor planning.
        Source of truth: plan_data["anchor_planning"]["levels"]
        """
        pd = getattr(self.app, "plan_data", {}) or {}
        ap = pd.get("anchor_planning", {})
        v = ap.get("levels", [])
        if isinstance(v, list) and v:
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    def _level_index(self, lvl: str):
        """
        Convert a level into a sortable index.
        """
        if not lvl:
            return None

        s = str(lvl).strip().upper().replace(" ", "")
        m = re.match(r"^([CTLS])(\d{1,2})$", s)
        if not m:
            return None

        region = m.group(1)
        num = int(m.group(2))

        # Big offsets so regions sort in anatomical order
        offsets = {"C": 0, "T": 100, "L": 200, "S": 300}
        return offsets[region] + num

    def _sort_and_dedupe_levels(self, levels):
        cleaned = []
        seen = set()

        for x in levels:
            s = str(x).strip().upper().replace(" ", "")
            idx = self._level_index(s)
            if idx is None:
                continue
            if s in seen:
                continue
            seen.add(s)
            cleaned.append((idx, s))

        cleaned.sort(key=lambda t: t[0])
        return [s for _, s in cleaned]

    # -------------------------
    # Cross connector logic
    # -------------------------
    
    def _refresh_cross_options(self):
        raw_levels = self._get_construct_levels()
        levels = self._sort_and_dedupe_levels(raw_levels)

        # Build adjacent pairs
        pairs = []
        indices = [self._level_index(l) for l in levels]

        for i in range(len(levels) - 1):
            a = levels[i]
            b = levels[i + 1]
            ia = indices[i]
            ib = indices[i + 1]

            if ia is None or ib is None:
                continue

            if (ib - ia) == 1:
                pairs.append(f"{a}/{b}")

        self.cross_options = pairs

        if self.cross_checks_frame is None:
            return

        for w in self.cross_checks_frame.winfo_children():
            w.destroy()

        # keep only still-valid saved selections
        self.cross_selected = [s for s in self.cross_selected if s in self.cross_options]
        if len(self.cross_selected) > 2:
            self.cross_selected = self.cross_selected[:2]

        self.cross_check_vars = {}
        for lvl in self.cross_options:
            var = tk.BooleanVar(value=(lvl in self.cross_selected))
            self.cross_check_vars[lvl] = var

            cb = ttk.Checkbutton(
                self.cross_checks_frame,
                text=lvl,
                variable=var,
                command=lambda L=lvl: self._on_cross_checkbox_toggled(L)
            )
            cb.pack(anchor="w")

        self._update_cross_summary()


    def _on_cross_toggle(self):
        if not self.cross_connector_var.get():
            self.cross_selected = []
            for var in getattr(self, "cross_check_vars", {}).values():
                var.set(False)
            self._update_cross_summary()
        else:
            self._refresh_cross_options()

        self._apply_cross_visibility()
        self._persist()


    def _apply_cross_visibility(self):
        if self.cross_connector_var.get():
            self.cross_section_frame.pack(fill="x", pady=(10, 0))
        else:
            self.cross_section_frame.pack_forget()
        
    def _on_cross_checkbox_toggled(self, toggled_level: str):
        selected = [lvl for lvl, var in self.cross_check_vars.items() if var.get()]

        if len(selected) > 2:
            self.cross_check_vars[toggled_level].set(False)
            messagebox.showwarning("Limit Reached", "You can select up to 2 cross-connector levels.")
            selected = [lvl for lvl, var in self.cross_check_vars.items() if var.get()]

        self.cross_selected = selected
        self._update_cross_summary()
        self._persist()


    def _update_cross_summary(self):
        if self.cross_summary_label is None:
            return
        if not self.cross_selected:
            self.cross_summary_label.configure(text="Selected: None")
        else:
            self.cross_summary_label.configure(text="Selected: " + ", ".join(self.cross_selected))

    # -------------------------
    # Persist/restore
    # -------------------------
    def _persist(self):
        self.app.plan_data.setdefault("rod_selection", {})
        rs = self.app.plan_data["rod_selection"]

        rs["left_rod"] = self.left_rod_var.get().strip()
        rs["right_rod"] = self.right_rod_var.get().strip()
        rs["other_rod"] = self.other_rod_var.get().strip()

        rs["cranial_cross_connector"] = bool(self.cross_connector_var.get())
        rs["cross_connector_positions"] = list(self.cross_selected)

        rs["left_offcut_id"] = self.left_offcut_id_var.get().strip()
        rs["right_offcut_id"] = self.right_offcut_id_var.get().strip()

        self.app.is_dirty = True

    def _restore(self):
        rs = self.app.plan_data.get("rod_selection", {})
        if not isinstance(rs, dict):
            rs = {}

        self.left_rod_var.set(str(rs.get("left_rod", "")).strip())
        self.right_rod_var.set(str(rs.get("right_rod", "")).strip())
        self.other_rod_var.set(str(rs.get("other_rod", "")).strip())

        self.cross_connector_var.set(bool(rs.get("cranial_cross_connector", False)))
        saved = rs.get("cross_connector_positions", [])
        if isinstance(saved, list):
            self.cross_selected = [str(x).strip() for x in saved if str(x).strip()]
        else:
            self.cross_selected = []
        
        self.left_offcut_id_var.set(str(rs.get("left_offcut_id", "")).strip())
        self.right_offcut_id_var.set(str(rs.get("right_offcut_id", "")).strip())


    # -------------------------
    # Navigation
    # -------------------------
    def _next_to_page_12(self):
        self._persist()
        if hasattr(self.app, "setup_page_12"):
            self.app.setup_page_12()
        else:
            messagebox.showinfo("Next Page", "Page 12 not implemented yet.")


    # -------------------------
    # Rod Father (Excel) logic
    # -------------------------

    def _reload_rodfather(self):
        self._load_rodfather_excel()
        self._run_offcut_query()

    def _load_rodfather_excel(self):
        self.offcuts = []
        self.offcuts_load_error = None

        if not os.path.exists(self.rodfather_path):
            self.offcuts_load_error = f"Rod Father file not found: {self.rodfather_path}"
            return

        try:
            wb = openpyxl.load_workbook(self.rodfather_path)
            if "Offcuts" not in wb.sheetnames:
                self.offcuts_load_error = "Missing sheet: Offcuts"
                return

            ws = wb["Offcuts"]

            header = []
            for cell in ws[1]:
                header.append(str(cell.value).strip() if cell.value is not None else "")

            required = ["Offcut ID", "Material", "Shape", "Length", "Status"]
            missing = [c for c in required if c not in header]
            if missing:
                self.offcuts_load_error = "Missing columns in Offcuts: " + ", ".join(missing)
                return

            idx = {name: header.index(name) for name in required}

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                offcut_id = row[idx["Offcut ID"]]
                if offcut_id is None or str(offcut_id).strip() == "":
                    continue

                material = row[idx["Material"]]
                shape = row[idx["Shape"]]
                length = row[idx["Length"]]
                status = row[idx["Status"]]

                try:
                    length_val = float(length)
                except Exception:
                    continue

                self.offcuts.append({
                    "offcut_id": str(offcut_id).strip(),
                    "material": str(material).strip() if material is not None else "",
                    "shape": str(shape).strip() if shape is not None else "",
                    "length": length_val,
                    "status": str(status).strip() if status is not None else "",
                })

        except Exception as e:
            self.offcuts_load_error = f"Failed to load Rod Father Excel: {e}"
        
        self._update_bin_overview()

    # here
    def _run_offcut_query(self):
        if self.offcuts_status_label is None or self.offcuts_tree is None:
            return

        if self.offcuts_load_error:
            self.offcuts_status_label.configure(text=self.offcuts_load_error)
            self._clear_offcuts_tree()
            return

        material = self.req_material_var.get().strip()
        shape = self.req_shape_var.get().strip()

        results = []
        for o in self.offcuts:
            if o["material"] != material:
                continue
            if o["shape"] != shape:
                continue
            if o["status"].lower() != "available":
                continue
            results.append(o)

        results.sort(key=lambda x: x["length"])
        self._fill_offcuts_tree(results)
        self.offcuts_status_label.configure(text=f"Available: {len(results)} rods for {material}, {shape}.")


    def _clear_offcuts_tree(self):
        for item in self.offcuts_tree.get_children():
            self.offcuts_tree.delete(item)

    def _fill_offcuts_tree(self, rows):
        self._clear_offcuts_tree()
        for o in rows:
            self.offcuts_tree.insert(
                "",
                "end",
                values=(o["offcut_id"], o["material"], o["shape"], f"{o['length']:.0f}", o["status"])
            )

    def _get_selected_offcut_id(self):
        if self.offcuts_tree is None:
            return None
        sel = self.offcuts_tree.selection()
        if not sel:
            return None
        values = self.offcuts_tree.item(sel[0], "values")
        if not values:
            return None
        return str(values[0]).strip()

    def _reserve_selected(self, side: str):
        offcut_id = self._get_selected_offcut_id()
        if not offcut_id:
            messagebox.showinfo("Select an offcut", "Select an offcut row first.")
            return

        ok, err = self._set_offcut_status_in_excel(offcut_id, "Reserved")
        if not ok:
            messagebox.showerror("Reserve failed", err or "Unknown error")
            return

        # Update in-memory copy
        for o in self.offcuts:
            if o["offcut_id"] == offcut_id:
                o["status"] = "Reserved"
                break

        # Persist to plan_data
        self.app.plan_data.setdefault("rod_selection", {})
        rs = self.app.plan_data["rod_selection"]

        if side == "left":
            rs["left_offcut_id"] = offcut_id
            self.left_offcut_id_var.set(offcut_id)
        else:
            rs["right_offcut_id"] = offcut_id
            self.right_offcut_id_var.set(offcut_id)

        self.app.is_dirty = True
        self._update_bin_overview()
        self._run_offcut_query()

    def _set_offcut_status_in_excel(self, offcut_id: str, new_status: str):
        if not os.path.exists(self.rodfather_path):
            return False, f"Rod Father file not found: {self.rodfather_path}"

        try:
            wb = openpyxl.load_workbook(self.rodfather_path)
            ws = wb["Offcuts"]

            header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
            if "Offcut ID" not in header or "Status" not in header:
                return False, "Offcuts sheet missing Offcut ID or Status columns."

            id_col = header.index("Offcut ID") + 1
            st_col = header.index("Status") + 1

            found_row = None
            for r in range(2, ws.max_row + 1):
                v = ws.cell(row=r, column=id_col).value
                if v is None:
                    continue
                if str(v).strip() == offcut_id:
                    found_row = r
                    break

            if found_row is None:
                return False, f"Offcut ID not found: {offcut_id}"

            ws.cell(row=found_row, column=st_col).value = new_status
            wb.save(self.rodfather_path)
            return True, None

        except Exception as e:
            return False, str(e)
    
    def _update_bin_overview(self):
        if not getattr(self, "bin_labels", None):
            return

        material = self.req_material_var.get().strip()
        shape = self.req_shape_var.get().strip()

        filtered = [
            o for o in self.offcuts
            if o.get("material") == material
            and o.get("shape") == shape
            and str(o.get("status", "")).strip().lower() == "available"
        ]

        overview = compute_bin_overview(filtered)

        for b in (100, 200, 300, 400, 600):
            lbl = self.bin_labels.get(b)
            if lbl is None:
                continue
            lbl.config(text=str(overview.get(b, {}).get("total", 0)))

    # def _required_bin(self, length_mm: float):
    #     for b in (100, 200, 300, 400, 600):
    #         if b > length_mm:
    #             return b
    #     return None


    # def _find_best_available_offcut(self, material: str, shape: str, required_len: float):
    #     min_bin = self._required_bin(required_len)
    #     if min_bin is None:
    #         return None

    #     eligible = []
    #     for o in self.offcuts:
    #         if o.get("material") != material:
    #             continue
    #         if o.get("shape") != shape:
    #             continue
    #         if str(o.get("status", "")).strip().lower() != "available":
    #             continue

    #         L = float(o.get("length", 0.0))
    #         b = self._required_bin(L - 1e-9) 

    #         if L <= 100:
    #             rod_bin = 100
    #         elif L <= 200:
    #             rod_bin = 200
    #         elif L <= 300:
    #             rod_bin = 300
    #         elif L <= 400:
    #             rod_bin = 400
    #         else:
    #             rod_bin = 600

    #         if rod_bin >= min_bin:
    #             eligible.append((rod_bin, L, o))

    #     if not eligible:
    #         return None

    #     eligible.sort(key=lambda t: (t[0], t[1]))
    #     return eligible[0][2]

    def _find_exact_available_piece(self, material: str, shape: str, required_len: float, tol: float = 0.5):
        for o in self.offcuts:
            if o.get("material") != material:
                continue
            if o.get("shape") != shape:
                continue
            if str(o.get("status", "")).strip().lower() != "available":
                continue

            try:
                L = float(o.get("length", 0.0))
            except Exception:
                continue

            if abs(L - required_len) <= tol:
                return o

        return None


    def _find_best_longer_available_piece(self, material: str, shape: str, required_len: float):
        """
        Return the available piece with length >= required_len that is closest to required_len.
        If there are multiple, choose the smallest length (closest).
        """
        candidates = []
        for o in self.offcuts:
            if o.get("material") != material:
                continue
            if o.get("shape") != shape:
                continue
            if str(o.get("status", "")).strip().lower() != "available":
                continue

            try:
                L = float(o.get("length", 0.0))
            except Exception:
                continue

            if L >= required_len:
                candidates.append((L, o))

        if not candidates:
            return None

        candidates.sort(key=lambda t: t[0])  # smallest length that is still >= required_len
        return candidates[0][1]


    def _next_offcut_id(self):
        """
        Generate a new Offcut ID by finding the max trailing number in existing IDs.
        Falls back to AUTO0001 style IDs.
        """
        max_n = 0
        for o in self.offcuts:
            s = str(o.get("offcut_id", "")).strip()
            if not s:
                continue
            m = re.search(r"(\d+)$", s)
            if not m:
                continue
            try:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
            except Exception:
                continue

        return f"AUTO{max_n + 1:04d}"


    def _append_new_offcut_to_excel(self, material: str, shape: str, length_mm: float, status: str = "Available"):
        """
        Append a new row to the Offcuts sheet, return (ok, new_id, err).
        """
        if not os.path.exists(self.rodfather_path):
            return False, None, f"Rod Father file not found: {self.rodfather_path}"

        try:
            wb = openpyxl.load_workbook(self.rodfather_path)
            if "Offcuts" not in wb.sheetnames:
                return False, None, "Missing sheet: Offcuts"

            ws = wb["Offcuts"]
            header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]

            required_cols = ["Offcut ID", "Material", "Shape", "Length", "Status"]
            missing = [c for c in required_cols if c not in header]
            if missing:
                return False, None, "Missing columns in Offcuts: " + ", ".join(missing)

            col = {name: header.index(name) + 1 for name in required_cols}

            new_id = self._next_offcut_id()
            new_row = ws.max_row + 1

            ws.cell(row=new_row, column=col["Offcut ID"]).value = new_id
            ws.cell(row=new_row, column=col["Material"]).value = material
            ws.cell(row=new_row, column=col["Shape"]).value = shape
            ws.cell(row=new_row, column=col["Length"]).value = float(length_mm)
            ws.cell(row=new_row, column=col["Status"]).value = status

            wb.save(self.rodfather_path)
            return True, new_id, None

        except Exception as e:
            return False, None, str(e)

    
    def _allocate_requested_rod(self):
        if self.alloc_status_label is None:
            return

        material = self.req_material_var.get().strip()
        shape = self.req_shape_var.get().strip()
        side = self.req_side_var.get().strip().lower()

        s = self.req_length_var.get().strip()
        if not s:
            messagebox.showwarning("Missing length", "Enter a required rod length in mm.")
            return

        try:
            required_len = float(s)
            if required_len <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Invalid length", "Required length must be a positive number.")
            return

        # 1) exact match check
        exact = self._find_exact_available_piece(material, shape, required_len)
        if exact:
            source_id = str(exact["offcut_id"]).strip()

            ok, err = self._set_offcut_status_in_excel(source_id, "Reserved")
            if not ok:
                messagebox.showerror("Allocation failed", err or "Unknown error")
                return

            for o in self.offcuts:
                if o.get("offcut_id") == source_id:
                    o["status"] = "Reserved"
                    break

            self.app.plan_data.setdefault("rod_selection", {})
            rs = self.app.plan_data["rod_selection"]
            key = "left_offcut_id" if side == "left" else "right_offcut_id"
            rs[key] = source_id

            # --- Store Rod Father allocation details for Page 14 exports ---
            rs.setdefault("rod_father", {})
            rs["rod_father"][side] = {
                "used": True,
                "mode": "exact",
                "material": material,
                "type": shape,
                "required_length_mm": float(required_len),
                "source_offcut_id": source_id,
                "source_length_mm": float(exact.get("length", required_len)),
                "leftover_length_mm": 0.0,
                "leftover_offcut_id": None,
            }

            if side == "left":
                self.left_offcut_id_var.set(source_id)
            else:
                self.right_offcut_id_var.set(source_id)

            self.app.is_dirty = True
            self._update_bin_overview()
            self._run_offcut_query()

            self.alloc_status_label.config(
                text=f"Exact match found, reserved Offcut ID {source_id} for {side}."
            )
            return

        # 2) otherwise cut from closest longer piece
        source = self._find_best_longer_available_piece(material, shape, required_len)
        if not source:
            self.alloc_status_label.config(
                text=f"No available rod found with length >= {required_len:.0f} mm for {material}, {shape}."
            )
            return

        source_id = str(source["offcut_id"]).strip()
        source_len = float(source.get("length", 0.0))
        offcut_leftover = source_len - required_len

        # confirm with user 
        leftover_line = (
            f"- New offcut created: {offcut_leftover:.0f} mm\n"
            if offcut_leftover > 0.5
            else "- New offcut created: none (leftover too small)\n"
        )

        msg = (
            f"No exact match found.\n\n"
            f"Proposed cut:\n"
            f"- Side: {side}\n"
            f"- Material: {material}\n"
            f"- Type: {shape}\n"
            f"- Required: {required_len:.0f} mm\n"
            f"- Cut from: {source_len:.0f} mm (Offcut ID {source_id})\n"
            f"{leftover_line}\n"
            f"Do you want to proceed?"
        )
        
        if not messagebox.askyesno("Confirm Cut", msg):
            self.alloc_status_label.config(text="Allocation cancelled, no changes made.")
            return

        # reserve the source piece (it gets consumed by cutting)
        ok, err = self._set_offcut_status_in_excel(source_id, "Reserved")
        if not ok:
            messagebox.showerror("Allocation failed", err or "Unknown error")
            return

        for o in self.offcuts:
            if o.get("offcut_id") == source_id:
                o["status"] = "Reserved"
                break

        # add the leftover offcut back into inventory (if meaningful)
        new_offcut_id = None
        if offcut_leftover > 0.5:  # ignore tiny leftovers, tweak threshold if you want
            ok2, new_id, err2 = self._append_new_offcut_to_excel(material, shape, offcut_leftover, status="Available")
            if not ok2:
                messagebox.showerror("Allocation failed", f"Reserved source, but failed to add leftover offcut: {err2}")
                return

            new_offcut_id = new_id

            # update in-memory list so UI refresh reflects it immediately
            self.offcuts.append({
                "offcut_id": str(new_id).strip(),
                "material": material,
                "shape": shape,
                "length": float(offcut_leftover),
                "status": "Available",
            })

        # persist chosen source for this plan side
        self.app.plan_data.setdefault("rod_selection", {})
        rs = self.app.plan_data["rod_selection"]
        key = "left_offcut_id" if side == "left" else "right_offcut_id"
        rs[key] = source_id

        # --- Store Rod Father allocation details for Page 14 exports ---
        rs.setdefault("rod_father", {})
        rs["rod_father"][side] = {
            "used": True,
            "mode": "cut",
            "material": material,
            "type": shape,
            "required_length_mm": float(required_len),
            "source_offcut_id": source_id,
            "source_length_mm": float(source_len),
            "leftover_length_mm": float(offcut_leftover),
            "leftover_offcut_id": new_offcut_id,
        }

        if side == "left":
            self.left_offcut_id_var.set(source_id)
        else:
            self.right_offcut_id_var.set(source_id)

        self.app.is_dirty = True
        self._update_bin_overview()
        self._run_offcut_query()

        if new_offcut_id:
            self.alloc_status_label.config(
                text=(
                    f"Cut {required_len:.0f} mm from {source_len:.0f} mm (Offcut ID {source_id}) for {side}, "
                    f"created {offcut_leftover:.0f} mm offcut (Offcut ID {new_offcut_id})."
                )
            )
        else:
            self.alloc_status_label.config(
                text=f"Cut {required_len:.0f} mm from {source_len:.0f} mm (Offcut ID {source_id}) for {side}, no leftover recorded."
            )