import tkinter as tk
from tkinter import ttk

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
LIGHT_GREEN = "#E8F4F4"
STRIPE_A = "#F7FAFA"
STRIPE_B = "#FFFFFF"
DIVIDER = "#D0E8E8"
FONT = ("Segoe UI", 12)

# Placeholder bending data — will be replaced by algorithm output
# Each tuple: (station_number, left_clicks, right_clicks)
MOCK_BENDING_DATA = [
    (1, 1, 1),
    (2, 6, 6),
    (3, 5, 5),
    (4, 5, 5),
    (5, 5, 5),
    (6, 4, 4),
    (7, 2, 2),
    (8, 2, 2),
    (9, 4, 4),
    (10, 3, 3),
    (11, 2, 2),
    (12, 1, 1),
    (13, 1, 1),
    (14, 1, 1),
    (15, 2, 2),
    (16, 2, 2),
    (17, 3, 3),
    (18, 2, 2),
    (19, 2, 2),
    (20, 1, 1),
    (21, 1, 1),
    (22, 2, 2),
    (23, 2, 2),
    (24, 3, 3),
    (25, 4, 4),
    (26, 3, 3),
    (27, 2, 2),
    (28, 2, 2),
    (29, 3, 3),
    (30, 3, 3),
    (31, 4, 4),
    (32, 1, 1),
]


class Page12CorrectionStrategies:
    def __init__(self, app):
        self.app = app

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Rod Bending Instructions",
            back_command=self.app.setup_page_11,
            next_command=self.app.setup_page_14
        )

        # ttk.Label(
        #     scrollable,
        #     text="SagiMetric bending instructions for the left and right rods.",
        #     font=FONT,
        #     background=WHITE,
        #     justify="left"
        # ).pack(anchor="w", pady=(6, 20))

        bending_data = self._get_bending_data()
        total_left = sum(r[1] for r in bending_data)
        total_right = sum(r[2] for r in bending_data)
        num_stations = len(bending_data)

        # ── Section title ────────────────────────────────────────────────────
        tk.Label(
            scrollable,
            text="SagiMetric Bending Instructions",
            font=("Segoe UI", 13, "bold"),
            fg="#111111",
            bg=WHITE,
        ).pack(anchor="w", pady=(0, 10))

        # ── Summary cards ────────────────────────────────────────────────────
        cards_outer = tk.Frame(scrollable, bg=WHITE)
        cards_outer.pack(fill="x", pady=(0, 20))

        card_data = [
            ("Stations", str(num_stations)),
            ("Total Left Clicks", str(total_left)),
            ("Total Right Clicks", str(total_right)),
        ]

        for col_i, (label, value) in enumerate(card_data):
            cards_outer.grid_columnconfigure(col_i, weight=1)

        for col_i, (label, value) in enumerate(card_data):
            card = tk.Frame(
                cards_outer,
                bg=LIGHT_GREEN,
                padx=0,
                pady=18,
                relief="flat",
                highlightbackground=LOGO_GREEN,
                highlightthickness=1,
            )
            card.grid(row=0, column=col_i, sticky="ew", padx=(0, 10) if col_i < 2 else 0)

            tk.Label(
                card,
                text=value,
                font=("Segoe UI", 28, "bold"),
                fg=LOGO_GREEN,
                bg=LIGHT_GREEN,
            ).pack()

            tk.Label(
                card,
                text=label,
                font=("Segoe UI", 10),
                fg="#555555",
                bg=LIGHT_GREEN,
            ).pack(pady=(2, 0))

        # ── Divider ──────────────────────────────────────────────────────────
        tk.Frame(scrollable, bg=DIVIDER, height=2).pack(fill="x", pady=(0, 16))

        # ── Subtitle ─────────────────────────────────────────────────────────
        tk.Label(
            scrollable,
            text="Values are generated automatically.",
            font=("Segoe UI", 10, "italic"),
            fg="#888888",
            bg=WHITE,
        ).pack(anchor="w", pady=(0, 10))

        # ── Treeview table ───────────────────────────────────────────────────
        style = ttk.Style()
        style.configure(
            "Bending.Treeview",
            font=("Segoe UI", 11),
            rowheight=36,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Bending.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            foreground=LOGO_GREEN,
            padding=(12, 8),
            relief="flat",
        )
        style.layout("Bending.Treeview", [
            ("Bending.Treeview.treearea", {"sticky": "nswe"})
        ])
        style.map("Bending.Treeview", background=[("selected", LOGO_GREEN)])

        # Wrap in a frame with a border to give the table a clean edge
        tree_border = tk.Frame(scrollable, bg=DIVIDER, padx=1, pady=1)
        tree_border.pack(fill="x", pady=(0, 16))

        cols = ("station", "left_clicks", "right_clicks")
        tree = ttk.Treeview(
            tree_border,
            columns=cols,
            show="headings",
            height=len(bending_data) + 1,
            style="Bending.Treeview",
            selectmode="none",
        )

        tree.heading("station", text="Station", anchor="w")
        tree.heading("left_clicks", text="Left Rod — Clicks", anchor="w")
        tree.heading("right_clicks", text="Right Rod — Clicks", anchor="w")

        # Stretch all columns equally
        for col in cols:
            tree.column(col, anchor="w", stretch=True, minwidth=120)

        # Alternating row tags
        tree.tag_configure("odd", background=STRIPE_A)
        tree.tag_configure("even", background=STRIPE_B)
        tree.tag_configure(
            "total",
            background=LIGHT_GREEN,
            font=("Segoe UI", 11, "bold")
        )

        positions = [
            0.00, 10.19, 20.39, 30.58, 40.77, 50.97, 61.16, 71.35,
            81.55, 91.74, 101.94, 112.13, 122.32, 132.52, 142.71, 152.90,
            163.10, 173.29, 183.48, 193.68, 203.87, 214.06, 224.26, 234.45,
            244.65, 254.84, 265.03, 275.23, 285.42, 295.61, 305.81, 316.00
        ]

        for i, (station, left_clicks, right_clicks) in enumerate(bending_data):
            tag = "odd" if i % 2 == 0 else "even"

            position = positions[i] if i < len(positions) else 0.0

            station_text = f"Station {station}: {position:.2f} mm"

            tree.insert(
                "", "end",
                values=(station_text, left_clicks, right_clicks),
                tags=(tag,)
            )

            
        # Totals row
        tree.insert(
            "", "end",
            values=(f"Total  ({num_stations} stations)", total_left, total_right),
            tags=("total",)
        )

        tree.pack(fill="x", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Data
    # ─────────────────────────────────────────────────────────────────────────

    def _get_bending_data(self):
        """
        Return bending data as a list of (station, left_clicks, right_clicks).
        Reads from plan_data if available, otherwise falls back to mock values.
        Once the algorithm is integrated, populate plan_data["rod_bending"]["stations"]
        and this method will pick it up automatically.
        """
        pd = getattr(self.app, "plan_data", {}) or {}
        bending = pd.get("rod_bending", {})
        stations = bending.get("stations", [])

        if isinstance(stations, list) and stations:
            return [
                (i + 1, s.get("left_clicks", 0), s.get("right_clicks", 0))
                for i, s in enumerate(stations)
            ]

        return list(MOCK_BENDING_DATA)