import tkinter as tk
from tkinter import ttk

WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)


class Page12CorrectionStrategies:
    def __init__(self, app):
        self.app = app 

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Correction Strategies",
            back_command=self.app.setup_page_11,
            next_command=self.app.setup_page_13
        )

        # Title only (placeholder)
        tk.Label(
            scrollable,
            text="Correction Strategies",
            font=("Segoe UI", 16, "bold"),
            bg=WHITE,
            fg=LOGO_GREEN
        ).pack(pady=(20, 10), anchor="w")

        ttk.Label(
            scrollable,
            text="Placeholder page (content TBD).",
            font=FONT
        ).pack(pady=(0, 10), anchor="w")
