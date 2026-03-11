import tkinter as tk
import os
from PIL import Image, ImageTk

class Page01Home:
    def __init__(self, app):
        self.app = app 

    def setup(self):
        app = self.app
        app.clear_window()

        center_frame = tk.Frame(app.root, bg=app.WHITE)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo_path = app._asset_path(os.path.join("assets", app.LOGO_FILE))
        if os.path.exists(logo_path):
            img = Image.open(logo_path)

            target_w = 300
            w, h = img.size
            target_h = int(target_w * (h / w))

            img = img.resize((target_w, target_h), Image.LANCZOS)
            app.logo_image = ImageTk.PhotoImage(img)

            logo_container = tk.Frame(center_frame, bg=app.WHITE, width=target_w, height=target_h)
            logo_container.pack(pady=(0, 20))
            logo_container.pack_propagate(False)

            logo_label = tk.Label(logo_container, image=app.logo_image, bg=app.WHITE)
            logo_label.place(x=-12, y=0)
        else:
            tk.Label(center_frame, text="[Logo Not Found]", font=app.FONT, bg=app.WHITE).pack(pady=(0, 20))

        # Title
        tk.Label(
            center_frame,
            text="FlowControl",
            font=("Segoe UI", 16, "bold"),
            bg=app.WHITE,
            fg=app.LOGO_GREEN
        ).pack(pady=(0, 30))

        # Buttons
        app._rounded_button(
            center_frame,
            text="Create New Plan",
            command=app.create_new_plan
        ).pack(pady=10)

        app._rounded_button(
            center_frame,
            text="Load Previous Plan",
            command=app.load_previous_plan
        ).pack(pady=10)
