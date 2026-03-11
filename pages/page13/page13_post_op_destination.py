import tkinter as tk
from tkinter import ttk

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)


class Page13PostOpDestination:
    def __init__(self, app):
        self.app = app

        # destination
        self.destination_var = tk.StringVar(value="5A Constant Observation Unit")

        self.mgmt_notes_var = tk.StringVar(value="")
        self.notes_text = None

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Post-Op Destination",
            back_command=self.app.setup_page_12,
            next_command=self._next,  
        )
        self._persist()

        ttk.Label(
            scrollable,
            text="Please select the post-op destination.",
            font=FONT,
            background=WHITE,
            justify="left"
        ).pack(anchor="w", pady=(6, 10))

        # -------------------------
        # Destination options
        # -------------------------
        dest_frame = ttk.LabelFrame(scrollable, text="Post-Op Destination")
        dest_frame.pack(fill="x", pady=(0, 12))

        inner = ttk.Frame(dest_frame)
        inner.pack(fill="x", padx=12, pady=12)

        options = [
            "5A Constant Observation Unit",
            "PICU",
            "OICU",
        ]

        for opt in options:
            ttk.Radiobutton(
                inner,
                text=opt,
                value=opt,
                variable=self.destination_var,
                command=self._persist
            ).pack(anchor="w", pady=2)

        # -------------------------
        # Post-Operative Management
        # -------------------------
        mgmt_frame = ttk.LabelFrame(scrollable, text="Post-Operative Management")
        mgmt_frame.pack(fill="both", expand=True, pady=(0, 8))

        mgmt_inner = ttk.Frame(mgmt_frame)
        mgmt_inner.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(
            mgmt_inner,
            text="Notes:",
            font=("Segoe UI", 10),
            background=WHITE
        ).pack(anchor="w", pady=(0, 6))

        self.notes_text = tk.Text(
            mgmt_inner,
            height=6,
            font=("Segoe UI", 11),
            wrap="word"
        )
        self.notes_text.pack(fill="both", expand=True)
        self.notes_text.bind("<KeyRelease>", lambda e: self._persist())

        self._restore()

    # -------------------------
    # Persist/restore
    # -------------------------
    def _persist(self):
        self.app.plan_data.setdefault("post_op", {})
        po = self.app.plan_data["post_op"]

        po["destination"] = self.destination_var.get().strip()

        if self.notes_text is not None:
            po["post_op_management_notes"] = self.notes_text.get("1.0", "end").strip()
        else:
            po["post_op_management_notes"] = self.mgmt_notes_var.get().strip()

        self.app.is_dirty = True

    def _restore(self):
        po = self.app.plan_data.get("post_op", {})
        if not isinstance(po, dict):
            po = {}

        dest = str(po.get("destination", "")).strip()
        if dest:
            self.destination_var.set(dest)
        else:
            self.destination_var.set("5A Constant Observation Unit")  # default selection 

        notes = str(po.get("post_op_management_notes", "")).strip()
        if self.notes_text is not None:
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", notes)

    # -------------------------
    # Navigation
    # -------------------------
    def _next(self):
        self._persist()
        self.app.setup_page_14()

