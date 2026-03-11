import tkinter as tk
from tkinter import ttk

WHITE = "#FFFFFF"
FONT = ("Segoe UI", 12)

from .page14_export import export_docx_top_block
from .page14_save import save_plan_json

class Page14PrintExport:
    def __init__(self, app):
        self.app = app

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Print Pre-Operative Plan / Operative Report",
            back_command=self.app.setup_page_13,
            next_command=None,
        )

        ttk.Label(
            scrollable,
            text="Export as Word Document",
            font=("Segoe UI", 14, "bold"),
            background=WHITE
        ).pack(anchor="w", pady=(6, 10))

        ttk.Label(
            scrollable,
            text="subtitle",
            font=FONT,
            background=WHITE,
            wraplength=560,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        self.app._rounded_button(
            scrollable,
            text="Export Pre-Operative Plan (Word)",
            command=lambda: export_docx_top_block(self.app.plan_data, kind="plan"),
            width=360,
            height=46,
            radius=16
        ).pack(anchor="w", pady=8)

        self.app._rounded_button(
            scrollable,
            text="Export Operative Report (Word)",
            command=lambda: export_docx_top_block(self.app.plan_data, kind="op_note"),
            width=360,
            height=46,
            radius=16
        ).pack(anchor="w", pady=8)

        self.app._rounded_button(
            scrollable,
            text="Team Communication (Email)",
            command=self.app.setup_page_14_team_communication,
            width=360,
            height=46,
            radius=16
        ).pack(anchor="w", pady=(18, 8))

        self.app._rounded_button(
            scrollable,
            text="Save Plan (JSON)",
            command=lambda: save_plan_json(self.app.plan_data),
            width=360,
            height=46,
            radius=16
        ).pack(anchor="w", pady=(18, 8))