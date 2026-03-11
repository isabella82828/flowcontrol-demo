import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import json
import os
import math
import openpyxl 
from collections import defaultdict
from PIL import Image, ImageTk, ImageDraw
from tkcalendar import Calendar


from pages.page01.page01_home import Page01Home
from pages.page10.page10_anchor_selection import Page10AnchorSelection

# Color and font config
WHITE = "#FFFFFF"
LOGO_GREEN = "#036160"
FONT = ("Segoe UI", 12)

LOGO_FILE = "flow_surgical_logo.png"

class MultiSelectDropdown(tk.Frame):
    def __init__(self, parent, options, on_change=None, width_chars=60, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.options = list(options)
        self.on_change = on_change
        self.popup = None

        self.enable_custom_entry = False
        self.custom_option_name = "Custom"
        self.custom_text_var = tk.StringVar(value="")
        self.custom_text_var.trace_add("write", lambda *_: self._sync_display())

        self.display_var = tk.StringVar(value="")

        # entry-like display
        self.entry = tk.Entry(self, textvariable=self.display_var, font=FONT, relief="groove", borderwidth=2)
        self.entry.configure(state="readonly", readonlybackground="white")
        self.entry.pack(side="left", fill="x", expand=True)

        self.btn = tk.Button(self, text="▼", font=FONT, width=2, command=self._toggle_popup)
        self.btn.pack(side="left", padx=(6, 0))

        # checkbox vars
        self._vars = {opt: tk.BooleanVar(value=False) for opt in self.options}
        for v in self._vars.values():
            v.trace_add("write", lambda *_: self._sync_display())

        # allow click anywhere
        self.entry.bind("<Button-1>", lambda e: self._toggle_popup())
        self.bind("<Button-1>", lambda e: self._toggle_popup())

    def _toggle_popup(self):
        if self.popup and self.popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        # Create popup
        self.popup = tk.Toplevel(self)
        self.popup.wm_overrideredirect(True)  # remove title bar
        self.popup.configure(bg="white")

        # Position under this widget
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        self.popup.geometry(f"{max(w, 280)}x260+{x}+{y}")

        container = tk.Frame(self.popup, bg="white")
        container.pack(fill="both", expand=True)

        # Scrollable checkbox area
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="white")
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_config(_):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_inner_config)

        def _on_canvas_config(e):
            canvas.itemconfig(inner_id, width=e.width)
        canvas.bind("<Configure>", _on_canvas_config)

        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Checkboxes
        for opt in self.options:
            ttk.Checkbutton(inner, text=opt, variable=self._vars[opt]).pack(anchor="w", padx=10, pady=4)

            # Inline custom textbox (only if enabled, only for the Custom option)
            if self.enable_custom_entry and opt == self.custom_option_name:
                custom_row = tk.Frame(inner, bg="white")
                custom_row.pack(fill="x", padx=32, pady=(0, 6))

                tk.Label(custom_row, text="Custom:", bg="white", font=("Segoe UI", 10)).pack(side="left")
                custom_entry = tk.Entry(custom_row, textvariable=self.custom_text_var, font=("Segoe UI", 10))
                custom_entry.pack(side="left", fill="x", expand=True, padx=(6, 10))

                def _toggle_custom_state(*_):
                    on = bool(self._vars[self.custom_option_name].get())
                    custom_entry.configure(state=("normal" if on else "disabled"))
                _toggle_custom_state()
                self._vars[self.custom_option_name].trace_add("write", lambda *_: _toggle_custom_state())

        # Actions
        btn_row = tk.Frame(self.popup, bg="white")
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Clear", font=FONT, command=self.clear).pack(side="left", padx=8, pady=8)
        tk.Button(btn_row, text="Done", font=FONT, command=self._close_popup).pack(side="right", padx=8, pady=8)

        # Close on focus out
        self.popup.bind("<FocusOut>", lambda e: self._close_popup())
        self.popup.focus_force()

    def _close_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None

    def _sync_display(self):
        selected = self.get_selected()
        display_items = []

        for opt in selected:
            if self.enable_custom_entry and opt == self.custom_option_name:
                custom_txt = self.custom_text_var.get().strip()
                if custom_txt:
                    display_items.append(custom_txt)
            else:
                display_items.append(opt)

        self.display_var.set(", ".join(display_items))

        if callable(self.on_change):
            self.on_change(selected)

    def get_selected(self):
        return [opt for opt, v in self._vars.items() if bool(v.get())]

    def get_custom_text(self):
        return (self.custom_text_var.get() or "").strip()

    def set_selected(self, selected_list):
        s = set([x.strip() for x in (selected_list or []) if x is not None])
        for opt, v in self._vars.items():
            v.set(opt in s)
        self._sync_display()

    def clear(self):
        for v in self._vars.values():
            v.set(False)
        self._sync_display()

class FlowbiWanApp:
    def __init__(self, root):
        self.root = root
        
        self.WHITE = WHITE
        self.LOGO_GREEN = LOGO_GREEN
        self.FONT = FONT
        self.LOGO_FILE = LOGO_FILE

        style = ttk.Style()
        style.theme_use("clam")  

        style.configure(".", background=WHITE)
        style.configure("TFrame", background=WHITE)
        style.configure("TLabel", background=WHITE)

        # Headings / subheadings
        style.configure("Header.TLabel", background=WHITE, foreground="black", font=("Segoe UI", 12, "bold"))
        style.configure("Subheader.TLabel", background=WHITE, foreground=LOGO_GREEN, font=("Segoe UI", 11, "bold"))

        style.configure("TLabelframe", background=WHITE)
        style.configure("TLabelframe.Label", background=WHITE, foreground="black", font=("Segoe UI", 12, "bold"))

        # Notebook area and tabs
        style.configure("TNotebook", background=WHITE, borderwidth=0)
        style.configure("TNotebook.Tab", background=WHITE)
        style.map("TNotebook.Tab",
        background=[("selected", WHITE), ("active", "#F5F5F5")])

        style.configure(
            "Green.TButton",
            font=FONT,
            foreground="white",
            background=LOGO_GREEN,
            padding=(14, 10)
        )
        style.map(
            "Green.TButton",
            background=[("active", LOGO_GREEN), ("disabled", "#A9B7B6")],
            foreground=[("disabled", "#F2F2F2")]
        )
        style.configure(
            "Light.TButton",
            font=FONT,
            padding=(12, 8)
        )

        style.configure(
            "White.TButton",
            font=FONT,
            foreground="black",
            background=WHITE,
            padding=(16, 10),
            borderwidth=1,
            relief="solid"
        )

        style.map(
            "White.TButton",
            background=[("active", "#F5F5F5"), ("pressed", "#ECECEC")],
        )

        self.root.title("FlowControl™: Surgical Planner")
        self.root.configure(bg=WHITE)
        self.root.geometry("600x650")
        self.is_dirty = False

        self.inventory_totals = {}
        self.inventory_rows = {}
        self.inventory_file_path = None

        self.logo_image = None
        self.logo_large = None   # for page 1
        self.logo_small = None   # for header

        self.plan_data = {
            "logic_results": {},
            "radiographic_parameters": {},
            "logic_source": "Lebel"  # default
        }

        self.page10 = Page10AnchorSelection(self)

        self.setup_page_1()
        self._force_redraw()
        self._mt_left_warning_shown = False  


    def _hex_to_rgba(self, hex_color, alpha=255):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)

    def _make_rounded_btn_img(
        self,
        w,
        h,
        radius,
        fill_hex,
        shadow=True,
        shadow_offset=(0, 3),
        shadow_alpha=60,
        shadow_blur_layers=3,
    ):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if shadow:
            ox, oy = shadow_offset
            for i in range(shadow_blur_layers, 0, -1):
                pad = i
                a = int(shadow_alpha * (i / shadow_blur_layers))
                shadow_col = (0, 0, 0, a)
                draw.rounded_rectangle(
                    [0 + ox - pad, 0 + oy - pad, w - 1 + ox + pad, h - 1 + oy + pad],
                    radius=radius + pad,
                    fill=shadow_col,
                )

        # main button
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=fill_hex)
        return ImageTk.PhotoImage(img)

    def _resolve_level_token(self, token: str) -> str:
        data = self.plan_data.get("radiographic_parameters", {})
        stand = data.get("standing_coronal", {})
        add_sup = data.get("additional_supine_coronal", {})
        add_stand = data.get("additional_standing_coronal", {})
        

        lstv_val = (stand.get("last_substantially_touched_vertebra") or "").strip()
        sltv_val = (add_sup.get("sltv") or add_stand.get("sltv") or "").strip()
        mtlv_val = (stand.get("mt_last_touched_vertebra") or "").strip()  # if you ever use MT-LTV

        if token == "LSTV":
            return lstv_val or "—"
        if token == "SLTV":
            return sltv_val or "—"
        if token == "MT-LTV":
            return mtlv_val or "—"
        return token


    def _rounded_button(
        self,
        parent,
        text,
        command,
        width=320,
        height=50,
        radius=18,
        fill=LOGO_GREEN,
        fill_hover="#047070",
        fill_pressed="#035656",
    ):
        normal_img = self._make_rounded_btn_img(width, height, radius, fill, shadow=False)
        hover_img  = self._make_rounded_btn_img(width, height, radius, fill_hover, shadow=False)
        press_img  = self._make_rounded_btn_img(width, height, radius, fill_pressed, shadow=False)

        btn = tk.Label(
            parent,
            image=normal_img,
            text=text,
            compound="center",
            fg="white",
            bg=WHITE,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
        )

        btn.image_normal = normal_img
        btn.image_hover = hover_img
        btn.image_press = press_img

        def _set_pady(pady_val):
            mgr = btn.winfo_manager()
            if mgr == "pack":
                btn.pack_configure(pady=pady_val)
            elif mgr == "grid":
                btn.grid_configure(pady=pady_val)

        def on_enter(_):
            btn.configure(image=btn.image_hover)
            btn._pressed = False

        def on_leave(_):
            btn.configure(image=btn.image_normal)
            btn._pressed = False
        _set_pady(10)

        def on_press(_):
            btn._pressed = True
            btn.configure(image=btn.image_press)
            _set_pady((11, 9))

        def on_release(_):
            if getattr(btn, "_pressed", False):
                btn._pressed = False
                btn.configure(image=btn.image_hover)
                _set_pady(10)
                command()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<ButtonPress-1>", on_press)
        btn.bind("<ButtonRelease-1>", on_release)

        return btn

    def setup_page_10(self):
        self.page10.setup()
                
    def setup_page_11(self):
        self.clear_window()
        from pages.page11.page11_rod_selection import Page11RodSelection
        Page11RodSelection(self).setup()

    def setup_page_12(self):
        self.clear_window()
        from pages.page12.page12_correction_strategies import Page12CorrectionStrategies
        Page12CorrectionStrategies(self).setup()

    def setup_page_13(self):
        self.clear_window()
        from pages.page13.page13_post_op_destination import Page13PostOpDestination
        Page13PostOpDestination(self).setup()

    def setup_page_14(self):
        self.clear_window()
        from pages.page14.page14_print_export import Page14PrintExport
        Page14PrintExport(self).setup()
    
    def setup_page_14_team_communication(self):
        self.clear_window()
        from pages.page14.page14_team_communication import Page14TeamCommunication
        Page14TeamCommunication(self).setup()


    def _asset_path(self, rel_path: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, rel_path)
    
    def _load_logo(self, size):
        path = self._asset_path(os.path.join("assets", LOGO_FILE))
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            img = img.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def bind_mousewheel(self, canvas):
        def _on_mousewheel(event):
            cls = event.widget.winfo_class()
            if cls in ("TCombobox", "Combobox"):
                return

            if event.delta:
                canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel, add="+")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def _force_redraw(self):
        self.root.update_idletasks()
        self.root.after(10, self.root.update_idletasks)

    def create_scrollable_tab(self, parent):
        canvas = tk.Canvas(parent, bg=WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=WHITE)

        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # Update scrollregion when contents change
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Force scroll_frame to always match canvas width
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
        )

        canvas.configure(yscrollcommand=scrollbar.set)
        self.bind_mousewheel(canvas)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scroll_frame

    def create_standard_page(self, title_text="FlowControl", back_command=None, next_command=None):
        self.clear_window()

        # --- HEADER ---
        header_frame = tk.Frame(self.root, bg=WHITE)
        header_frame.pack(fill="x", pady=10, padx=10)

        # 3 columns: logo | title (expands) | exit
        header_frame.columnconfigure(0, weight=0)
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=0)

        # Logo (left)
        if self.logo_small is None:
            self.logo_small = self._load_logo((140, 70))

        if self.logo_small is not None:
            logo_label = tk.Label(header_frame, image=self.logo_small, bg=WHITE)
            logo_label.image = self.logo_small
            logo_label.grid(row=0, column=0, padx=(5, 10), pady=5, sticky="w")
        else:
            tk.Label(header_frame, text="[Logo]", font=FONT, bg=WHITE)\
                .grid(row=0, column=0, padx=(5, 10), pady=5, sticky="w")

        # Title 
        tk.Label(
            header_frame,
            text=title_text,
            font=("Segoe UI", 14, "bold"),
            bg=WHITE,
            fg=LOGO_GREEN
        ).grid(row=0, column=1)

        # Exit button 
        exit_btn = self._rounded_button(
            header_frame,
            text="Exit",
            command=self.exit_to_page_1,
            width=120,
            height=44,
            radius=16
            )
        exit_btn.grid(row=0, column=2, padx=(10, 20), pady=5, sticky="e")

        # --- SCROLLABLE CONTENT ---
        content_frame = tk.Frame(self.root, bg=WHITE)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollable_frame = self.create_scrollable_tab(content_frame)

        # --- FOOTER ---
        footer_frame = tk.Frame(self.root, bg=WHITE)
        footer_frame.pack(fill="x", side="bottom", pady=10, padx=10)

        if back_command:
            back_btn = self._rounded_button(
                footer_frame,
                text="Back",
                command=back_command,
                width=140,
                height=46,
                radius=16
            )
            back_btn.pack(side="left", padx=6)

        if next_command:
            next_btn = self._rounded_button(
                footer_frame,
                text="Next",
                command=next_command,
                width=140,
                height=46,
                radius=16
            )
            next_btn.pack(side="right", padx=6)

        return scrollable_frame

    def upload_ct_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.plan_data["ct_dicom_folder"] = folder
            self.ct_label.config(text=f"Selected: {os.path.basename(folder)}")
            self.clear_ct_button.pack()
            self.is_dirty = True

    def clear_ct_folder(self):
        self.plan_data.pop("ct_dicom_folder", None)
        self.ct_label.config(text="")
        self.clear_ct_button.pack_forget()
        self.is_dirty = True

    def upload_rad_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.plan_data["radiograph_dicom_folder"] = folder
            self.rad_label.config(text=f"Selected: {os.path.basename(folder)}")
            self.clear_rad_button.pack()
            self.is_dirty = True

    def clear_rad_folder(self):
        self.plan_data.pop("radiograph_dicom_folder", None)
        self.rad_label.config(text="")
        self.clear_rad_button.pack_forget()
        self.is_dirty = True

    def _add_row_label(self, parent, text):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=5)
        label = tk.Label(row, text=text, font=FONT, bg=WHITE)
        label.pack(side="left", padx=(0, 10))
        return row

    def _add_entry(self, parent):
        entry = tk.Entry(parent, font=FONT)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _add_combo(self, parent, options, default=None):
        var = tk.StringVar(value=default or options[0])
        combo = ttk.Combobox(parent, values=options, textvariable=var, state="readonly", font=FONT)
        combo.pack(side="right", fill="x", expand=True)
        return var, combo

    def _add_help_btn(self, parent, title, message):
        def show_help():
            messagebox.showinfo(title, message)
        help_btn = ttk.Button(parent, text="?", command=show_help, font=FONT)
        help_btn.pack(side="right", padx=5)

    def _set_plan_value(self, section, key, value):
        if "radiographic_parameters" not in self.plan_data:
            self.plan_data["radiographic_parameters"] = {}
        if section not in self.plan_data["radiographic_parameters"]:
            self.plan_data["radiographic_parameters"][section] = {}
        self.plan_data["radiographic_parameters"][section][key] = value
        self.is_dirty = True

    def _coerce_float(self, val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def setup_page_1(self):
        self.clear_window()
        Page01Home(self).setup()

    def create_new_plan(self):
        self.plan_data = {
            "patient": {},
            "logic_results": {},
            "radiographic_parameters": {},
            "logic_source": "Lebel"
        }
        self._ensure_contacts_block()
        self.setup_page_2()
        self._force_redraw()

    def load_previous_plan(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.plan_data = json.load(f)
                    if not self.plan_data.get("logic_source"):
                        self.plan_data["logic_source"] = "Lebel"

                self._ensure_contacts_block()
                self.setup_page_2()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load plan: {e}")

    def exit_to_page_1(self):
        self.prompt_save_and_exit()

    def prompt_save_and_exit(self):
        if self.is_dirty or self.plan_data:
            result = messagebox.askyesnocancel("Save Plan", "Would you like to save this plan before exiting?")
            if result:
                filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
                if filepath:
                    try:
                        with open(filepath, 'w') as f:
                            json.dump(self.plan_data, f, indent=2)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save plan: {e}")
                        return
                self.setup_page_1()
            elif result is False:
                self.setup_page_1()
        else:
            if messagebox.askyesno("Exit", "No changes detected. Exit anyway?"):
                self.setup_page_1()

    def setup_page_2(self):
        self.is_dirty = False 

        scrollable = self.create_standard_page(
        title_text="FlowControl",
        back_command=self.setup_page_1,
        next_command=lambda: self.validate_and_continue()
        )
        
        tk.Label(scrollable, text="Patient ID:", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.patient_id_entry = tk.Entry(scrollable, font=FONT, relief="groove", borderwidth=2)
        self.patient_id_entry.pack(fill="x")
        self.patient_id_entry.bind("<KeyRelease>", lambda e: setattr(self, "is_dirty", True))
        
        # Surgery Date
        tk.Label(scrollable, text="Surgery Date (YYYY-MM-DD):", bg=WHITE, font=FONT)\
            .pack(pady=(10, 0), anchor="w")

        date_row = tk.Frame(scrollable, bg=WHITE)
        date_row.pack(fill="x")

        self.surgery_date_entry = tk.Entry(date_row, font=FONT, relief="groove", borderwidth=2)
        self.surgery_date_entry.pack(side="left", fill="x", expand=True)

        existing = self.plan_data.get("patient", {})
        existing_date = (existing.get("surgery_date") or "").strip()
        if existing_date:
            self.surgery_date_entry.delete(0, "end")
            self.surgery_date_entry.insert(0, existing_date)

        def _open_date_picker():
            top = tk.Toplevel(self.root)
            top.title("Select Surgery Date")
            top.configure(bg=WHITE)
            top.transient(self.root)
            top.grab_set()
            top.attributes("-topmost", True)

            cal = Calendar(
                top,
                selectmode="day",
                date_pattern="yyyy-mm-dd",
                font=("Segoe UI", 10)
            )
            cal.pack(padx=10, pady=10)

            if self.surgery_date_entry.get().strip():
                try:
                    cal.selection_set(self.surgery_date_entry.get().strip())
                except Exception:
                    pass

            def _use_selected():
                chosen = cal.get_date() 
                self.surgery_date_entry.delete(0, "end")
                self.surgery_date_entry.insert(0, chosen)
                self.is_dirty = True
                top.destroy()

            btn_row = tk.Frame(top, bg=WHITE)
            btn_row.pack(fill="x", padx=10, pady=(0, 10))

            ttk.Button(btn_row, text="Cancel", command=top.destroy).pack(side="left")
            ttk.Button(btn_row, text="Use date", command=_use_selected).pack(side="right")

            # allow double click on a date to accept quickly
            cal.bind("<<CalendarSelected>>", lambda e: _use_selected())

        ttk.Button(date_row, text="📅", width=3, command=_open_date_picker).pack(side="left", padx=(6, 0))

        self.surgery_date_entry.bind("<KeyRelease>", lambda e: setattr(self, "is_dirty", True))


        # Age
        tk.Label(scrollable, text="Patient Age (years):", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.age_var = tk.StringVar(value="12")
        self.age_combobox = ttk.Combobox(scrollable, textvariable=self.age_var, values=[str(i) for i in range(1, 19)], font=FONT, state="readonly")
        self.age_combobox.pack(fill="x")
        self.age_combobox.bind("<<ComboboxSelected>>", lambda e: setattr(self, "is_dirty", True))

        # Sex
        tk.Label(scrollable, text="Sex:", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.sex_var = tk.StringVar(value="F")  
        self.sex_combobox = ttk.Combobox(
            scrollable,
            textvariable=self.sex_var,
            values=["F", "M", "Other", "Unknown"],
            font=FONT,
            state="readonly"
        )
        self.sex_combobox.pack(fill="x")
        self.sex_combobox.bind("<<ComboboxSelected>>", lambda e: setattr(self, "is_dirty", True))
        
        # Aim (procedure goal)
        tk.Label(scrollable, text="Aim (Goal of Procedure):", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")

        aim_options = [
            "Prevent curve progression",   # default selection
            "Improve shoulder balance",
            "Decrease thoracic prominence",
            "Improve trunk shift",
            "Decrease lumbar prominence",
            "Custom",
        ]

        self.aim_multi = MultiSelectDropdown(
            scrollable,
            options=aim_options,
            on_change=lambda _sel: setattr(self, "is_dirty", True),
        )

        self.aim_multi.enable_custom_entry = True  
        self.aim_multi.pack(fill="x")
        
        if existing.get("aim_custom_text"):
            self.aim_multi.custom_text_var.set(existing["aim_custom_text"])

        # --- default selection  ---
        existing = self.plan_data.get("patient", {})
        saved_aim = existing.get("aim", [])  # expect list like ["..."]
        if not saved_aim:
            try:
                self.aim_multi.set_selected(["Prevent curve progression"])
            except Exception:
                pass

        # Weight
        tk.Label(scrollable, text="Weight:", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.weight_entry = tk.Entry(scrollable, font=FONT, relief="groove", borderwidth=2)
        self.weight_entry.pack(fill="x")
        self.weight_entry.bind("<KeyRelease>", lambda e: setattr(self, "is_dirty", True))

        # Weight Unit
        self.weight_unit = tk.StringVar(value="kg")
        self.weight_unit_combobox = ttk.Combobox(scrollable, textvariable=self.weight_unit, values=["kg", "lbs"],font=FONT, state="readonly")
        self.weight_unit_combobox.pack(fill="x", pady=(0, 10))
        self.weight_unit_combobox.bind("<<ComboboxSelected>>", lambda e: setattr(self, "is_dirty", True))

        # Scoliosis Etiology
        tk.Label(scrollable, text="Scoliosis Etiology:", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.etiology_var = tk.StringVar(value="AIS")
        self.etiology_menu = ttk.Combobox(scrollable, textvariable=self.etiology_var,
                                        values=["AIS", "Congenital", "Syndromic", "Neuromuscular"],
                                        font=FONT, state="readonly")
        self.etiology_menu.pack(fill="x")
        self.etiology_menu.bind("<<ComboboxSelected>>", self.check_etiology_warning)
        self.etiology_menu.bind("<<ComboboxSelected>>", lambda e: setattr(self, "is_dirty", True), add="+")

        # Logic Selector
        tk.Label(scrollable, text="ScoliMaster (i.e. Decision Logic):", bg=WHITE, font=FONT).pack(pady=(10, 0), anchor="w")
        self.logic_var = tk.StringVar(value=(self.plan_data.get("logic_source") or "Lebel"))
        self.logic_menu = ttk.Combobox(scrollable, textvariable=self.logic_var,
                                    values=["Lebel", "Torode", "Baldwin"],
                                    font=FONT, state="readonly")
        self.logic_menu.pack(fill="x")
        self.logic_menu.bind("<<ComboboxSelected>>", self.check_logic_warning)
        self.logic_menu.bind("<<ComboboxSelected>>", lambda e: setattr(self, "is_dirty", True), add="+")

        existing = self.plan_data.get("patient", {})
        if existing.get("sex"):
            self.sex_var.set(existing["sex"])
        if existing.get("aim"):
            # support older saves where aim was a string
            if isinstance(existing["aim"], list):
                self.aim_multi.set_selected(existing["aim"])
            else:
                self.aim_multi.set_selected([x.strip() for x in str(existing["aim"]).split(",") if x.strip()])

        # Patient ID
        if existing.get("id"):
            self.patient_id_entry.delete(0, "end")
            self.patient_id_entry.insert(0, str(existing["id"]))

        # Age
        if existing.get("age_years") is not None:
            self.age_var.set(str(existing["age_years"]))

        # Weight (assume stored as kg)
        if existing.get("weight_kg") is not None:
            self.weight_entry.delete(0, "end")
            self.weight_entry.insert(0, str(existing["weight_kg"]))
            self.weight_unit.set("kg")

        # Etiology
        if existing.get("etiology_raw"):
            self.etiology_var.set(existing["etiology_raw"])

        # Logic source
        if self.plan_data.get("logic_source"):
            self.logic_var.set(self.plan_data["logic_source"])

    def check_etiology_warning(self, event=None):
        if self.etiology_var.get() in ["Congenital", "Syndromic"]:
            messagebox.showinfo("Notice", f"{self.etiology_var.get()} module is still in development.")

    def check_logic_warning(self, event=None):
        if self.logic_var.get() in ["Torode", "Baldwin"]:
            messagebox.showinfo("Notice", f"{self.logic_var.get()} logic is still in development.")

    def validate_page_2(self):
        pid = self.patient_id_entry.get().strip()
        date = self.surgery_date_entry.get()

        if not pid or not date:
            messagebox.showwarning("Missing Info", "Patient ID and Surgery Date are required.")
            return False

        # weight -> kg
        weight_txt = self.weight_entry.get().strip()
        if weight_txt:
            try:
                weight_val = float(weight_txt)
                if self.weight_unit.get() == "lbs":
                    weight_val *= 0.45359237  # Exact kg per lb
                weight_val = round(weight_val, 2)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for weight.")
                return False
        else:
            weight_val = None

        # Diagnosis mapping 
        etiology = (self.etiology_var.get() or "").strip()
        diagnosis = "NMS" if etiology.lower() in ("neuromuscular",) else etiology  

        # Ensure nested patient dict
        patient = self.plan_data.setdefault("patient", {})

        aim_list = self.aim_multi.get_selected()
        aim_custom = self.aim_multi.get_custom_text()

        aim_text_items = []
        for opt in aim_list:
            if opt == "Custom":
                if aim_custom:
                    aim_text_items.append(aim_custom)
            else:
                aim_text_items.append(opt)

        patient.update({
            "id": pid,
            "surgery_date": date,
            "age_years": int(self.age_var.get()) if str(self.age_var.get()).isdigit() else self.age_var.get(),
            "weight_kg": weight_val,             
            "diagnosis": diagnosis,               
            "etiology_raw": etiology,   
            "sex": (self.sex_var.get() or "").strip(),
            "aim": aim_list,
            "aim_custom_text": aim_custom,
            "aim_text": ", ".join(aim_text_items),
        })

        self.plan_data["logic_source"] = self.logic_var.get()

        self.is_dirty = True
        return True

    def validate_and_continue(self):
        if self.validate_page_2():
            self.setup_page_3()

    def setup_page_3(self):
        self.is_dirty = False  # Reset dirty flag

        scrollable = self.create_standard_page(
            title_text="FlowControl™",
            back_command=self.setup_page_2,
            next_command=self.setup_page_4
        )

        # Title
        tk.Label(scrollable, text="Upload Pre-Operative Imaging", font=("Segoe UI", 14, "bold"), bg=WHITE).pack(pady=(10, 5))

        # Instructions
        instructions = (
            "Upload your pre-operative DICOM folders (CT and radiographs).\n"
            "FlowControl™ will soon support automated in-image measurements.\n"
        )
        tk.Label(scrollable, text=instructions, font=FONT, bg=WHITE, justify="left", anchor="w", wraplength=550).pack(pady=10, anchor="w")

        # --- CT Upload Section ---
        ttk.Button(
            scrollable,
            text="Upload CT DICOM Folder",
            style="White.TButton",
            command=self.upload_ct_folder
        ).pack(pady=(15, 0), anchor="w")

        self.ct_label = tk.Label(scrollable, text="", font=("Segoe UI", 10), bg=WHITE, fg="gray", anchor="w")
        self.ct_label.pack(fill="x", padx=5)

        self.clear_ct_button = ttk.Button(
            scrollable,
            text="Clear CT Folder",
            style="Light.TButton",
            command=self.clear_ct_folder
        )
        self.clear_ct_button.pack(anchor="w", padx=5)
        self.clear_ct_button.pack_forget()

        # --- Radiograph Upload Section ---
        ttk.Button(
            scrollable,
            text="Upload Radiograph DICOM Folder",
            style="White.TButton",
            command=self.upload_rad_folder
        ).pack(pady=(15, 0), anchor="w")

        self.rad_label = tk.Label(scrollable, text="", font=("Segoe UI", 10), bg=WHITE, fg="gray", anchor="w")
        self.rad_label.pack(fill="x", padx=5)

        self.clear_rad_button = ttk.Button(
            scrollable,
            text="Clear Radiograph Folder",
            style="Light.TButton",
            command=self.clear_rad_folder
        )
        self.clear_rad_button.pack(anchor="w", padx=5)
        self.clear_rad_button.pack_forget()

    def setup_page_4(self):
        # from pages.page04.page04_radiographic import Page04Radiographic
        # Page04Radiographic(self).setup()
        from pages.page04.page04_radiographic_adaptive import Page04RadiographicAdaptive
        Page04RadiographicAdaptive(self).setup()

    def validate_page4_and_mark(self):
        missing_fields_by_tab = {}
        ok = True

        def check_fields(tab_key, tab_label, required_fields):
            nonlocal ok
            data = self.plan_data.get("radiographic_parameters", {}).get(tab_key, {})
            missing = [label for key, label in required_fields if data.get(key) in [None, ""]]
            if missing:
                missing_fields_by_tab[tab_label] = missing
                self._mark_tab_red(tab_label)
                ok = False
            else:
                self._clear_tab_mark(tab_label)

        # --- Standing Coronal ---
        check_fields("standing_coronal", "Standing Coronal", [
            ("pt_cobb", "Proximal Thoracic Cobb Angle"),
            ("mt_cobb", "Main Thoracic Cobb Angle"),
            ("tl_l_cobb", "Thoracolumbar/Lumbar Cobb Angle")
        ])

        # --- Standing Sagittal ---
        check_fields("standing_sagittal", "Standing Sagittal", [
            ("t2_5_kyphosis", "T2–T5 Kyphosis"),
            ("t5_12_kyphosis", "T5–T12 Kyphosis"),
            ("t10_l2_kyphosis", "T10–L2 Kyphosis"),
        ])

        # --- Additional Supine Coronal ---
        check_fields("additional_supine_coronal", "Additional Supine Coronal", [
            ("sltv", "Supine Last Touched Vertebra")
        ])

        # --- Additional Standing Coronal ---
        check_fields("additional_standing_coronal", "Additional Standing Coronal", [
            ("l4_tilt_direction", "L4 Tilt Direction")
        ])

        # --- Additional Bending ---
        check_fields("additional_bending", "Additional Bending", [
            ("bending_l3_4_disc_angle", "Bending L3–4 Disc Angle")
        ])

        # --- Additional Standing Sagittal ---
        check_fields("additional_standing_sagittal", "Additional Standing Sagittal", [
            ("lordotic_disc_below_mt_ltv", "Lordotic Disc Below MT LTV"),
            ("scsl", "Sagittal Central Sacral Line")
        ])

        return ok, missing_fields_by_tab

    # --- Marking functions ---
    def _mark_tab_red(self, tab_label):
        for i in range(len(self.page4_tabs)):
            if self.page4_notebook.tab(i, "text") == tab_label:
                self.page4_notebook.tab(i, text=f"🔴 {tab_label}")

    def _clear_tab_mark(self, tab_label):
        for i in range(len(self.page4_tabs)):
            if self.page4_notebook.tab(i, "text") == f"🔴 {tab_label}":
                self.page4_notebook.tab(i, text=tab_label)

    def page4_next_logic(self):
        ok, missing = self.validate_page4_and_mark()
        if not ok:
            lines = []
            for tab, fields in missing.items():
                lines.append(f"{tab}:\n  - " + "\n  - ".join(fields))
            proceed = messagebox.askyesno(
                "Incomplete Radiographic Data",
                "Some high impact fields are missing (tabs marked 🔴):\n\n" +
                "\n\n".join(lines) +
                "\n\nYou can still continue, but accurately entering the requested data allows level selection recommendations.\nContinue?"
            )
            if not proceed:
                return

        self.setup_page_5()

    # Page 5 
    def setup_page_5(self):
        scrollable = self.create_standard_page(
            title_text="Level Recommendations",
            back_command=self.setup_page_4,
            next_command=self.page5_next
        )

        print("[DEBUG] logic_source=", self.plan_data.get("logic_source"), "logic=", self.plan_data.get("logic_source"))

        row = self._add_row_label(scrollable, "Selected Logic Source:")
        self.logic_display_var = tk.StringVar(value=(self.plan_data.get("logic_source") or "Lebel"))
        ttk.Label(row, textvariable=self.logic_display_var, font=FONT).pack(side="left", padx=10)

        # --- Output fields ---
        self.result_labels = {}
        for label in ["Lenke Type", "Lumbar Modifier", "Sagittal Modifier", "UIV", "LIV"]:
            r = self._add_row_label(scrollable, f"{label}:")
            var = tk.StringVar(value="—")
            ttk.Label(r, textvariable=var, font=FONT).pack(side="left", padx=10)
            self.result_labels[label.lower().replace(" ", "_")] = var

        # --- Rationale/Evaluation text boxes ---
        for section, height in [("UIV Rationale", 3), ("LIV Rationale", 3),
                                ("STF Evaluation", 7), ("SLF Evaluation", 5)]:
            tk.Label(scrollable, text=section + ":", font=FONT, bg=WHITE).pack(pady=(15, 2))
            txt = tk.Text(scrollable, height=height, font=("Segoe UI", 10), wrap="word")
            txt.config(state="disabled")
            txt.pack(fill="x", padx=10)
            self.result_labels[section.lower().replace(" ", "_")] = txt

        self.run_level_logic()

    def run_level_logic(self):
        logic = None
        if hasattr(self, "logic_var") and self.logic_var is not None:
            logic = self.logic_var.get()

        logic = (logic or self.plan_data.get("logic_source") or "Lebel")

        self.plan_data["logic_source"] = logic

        results = self.calculate_lenke_and_levels(logic=logic)

        self.result_labels["lenke_type"].set(results.get("lenke_type", "—"))
        self.result_labels["lumbar_modifier"].set(results.get("lumbar_modifier", "—"))
        self.result_labels["sagittal_modifier"].set(results.get("sagittal_modifier", "—"))
        self.result_labels["uiv"].set(results.get("uiv", "—"))
        self.result_labels["liv"].set(results.get("liv", "—"))

        def update_text(key, content):
            box = self.result_labels[key]
            box.config(state="normal")
            box.delete("1.0", tk.END)
            if isinstance(content, list):
                box.insert("1.0", "\n".join(content))
            else:
                box.insert("1.0", content or "")
            box.config(state="disabled")

        update_text("uiv_rationale", results.get("uiv_rationale", ""))
        update_text("liv_rationale", results.get("liv_rationale", ""))
        update_text("stf_evaluation", results.get("stf_reasons", []))
        update_text("slf_evaluation", results.get("slf_reason", ""))

        # Save result block for export
        self.plan_data["level_selection"] = results

    # --- Save Plan from Page 5 ---
    def save_and_exit_plan(self):
        if "level_selection" not in self.plan_data:
            messagebox.showwarning("Missing Results", "Please run the logic to generate level selection.")
            return
        self.exit_to_page_1()

    def page5_next(self):
        level_sel = self.plan_data.get("level_selection", {}) or {}
        lenke = (level_sel.get("lenke_type") or "").strip()

        if lenke == "Lenke 1" or lenke.startswith("Lenke 1"):
            self.setup_page5_5()
        else:
            self.setup_page_6()

    def setup_page5_5(self):
        self.clear_window()
        from pages.page5_5.page5_5 import Page5_5
        Page5_5(self).setup()

    # --- Logic Dispatcher ---
    def calculate_lenke_and_levels(self, logic=None):
        if logic is None:
            # Fallbacks for safety
            if hasattr(self, "logic_var") and self.logic_var is not None:
                logic = self.logic_var.get()
            if not logic:
                logic = (self.plan_data.get("logic_source") or "Lebel")

        if logic == "Lebel":
            return self._calculate_lenke_lebel()

        # Placeholders for Torode/Baldwin logic (coming soon!)
        return {
            "lenke_type": "Unclassified",
            "lumbar_modifier": "-",
            "sagittal_modifier": "-",
            "uiv": "T2",
            "liv": "L3",
            "uiv_rationale": f"Default logic placeholder ({logic})",
            "liv_rationale": f"Default logic placeholder ({logic})",
            "stf_eligible": "No",
            "stf_reasons": [f"Logic not yet implemented for: {logic}"],
            "slf_eligible": "No" ,
            "slf_reason": f"Logic not yet implemented for: {logic}",
        }

    def _get_float(self, x, default=0):
        try:
            if x is None or x == "":
                return default
            return float(x)
        except Exception:
            return default
    
    def _shift_dir(self, mm: float) -> str:
        try:
            mm = float(mm)
        except Exception:
            return "Neutral"
        if mm > 0:
            return "Right"
        if mm < 0:
            return "Left"
        return "Neutral"

    def _calculate_lenke_lebel(self):
        # Buckets
        data = self.plan_data.get("radiographic_parameters", {})
        stand = data.get("standing_coronal", {})
        sag = data.get("standing_sagittal", {})

        # Standing coronal 
        pt_cobb = self._get_float(stand.get("pt_cobb"), 0)
        mt_cobb = self._get_float(stand.get("mt_cobb"), 0)
        tl_l_cobb = self._get_float(stand.get("tl_l_cobb"), 0)

        stand = data.get("standing_coronal", {})
        additional_stand = data.get("additional_standing_coronal", {})
        bend = data.get("bending", {})
        additional_bend = data.get("additional_bending", {})

        lstv = (
            (stand.get("last_substantially_touched_vertebra") or "").strip()
            or (additional_bend.get("lstv") or "").strip()
            or (bend.get("lstv") or "").strip()
            or (additional_stand.get("lstv") or "").strip()
        )

        additional_supine = data.get("additional_supine_coronal", {})
        additional_sag = data.get("additional_standing_sagittal", {})
        
        csvl_pos = stand.get("csvl_tll_apex_position", "")     
        risser_str = stand.get("risser_score", "0")          

        try:
            risser = int(risser_str)
        except Exception:
            risser = 0

        # Bending
        pt_bend  = self._get_float(bend.get("pt_cobb"), 0)
        mt_bend  = self._get_float(bend.get("mt_cobb"), 0)
        tll_bend = self._get_float(bend.get("tl_l_cobb"), 0)

        # Standing sagittal
        pt_kyph = self._get_float(sag.get("t2_5_kyphosis"), 0)
        t5_12_kyph = self._get_float(sag.get("t5_12_kyphosis"), 0)
        t10_l2_kyph = self._get_float(sag.get("t10_l2_kyphosis"), 0)
        pt_apex = sag.get("pt_apex_level", "")

        # Additional — Standing Coronal
        mt_apical_translation  = self._get_float(stand.get("mt_apical_translation_mm"), 0)
        tll_apical_translation = self._get_float(stand.get("tll_apical_translation_mm"), 0)

        mt_nash_moe  = self._get_float(stand.get("mt_nashmoe_grade"), 0)
        tll_nash_moe = self._get_float(stand.get("tll_nashmoe_grade"), 0)

        l4_tilt_direction = additional_stand.get("l4_tilt_direction", "")

        print(
            "[DEBUG] SLTV:", additional_supine.get("sltv"),
            "| LSTV:", lstv,
            "| MT-LTV:", additional_stand.get("mt_ltv")
        )
        sltv = additional_supine.get("sltv", "") or additional_stand.get("sltv", "")
        mt_ltv = additional_stand.get("mt_ltv", "")
        
        gravity_stability_score = str(additional_stand.get("gravity_stability_score", "0"))
        rotational_stability_score = str(additional_stand.get("rotational_stability_score", "0"))
        
        upright_l3_4_disc_angle  = self._get_float(sag.get("l3_4_disc_angle_upright"), 0)
        bending_l3_4_disc_angle  = self._get_float(bend.get("l3_4_disc_angle"), 0)

        l3_deviation_csvl = self._get_float(stand.get("l3_deviation_csvl_mm"), 0)
        l3_rotation_grade = str(additional_stand.get("l3_rotation_grade", "0"))
       
        selective_thoracic_pref = additional_stand.get("selective_thoracic_pref", "No")
        
        trunk_shift = (stand.get("trunk_shift") or "").strip() 
        
        uev = additional_stand.get("tll_uev", "")

        # Additional — Bending
        bending_l3_4_disc_angle = self._get_float(additional_bend.get("bending_l3_4_disc_angle"), 0)

        # Additional — Standing Sagittal
        lordotic_disc = additional_sag.get("lordotic_disc_below_mt_ltv", "No")
        scsl = additional_sag.get("scsl", "")

        # Shoulder Elevation & T1 tilt (for UIV)
        shoulder_raw = (stand.get("shoulder_elevation", "") or "").strip()
        if shoulder_raw in ("0", "Neutral", "Neither", ""):
            shoulder = "Neither"
        else:
            shoulder = shoulder_raw

        t1_tilt = self._get_float(stand.get("t1_tilt"), 0)
        t1_tilt_sign = "Right" if t1_tilt < 0 else "Left" if t1_tilt > 0 else "Neither"

        print("\n[LEBEL] ===== New Calculation =====")
        print("[LEBEL] Inputs:",
            "pt_cobb", pt_cobb,
            "mt_cobb", mt_cobb,
            "tl_l_cobb", tl_l_cobb,
            "csvl_pos", csvl_pos,
            "pt_bend", pt_bend,
            "mt_bend", mt_bend,
            "tll_bend", tll_bend,
            "t5_12_kyph", t5_12_kyph,
            "t10_l2_kyph", t10_l2_kyph,
            "shoulder", shoulder,
            "t1_tilt", t1_tilt,
            "pt_apex", pt_apex,
            "risser", risser)

        # --- Structural flags (Lenke) ---
        structural_pt = (pt_bend > 25) or (pt_kyph > 20)
        structural_mt = (mt_bend > 25)
        structural_tll = (tll_bend > 25) or (t10_l2_kyph > 20)

        print("[LEBEL] Structural flags:",
            "PT", structural_pt,
            "MT", structural_mt,
            "TL/L", structural_tll)

        # --- Lenke Type ---
        lenke = "Unclassified"
        if structural_mt and not structural_pt and not structural_tll:
            lenke = "Lenke 1"
        elif structural_pt and structural_mt and not structural_tll:
            lenke = "Lenke 2"
        elif structural_mt and structural_tll and not structural_pt:
            # 3 or 6 depending on MT vs TL/L dominance
            lenke = "Lenke 3"
            if mt_cobb < tl_l_cobb:
                lenke = "Lenke 6"
        elif structural_pt and structural_mt and structural_tll:
            lenke = "Lenke 4"
        elif structural_tll and not structural_mt and not structural_pt:
            lenke = "Lenke 5"

        print("[LEBEL] Lenke type:", lenke)


        # --- Modifiers ---
        # Lumbar (CSVL at apex on standing coronal)
        if csvl_pos == "Between Pedicles":
            lumbar_modifier = "A"
        elif csvl_pos == "Touches apical body":
            lumbar_modifier = "B"
        elif csvl_pos == "Completely medial":
            lumbar_modifier = "C"
        else:
            lumbar_modifier = "?"

        # Sagittal (T5–T12 kyphosis)
        if t5_12_kyph < 10:
            sagittal_modifier = "-"
        elif t5_12_kyph <= 40:
            sagittal_modifier = "N"
        else:
            sagittal_modifier = "+"
        
        print("[LEBEL] Modifiers:",
        "lumbar", lumbar_modifier,
        "sagittal", sagittal_modifier)

        # --- UIV ---
        uiv = ""
        uiv_rationale = ""
        if lenke in ("Lenke 1", "Lenke 3", "Lenke 4", "Lenke 6"):
            if shoulder == t1_tilt_sign:
                if pt_apex == "T4":
                    uiv = "T3"
                    uiv_rationale = "Concordant: PT apex at T4 → choose T3"
                else:
                    uiv = "T4"
                    uiv_rationale = "Concordant: PT apex ≠ T4 → choose T4"
            else:
                uiv = "T2"
                uiv_rationale = "Discordant shoulders and T1 tilt → choose T2"
        elif lenke == "Lenke 2":
            uiv = "T2"
            uiv_rationale = "Lenke 2 → always T2"
        elif lenke == "Lenke 5":
            if t10_l2_kyph > 0:
                uiv = "T4"
                uiv_rationale = "TL kyphosis > 0 → choose T4"
            else:
                uiv = uev
                uiv_rationale = f"TL flat/lordotic → choose UEV ({uev})"
        print("[LEBEL] UIV:", uiv, "|", uiv_rationale)

        # --- STF (Lenke 1–4 + lumbar C) ---
        stf_eligible = "No"
        stf_reasons = []
        mt_minus_tll = mt_cobb - tl_l_cobb

        atr = (mt_apical_translation / tll_apical_translation) if (mt_apical_translation and tll_apical_translation) else None
        avrr = (mt_nash_moe / tll_nash_moe) if (mt_nash_moe and tll_nash_moe) else None

        if lenke in ("Lenke 1", "Lenke 2", "Lenke 3", "Lenke 4") and lumbar_modifier == "C":
            if tll_bend < 25: stf_reasons.append("✓ TL/L bend < 25°")
            else: stf_reasons.append("✗ TL/L bend ≥ 25°")

            if mt_minus_tll > 10: stf_reasons.append("✓ MT–TL/L > 10°")
            else: stf_reasons.append("✗ MT–TL/L ≤ 10°")

            if atr and atr > 1.2: stf_reasons.append("✓ ATR > 1.2")
            else: stf_reasons.append("✗ ATR ≤ 1.2 or missing")

            if avrr and avrr > 1.2: stf_reasons.append("✓ AVRR > 1.2")
            else: stf_reasons.append("✗ AVRR ≤ 1.2 or missing")

            if t10_l2_kyph < 10: stf_reasons.append("✓ T10–L2 kyphosis < 10°")
            else: stf_reasons.append("✗ T10–L2 kyphosis ≥ 10°")

            if tl_l_cobb < 50: stf_reasons.append("✓ TL/L standing Cobb < 50°")
            else: stf_reasons.append("✗ TL/L Cobb ≥ 50°")

            if trunk_shift == "Right":
                stf_reasons.append("✓ Trunk shift right")
            else:
                stf_reasons.append("✗ Trunk shift not right")

            if lordotic_disc == "Yes": stf_reasons.append("✓ Lordotic disc below MT-LTV")
            else: stf_reasons.append("✗ No lordotic disc below MT-LTV")

            if all(line.startswith("✓") for line in stf_reasons):
                stf_eligible = "Yes"
        else:
            stf_reasons.append("Not applicable (Lenke ≠ 1–4 or modifier ≠ C)")
        
        print("[LEBEL] STF eligible:", stf_eligible)
        for r in stf_reasons:
            print("   ", r)

        # --- Disc Flexibility Index & TSS ---
        disc_flex_index = None
        if upright_l3_4_disc_angle and upright_l3_4_disc_angle != 0:
            disc_flex_index = round(
                (upright_l3_4_disc_angle - bending_l3_4_disc_angle) / upright_l3_4_disc_angle * 100, 1
            )

        tss = None
        try:
            gravity_score = int(gravity_stability_score)
            rotation_score = int(rotational_stability_score)
            tss = gravity_score + rotation_score
        except Exception:
            tss = None

        # Ratios
        cobb_ratio = (mt_cobb / tl_l_cobb) if (mt_cobb and tl_l_cobb) else None
        translation_ratio = (mt_apical_translation / tll_apical_translation) if (mt_apical_translation and tll_apical_translation) else None

        # --- LIV (logic) ---
        final_liv = ""
        liv_rationale = ""

        if lenke in ("Lenke 1", "Lenke 2"):
            if lumbar_modifier == "A":
                if l4_tilt_direction == "Left":
                    final_liv = sltv or "SLTV"
                    liv_rationale = "Modifier A + L4 tilts left → SLTV"
                else:
                    final_liv = lstv or "LSTV"
                    liv_rationale = "Modifier A + L4 tilts right → LSTV"
            elif lumbar_modifier in ("B", "C"):
                if stf_eligible == "Yes" and selective_thoracic_pref != "No":
                    final_liv = mt_ltv or "MT-LTV"
                    liv_rationale = "Modifier B/C + meets STF → MT-LTV"
                else:
                    final_liv = sltv or "SLTV"
                    liv_rationale = "Modifier B/C + no STF → SLTV"

        elif lenke in ("Lenke 3", "Lenke 4", "Lenke 5", "Lenke 6"):
            risk_factors = []
            if l3_deviation_csvl and l3_deviation_csvl > 20:
                risk_factors.append("L3 deviation > 20mm")
            if l3_rotation_grade in ("2", "3", "4"):
                risk_factors.append("L3 rotation grade ≥ 2")
            if tss is not None and tss <= -5:
                risk_factors.append("Total Stability Score ≤ -5")
            if disc_flex_index is not None and disc_flex_index < 25:
                risk_factors.append("Disc flexibility < 25%")
            if risser is not None and isinstance(risser, int) and risser < 2:
                risk_factors.append("Risser < 2")
            if risk_factors:
                final_liv = "L4"
                liv_rationale = "L4 due to: " + "; ".join(risk_factors)
            else:
                final_liv = "L3"
                liv_rationale = "L3: No risk criteria"
        
        final_liv = self._resolve_level_token(final_liv)

        print("[LEBEL] LIV:", final_liv, "|", liv_rationale)

        # --- SLF (Lenke 5/6 + lumbar C) ---
        slf_eligible = "No"
        slf_reason = ""
        if lenke in ("Lenke 5", "Lenke 6") and lumbar_modifier == "C":
            reasons = []
            if self._shift_dir(trunk_shift) != "Left":
                reasons.append("Trunk shift ≠ Left")
            if shoulder != "Left": reasons.append("Shoulder elevation ≠ Left")
            if not cobb_ratio or cobb_ratio <= 1.25: reasons.append("Cobb ratio ≤ 1.25")
            if not translation_ratio or translation_ratio <= 1.25: reasons.append("Translation ratio ≤ 1.25")
            if not mt_cobb or mt_cobb >= 40: reasons.append("MT Cobb ≥ 40°")
            if not t10_l2_kyph or t10_l2_kyph >= 10: reasons.append("T10–L2 Kyphosis ≥ 10°")
            
            FLEX_THRESH = 30 
            if disc_flex_index is None or disc_flex_index < FLEX_THRESH:
                reasons.append(f"Disc flexibility index < {FLEX_THRESH}%")

            if not reasons:
                slf_eligible = "Yes"
                slf_reason = "Eligible (All criteria met)"
            else:
                slf_reason = "Not eligible: " + "; ".join(reasons)
        else:
            slf_reason = "Not eligible: Lenke ≠ 5/6 or modifier ≠ C"
        print("[LEBEL] SLF eligible:", slf_eligible, "|", slf_reason)

        # --- Package return payload for Page 5 ---
        return {
            "lenke_type": lenke,
            "lumbar_modifier": lumbar_modifier,
            "sagittal_modifier": sagittal_modifier,
            "uiv": uiv or "—",
            "liv": final_liv or "—",
            "uiv_rationale": uiv_rationale,
            "liv_rationale": liv_rationale,
            "stf_eligible": stf_eligible,
            "stf_reasons": stf_reasons,
            "slf_eligible": slf_eligible,
            "slf_reason": slf_reason,
        }

    def _calculate_lenke_tarode(self):
        self.plan_data["logic_results"].update({
            "uiv_tarode": "T2",
            "uiv_rationale_tarode": "Tarode placeholder",
            "liv_tarode": "L4",
            "liv_rationale_tarode": "Tarode placeholder",
            "stf_eligible_tarode": "No",
            "stf_rationale_tarode": "Tarode logic not yet implemented",
            "slf_eligible_tarode": "No",
            "slf_rationale_tarode": "Tarode logic not yet implemented"
        })

    def _calculate_lenke_baldwin(self):
        self.plan_data["logic_results"].update({
            "uiv_baldwin": "T2",
            "uiv_rationale_baldwin": "Baldwin placeholder",
            "liv_baldwin": "L4",
            "liv_rationale_baldwin": "Baldwin placeholder",
            "stf_eligible_baldwin": "No",
            "stf_rationale_baldwin": "Baldwin logic not yet implemented",
            "slf_eligible_baldwin": "No",
            "slf_rationale_baldwin": "Baldwin logic not yet implemented"
        })

    def _calculate_lenke_logic(self):
        logic_source = self.logic_var.get()
        self.plan_data["logic_source"] = logic_source

        if logic_source == "Lebel":
            self._calculate_lenke_lebel()
        elif logic_source == "Tarode":
            self._calculate_lenke_tarode()
        elif logic_source == "Baldwin":
            self._calculate_lenke_baldwin()
    
    def setup_page_6(self):
        if hasattr(self, "page6_notebook") and self.page6_notebook.winfo_exists():
            self.page6_notebook.destroy()

        outer_frame = self.create_standard_page(
            title_text="Intraoperative & Perioperative Setup",
            back_command=self.setup_page_5,
            next_command=self.setup_page_10
        )

        # Notebook
        self.page6_notebook = ttk.Notebook(outer_frame)
        self.page6_notebook.pack(fill="both", expand=True, pady=10)

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 8], width=26)

        tab_configs = [
            ("Operating Room Setup", self._build_tab_operating_room_setup),
            ("Additional Equipment", self._build_tab_additional_equipment),
            ("Pain Reduction Strategies", self._build_tab_pain_reduction),
            ("Infection Reduction Strategies", self._build_tab_infection_reduction),
            ("Blood Conservation Strategies", self._build_tab_blood_conservation), 
            ("Post-Op Recovery", self._build_tab_post_op_recovery),
        ]

        self.page6_tabs = {}
        for tab_name, build_fn in tab_configs:
            tab_frame = ttk.Frame(self.page6_notebook) 
            self.page6_notebook.add(tab_frame, text=tab_name)
            self.page6_tabs[tab_name] = tab_frame

            # Build tab content 
            try:
                build_fn(tab_frame)
            except Exception as e:
                import traceback
                err = ttk.Label(tab_frame, text=f"Error building '{tab_name}': {e}")
                err.pack(anchor="w", padx=8, pady=8)
                print(f"[Page6] Error in {tab_name}:\n{traceback.format_exc()}")

    # Page 9 
    def setup_page_9(self):
        scrollable = self.create_standard_page(
            title_text="Page 9 (placeholder)",
            back_command=self.setup_page_6,
        )
        ttk.Label(scrollable, text="Page 9 placeholder.", font=FONT).pack(pady=20)

    def back_to_post_op(self):
        self.setup_page_6()
        try:
            for idx, tab_id in enumerate(self.page6_notebook.tabs()):
                if self.page6_notebook.tab(tab_id, "text") == "Post-Op Recovery":
                    self.page6_notebook.select(idx)
                    break
        except Exception:
            pass

    def _build_tab_operating_room_setup(self, frame):
        
        sf = ttk.Frame(frame, style="TFrame")
        sf.pack(fill="both", expand=True)

        setup = self.plan_data.setdefault("setup", {})
        self.plan_data.setdefault("patient", {})

        # Apply AIS/NMS defaults 
        self._apply_diagnosis_defaults_once()

        # -----------------------------
        # STATUS LINE (weight + diagnosis)
        # -----------------------------
        weight_used = self._get_weight_kg() or 0.0
        dx_used = (self.plan_data.get("patient", {}).get("diagnosis") or "—")
        ttk.Label(
            sf,
            text=f"Using weight: {weight_used:.1f} kg    |    Diagnosis: {dx_used}",
        ).pack(anchor="w", padx=8, pady=(4, 2))

        # -----------------------------
        # OPERATING TABLE
        # -----------------------------
        table_frame = ttk.LabelFrame(sf, text="Operating Room Setup")
        table_frame.pack(fill="x", pady=(6, 10))

        table_var = tk.StringVar(value=setup.get("table_type", "trios"))
        table_other_text = tk.StringVar(value=setup.get("table_other_text", ""))

        ttk.Radiobutton(
            table_frame,
            text='Mizuho OSI Trios Spinal Surgery Top (Jackson Spinal Bed)',
            variable=table_var, value="trios"
        ).pack(anchor="w", padx=8, pady=2)
        ttk.Radiobutton(
            table_frame, text="Neurosurgical Table",
            variable=table_var, value="neuro"
        ).pack(anchor="w", padx=8, pady=2)

        other_row = ttk.Frame(table_frame); other_row.pack(fill="x", padx=8, pady=(2, 8))
        ttk.Radiobutton(other_row, text="Other:", variable=table_var, value="other").pack(side="left")
        other_entry = ttk.Entry(other_row, textvariable=table_other_text, width=40)
        other_entry.pack(side="left", padx=(6, 0))

        def _toggle_other_entry(*_):
            other_entry.configure(state=("normal" if table_var.get() == "other" else "disabled"))
        _toggle_other_entry()
        table_var.trace_add("write", _toggle_other_entry)

        # -----------------------------
        # TITLE + MASTER ENABLE
        # -----------------------------
        title_row = ttk.Frame(sf); title_row.pack(fill="x", pady=(8, 4))
        tk.Label(
            title_row, text="Cranial–Femoral Traction",
            bg=WHITE, fg=LOGO_GREEN, font=("Segoe UI", 14, "bold")
        ).pack(side="left")
        traction_on = tk.BooleanVar(value=bool(setup.get("traction_on", True)))
        ttk.Checkbutton(title_row, text="Enabled", variable=traction_on).pack(side="left", padx=10)
        # -----------------------------
        # CALC OPTIONS
        # -----------------------------
        calc_frame = ttk.LabelFrame(sf, text="Calculation Options")
        calc_frame.pack(fill="x", pady=(4, 8))
        calc_mode = tk.StringVar(value=setup.get("traction_mode", "Fixed35"))
        for txt, val in [
            ("Fixed Proportion of Body Weight (~35%) – 10% cranial / 25% femoral", "Fixed35"),
            ("Fixed Proportion of Body Weight (~50%) – 25% cranial / 25% femoral", "Fixed50"),
            ("13/26 lbs – Zeller", "Zeller"),
        ]:
            ttk.Radiobutton(calc_frame, text=txt, value=val, variable=calc_mode)\
                .pack(anchor="w", padx=8, pady=2)

        # ----------------------------
        # SUGGESTED + EDITABLE CALC 
        # ----------------------------
        sugg = ttk.LabelFrame(sf, text="Suggested (auto)")
        sugg.pack(fill="x", pady=(6, 8))
        suggest_lbl = ttk.Label(sugg, text="")
        suggest_lbl.pack(anchor="w", padx=8, pady=(8, 6))


        calc_box = tk.Text(sugg, height=6, width=70)
        calc_box.pack(fill="x", padx=8, pady=(0, 6))
        calc_box_dirty = {"val": False}
        def mark_calc_dirty(_): calc_box_dirty["val"] = True
        calc_box.bind("<Key>", mark_calc_dirty)

        ttk.Button(
            sugg, text="Reset Calc Text to Suggested",
            command=lambda: (_fill_calc_text_from_current(), calc_box_dirty.__setitem__("val", False))
        ).pack(anchor="w", padx=8, pady=(0, 8))

        # -----------------------------
        # CRANIAL SECTION
        # -----------------------------
        cranial_frame = ttk.LabelFrame(sf, text="Cranial Traction")
        cranial_frame.pack(fill="x", pady=(4, 8))

        cranial_device = tk.StringVar(
            value=setup.get("cranial_device", setup.get("_default_cranial_device", "gwtongs"))
        )
        dev_row = ttk.Frame(cranial_frame); dev_row.pack(fill="x", padx=8, pady=(8, 4))
        for txt, val in [
            ("None", "none"),
            ("Gardner Wells Tongs", "gwtongs"),
            ("Mayfield Clamp", "mayfield"),
            ("Halo via Mayfield Adapter", "halo"),
        ]:
            ttk.Radiobutton(dev_row, text=txt, value=val, variable=cranial_device)\
                .pack(side="left", padx=(0, 10))

        SpinboxWidget = getattr(ttk, "Spinbox", tk.Spinbox)
        cranial_lbs = tk.DoubleVar(value=float(setup.get("cranial_weight_lbs", 13.0)))
        cranial_row = ttk.Frame(cranial_frame); cranial_row.pack(fill="x", padx=8, pady=6)
        ttk.Label(cranial_row, text="Cranial traction (lbs):", width=24).pack(side="left")
        SpinboxWidget(cranial_row, from_=0, to=200, increment=1.0, width=8, textvariable=cranial_lbs)\
            .pack(side="left")

        # -----------------------------
        # FEMORAL SECTION
        # -----------------------------
        fem_frame = ttk.LabelFrame(sf, text="Femoral Traction")
        fem_frame.pack(fill="x", pady=(4, 10))

        fem_on = tk.BooleanVar(value=bool(setup.get("femoral_on", setup.get("_default_fem_on", True))))
        on_row = ttk.Frame(fem_frame); on_row.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Checkbutton(on_row, text="Enabled", variable=fem_on).pack(side="left")

        fem_type = tk.StringVar(value=setup.get("femoral_type", setup.get("_default_fem_type", "skeletal")))
        type_row = ttk.Frame(fem_frame); type_row.pack(fill="x", padx=8, pady=4)
        for txt, val in [
            ("None", "none"),
            ("Skeletal Traction", "skeletal"),
            ("Traction Boots", "boots"),
            ("Skin Traction", "skin"),
        ]:
            ttk.Radiobutton(type_row, text=txt, value=val, variable=fem_type)\
                .pack(side="left", padx=(0, 10))

        fem_dist = tk.StringVar(value=setup.get("femoral_distribution", setup.get("_default_fem_dist", "symmetric")))
        dist_row = ttk.Frame(fem_frame); dist_row.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Label(dist_row, text="Distribution:").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(dist_row, text="Symmetric", value="symmetric", variable=fem_dist)\
            .pack(side="left", padx=(0, 10))
        ttk.Radiobutton(dist_row, text="Asymmetric", value="asymmetric", variable=fem_dist)\
            .pack(side="left")

        # Symmetric: one per-leg field (mirrors to L/R)
        sym_row = ttk.Frame(fem_frame); sym_row.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(sym_row, text="Femoral total (lbs):", width=28).pack(side="left")
        fem_total = tk.DoubleVar(value=float(setup.get("femoral_total_lbs", 26.0)))
        SpinboxWidget(sym_row, from_=0, to=200, increment=1.0, width=8, textvariable=fem_total).pack(side="left")

        def _sync_total_to_lr(*_):
            if fem_dist.get() != "symmetric":
                return
            try:
                total = int(float(fem_total.get()))
            except Exception:
                return

            left = total // 2
            right = total - left
            fem_l_lbs.set(float(left))
            fem_r_lbs.set(float(right))

        fem_total.trace_add("write", lambda *_: (_sync_total_to_lr(), persist()))

        # Asymmetric: two fields (start hidden)
        asym_row = ttk.Frame(fem_frame); asym_row.pack_forget()
        ttk.Label(asym_row, text="Right femoral weight (lbs):", width=28).pack(side="left")
        fem_r_lbs = tk.DoubleVar(value=float(setup.get("femoral_right_lbs", 13.0)))
        SpinboxWidget(asym_row, from_=0, to=200, increment=1.0, width=8, textvariable=fem_r_lbs)\
            .pack(side="left", padx=(0, 12))
        ttk.Label(asym_row, text="Left femoral weight (lbs):", width=24).pack(side="left")
        fem_l_lbs = tk.DoubleVar(value=float(setup.get("femoral_left_lbs", 13.0)))
        SpinboxWidget(asym_row, from_=0, to=200, increment=1.0, width=8, textvariable=fem_l_lbs)\
            .pack(side="left")

        # -----------------------------
        # HELPERS
        # -----------------------------
        def refresh_visibility(*_):
            on = bool(traction_on.get())
            cran_ok = on and (cranial_device.get() != "none")
            # calc radios active if traction is on
            for w in calc_frame.winfo_children():
                try: w.configure(state=("normal" if on else "disabled"))
                except tk.TclError: pass
            # cranial device radios always active
            for w in dev_row.winfo_children():
                try: w.configure(state="normal")
                except tk.TclError: pass
            # cranial numeric spinbox only if cran_ok
            for w in cranial_row.winfo_children():
                try: w.configure(state=("normal" if cran_ok else "disabled"))
                except tk.TclError: pass

            # femoral headers/radios: active when traction is on
            for w in (on_row, type_row, dist_row):
                for c in w.winfo_children():
                    try: c.configure(state=("normal" if on else "disabled"))
                    except tk.TclError: pass

            numerics_ok = on and bool(fem_on.get()) and (fem_type.get() != "none")

            if fem_dist.get() == "symmetric":
                if not sym_row.winfo_ismapped():
                    sym_row.pack(fill="x", padx=8, pady=(8, 4))
                if asym_row.winfo_ismapped():
                    asym_row.pack_forget()
                for c in sym_row.winfo_children():
                    try: c.configure(state=("normal" if numerics_ok else "disabled"))
                    except tk.TclError: pass
            else:
                if not asym_row.winfo_ismapped():
                    asym_row.pack(fill="x", padx=8, pady=(8, 4))
                if sym_row.winfo_ismapped():
                    sym_row.pack_forget()
                for c in asym_row.winfo_children():
                    try: c.configure(state=("normal" if numerics_ok else "disabled"))
                    except tk.TclError: pass

            _toggle_other_entry()

        def _ensure_distribution_matches_total(s):
            # if symmetric selected but odd total, flip to asymmetric to avoid mismatch
            if fem_dist.get() == "symmetric" and (s["fem_total_lb"] % 2 == 1):
                fem_dist.set("asymmetric")

        def recompute_and_fill(force=False):
            s = self._suggest_traction_weights(self._get_weight_kg(), calc_mode.get(), fem_dist.get())

            # Suggestion label
            if fem_dist.get() == "symmetric":
                suggest_lbl.configure(
                    text=f"Cranial: {s['cranial_lb']} lbs  |  Femoral total: {s['fem_total_lb']} lbs"
                )
            else:
                suggest_lbl.configure(
                    text=f"Cranial: {s['cranial_lb']} lbs  |  Femoral total: {s['fem_total_lb']} lbs  |  "
                        f"Left: {s['fem_left_lb']}  Right: {s['fem_right_lb']}"
                )

            if force:
                cranial_lbs.set(s["cranial_lb"])
                if fem_dist.get() == "symmetric":
                    fem_total.set(s["fem_total_lb"])
                    fem_l_lbs.set(s["fem_left_lb"])
                    fem_r_lbs.set(s["fem_right_lb"])
                else:
                    fem_l_lbs.set(s["fem_left_lb"])
                    fem_r_lbs.set(s["fem_right_lb"])


            if not calc_box_dirty["val"] or force:
                _fill_calc_text_from_suggestions(s)

        def _fill_calc_text_from_suggestions(s):
            text = self._format_calc_text(
                weight_kg=self._get_weight_kg(),
                cranial_lb=s["cranial_lb"],
                fem_total_lb=s["fem_total_lb"],
                fem_left_lb=s["fem_left_lb"],
                fem_right_lb=s["fem_right_lb"],
                mode=calc_mode.get(),
                distribution=fem_dist.get(),
            )

            calc_box.delete("1.0", "end")
            calc_box.insert("1.0", text)

        def _fill_calc_text_from_current():

            text = self._format_calc_text(
                weight_kg=self._get_weight_kg(),
                cranial_lb=float(cranial_lbs.get()),
                fem_total_lb=float(fem_l_lbs.get() + fem_r_lbs.get()),
                fem_left_lb=float(fem_l_lbs.get()),
                fem_right_lb=float(fem_r_lbs.get()),
                mode=calc_mode.get(),
                distribution=fem_dist.get(),
            )

            calc_box.delete("1.0", "end")
            calc_box.insert("1.0", text)

        def persist(*_):
            setup.update({
                "table_type": table_var.get(),
                "table_other_text": table_other_text.get().strip(),
                "traction_on": bool(traction_on.get()),
                "traction_mode": calc_mode.get(),
                "cranial_device": cranial_device.get(),
                "cranial_weight_lbs": float(cranial_lbs.get()),
                "femoral_on": bool(fem_on.get()),
                "femoral_type": fem_type.get(),
                "femoral_distribution": fem_dist.get(),
                "femoral_left_lbs": float(fem_l_lbs.get()),
                "femoral_right_lbs": float(fem_r_lbs.get()),
                "femoral_total_lbs": float(fem_total.get()) if fem_dist.get() == "symmetric" else (float(fem_l_lbs.get()) + float(fem_r_lbs.get())),
                "femoral_per_leg_lbs": (float(fem_total.get()) / 2.0) if fem_dist.get() == "symmetric" else None,
                "traction_calc_notes": calc_box.get("1.0", "end").strip(),
                "patient_weight_kg_at_calc": float(self._get_weight_kg()),
                "_diagnosis_defaults_applied": True,
            })
            self._save_traction_to_plan_data(traction_on, calc_mode, fem_dist, cranial_lbs, fem_l_lbs, fem_r_lbs)

        for v in (table_var, table_other_text, traction_on, calc_mode, cranial_device,
                cranial_lbs, fem_on, fem_type, fem_dist, fem_l_lbs, fem_r_lbs, fem_total):
            v.trace_add("write", lambda *_: (recompute_and_fill(False), refresh_visibility(), persist()))

        recompute_and_fill(force=True)
        refresh_visibility()
        persist()

    def _apply_diagnosis_defaults_once(self):
        setup = self.plan_data.setdefault("setup", {})
        if setup.get("_diagnosis_defaults_applied"):
            return  

        dx = (self.plan_data.get("patient", {}).get("diagnosis") or "").strip().lower()

        # Defaults 
        if "nms" in dx or "neuromuscular" in dx:
            setup.setdefault("traction_on", True)
            setup.setdefault("cranial_device", "mayfield")    
            setup.setdefault("femoral_on", True)
            setup.setdefault("femoral_type", "skeletal")     
            setup.setdefault("femoral_distribution", "symmetric")
        else:  # AIS and all other diagnoses
            setup.setdefault("traction_on", True)
            setup.setdefault("cranial_device", "gwtongs")
            setup.setdefault("femoral_on", True)
            setup.setdefault("femoral_type", "skeletal")
            setup.setdefault("femoral_distribution", "symmetric")

        # record what the suggesitons were
        setup.setdefault("_default_cranial_device", setup.get("cranial_device"))
        setup.setdefault("_default_fem_on", setup.get("femoral_on"))
        setup.setdefault("_default_fem_type", setup.get("femoral_type"))
        setup.setdefault("_default_fem_dist", setup.get("femoral_distribution"))

    def _get_weight_kg(self):
        try:
            return float(self.plan_data.get("patient", {}).get("weight_kg", 0.0))
        except Exception:
            return 0.0

    def _apply_traction_suggestion(
        self,
        traction_mode_var,
        distribution_var,
        cranial_var,
        feml_var,
        femr_var,
        force=False,
        initialize=False,
    ):
        """
        Compatibility helper: computes suggestions using the new spec and, when requested,
        writes them into the provided variables.
        """
        s = self._suggest_traction_weights(self._get_weight_kg(), traction_mode_var.get(), distribution_var.get())

        if hasattr(self, "_traction_suggest_label"):
            self._traction_suggest_label.configure(
                text=f"Cranial: {s['cranial_lb']} lbs  |  Femoral total: {s['fem_total_lb']} lbs  |  "
                    f"Left: {s['fem_left_lb']}  Right: {s['fem_right_lb']}"
            )

        if force or initialize:
            cranial_var.set(float(s["cranial_lb"]))
            if distribution_var.get() == "symmetric":
                per_leg = float(s["fem_per_leg_lb"])
                feml_var.set(per_leg)
                femr_var.set(per_leg)
            else:
                feml_var.set(float(s["fem_left_lb"]))
                femr_var.set(float(s["fem_right_lb"]))

    def _format_calc_text(self, weight_kg, cranial_lb, fem_total_lb, fem_left_lb, fem_right_lb, mode, distribution):
        mode_map = {
            "Fixed35": "Fixed Proportion of Body Weight (~35%): 10% cranial, 25% femoral",
            "Fixed50": "Fixed Proportion of Body Weight (~50%): 25% cranial, 25% femoral",
            "Zeller":  "13/26 lbs – Zeller",
        }

        lines = [
            f"Calculation mode: {mode_map.get(mode, mode)}",
            f"W_kg (patient weight): {weight_kg:.1f} kg",
            "",
            "Cranial traction (lb):",
            f"  C_lb = {int(cranial_lb)}",
            "",
            "Femoral traction – total (lb):",
            f"  F_total_lb = {int(fem_total_lb)}",
            "",
        ]

        if distribution == "asymmetric":
            lines += [
                "Femoral traction – per leg (lb):",
                f"  F_left_lb  = {int(fem_left_lb)}",
                f"  F_right_lb = {int(fem_right_lb)}",
                "",
            ]

        lines += [
            "Notes: Values are floored to whole pounds.",
        ]

        return "\n".join(lines)

    def _suggest_traction_weights(self, weight_kg, mode, distribution):
        lb_per_kg = 2.2046226218
        weight_lb = float(weight_kg) * lb_per_kg

        if mode == "Fixed50":
            cranial = math.floor(0.25 * weight_lb)
            fem_total = math.floor(0.25 * weight_lb)
        elif mode == "Zeller":
            cranial = 13
            fem_total = 26
        else:  # Fixed35
            cranial = math.floor(0.10 * weight_lb)
            fem_total = math.floor(0.25 * weight_lb)

        fem_left = int(fem_total) // 2
        fem_right = int(fem_total) - fem_left  

        fem_per_leg = None
        if distribution == "symmetric":
            fem_per_leg = fem_left 

        return {
            "cranial_lb": int(cranial),
            "fem_total_lb": int(fem_total),
            "fem_left_lb": int(fem_left),
            "fem_right_lb": int(fem_right),
            "fem_per_leg_lb": fem_per_leg,
        }

    def _update_traction_ui(self, container, traction_on_var, distribution_var):
        enabled = bool(traction_on_var.get())
        children = container.winfo_children()
        for idx, child in enumerate(children):
            if idx in (0, 1):
                continue
            try:
                child.configure(state=("normal" if enabled else "disabled"))
            except tk.TclError:
                pass
            for g in child.winfo_children():
                try:
                    g.configure(state=("normal" if enabled else "disabled"))
                except tk.TclError:
                    pass

    def _save_traction_to_plan_data(self, traction_on, traction_mode, distribution, cranial_lbs, fem_l_lbs, fem_r_lbs):
        self.plan_data.setdefault("setup", {})
        self.plan_data["setup"].update({
            "traction_on": bool(traction_on.get()),
            "traction_mode": traction_mode.get(),
            "traction_distribution": distribution.get(),
            "cranial_weight_lbs": float(cranial_lbs.get()),
            "femoral_left_lbs": float(fem_l_lbs.get()),
            "femoral_right_lbs": float(fem_r_lbs.get()),
            "traction_total_lbs": float(cranial_lbs.get()) + float(fem_l_lbs.get()) + float(fem_r_lbs.get()),
            "patient_weight_kg_at_calc": float(self._get_weight_kg()),
        })
    def _diagnosis_is_nms(self) -> bool:
        dx = (self.plan_data.get("patient", {}).get("diagnosis") or "").lower()
        return ("nms" in dx) or ("neuromuscular" in dx)

    def _build_tab_additional_equipment(self, frame):
        equip = self.plan_data.setdefault("additional_equipment", {})
        is_nms = self._diagnosis_is_nms()

        # Always-checked items
        neuro_on = tk.BooleanVar(value=equip.get("neuro_on", True))
        small_cassette_on = tk.BooleanVar(value=equip.get("small_cassette_on", True))
        sonopet_on = tk.BooleanVar(value=equip.get("sonopet_on", True))
        nav7d_on = tk.BooleanVar(value=equip.get("nav7d_on", True))
        suk_on = tk.BooleanVar(value=equip.get("suk_on", True))
        long_radiographs_on = tk.BooleanVar(value=equip.get("long_radiographs_on", True))

        # Neurophysiology section
        neuro_frame = ttk.LabelFrame(frame, text="Neurophysiology (default: ON)")
        neuro_frame.pack(fill="x", pady=(8,6))
        ttk.Checkbutton(neuro_frame, text="Enable Neurophysiology", variable=neuro_on)\
            .pack(anchor="w", padx=8, pady=(8,4))

        modes = equip.get("neuro_modalities", {"SSEPs": True, "MEPs": True, "EMGs": True})
        modal_vars = {k: tk.BooleanVar(value=bool(modes.get(k, True))) for k in ("SSEPs","MEPs","EMGs")}

        row = ttk.Frame(neuro_frame); row.pack(fill="x", padx=8, pady=(0,4))
        ttk.Label(row, text="Modalities:").pack(side="left", padx=(0,10))
        for label in ("SSEPs","MEPs","EMGs"):
            ttk.Checkbutton(row, text=label, variable=modal_vars[label]).pack(side="left", padx=(0,12))

        baseline_default = equip.get("neuro_baseline", "prone")
        baseline_var = tk.StringVar(value=baseline_default)  # "supine" or "prone"
        base_row = ttk.Frame(neuro_frame); base_row.pack(fill="x", padx=8, pady=(0,8))
        ttk.Label(base_row, text="Baseline recordings obtained:").pack(side="left", padx=(0,10))
        ttk.Radiobutton(base_row, text="Supine", variable=baseline_var, value="supine").pack(side="left", padx=(0,10))
        ttk.Radiobutton(base_row, text="Prone (before traction)", variable=baseline_var, value="prone").pack(side="left")

        # Imaging / devices
        xray1 = ttk.LabelFrame(frame, text="Imaging / Devices")
        xray1.pack(fill="x", pady=(6,6))
        ttk.Checkbutton(xray1,
            text="Small Cassette AP digital radiograph 45 minutes after skin cut for level check  (Pager: 416-713-0188)",
            variable=small_cassette_on).pack(anchor="w", padx=8, pady=(8,4))


        ttk.Checkbutton(xray1, text="Stryker iQ Ultrasonic Surgical System with Sonopet iQ Aspirator",
                        variable=sonopet_on).pack(anchor="w", padx=8, pady=4)

        nav = ttk.LabelFrame(frame, text="7D Navigation")
        nav.pack(fill="x", pady=(6,6))
        ttk.Checkbutton(nav, text="Enable 7D Navigation", variable=nav7d_on)\
            .pack(anchor="w", padx=8, pady=(8,4))

        nav_items = equip.get("nav7d_items", {
            "pointer_ball_tip": True,
            "pedicle_probe_lumbar": True,
            "pedicle_probe_sharp": False,
            "spine_reference_clamp": True,
            "flex_array_rod_connector": True,
        })
        nav_vars = {
            "pointer_ball_tip": tk.BooleanVar(value=nav_items.get("pointer_ball_tip", True)),
            "pedicle_probe_lumbar": tk.BooleanVar(value=nav_items.get("pedicle_probe_lumbar", True)),
            "pedicle_probe_sharp": tk.BooleanVar(value=nav_items.get("pedicle_probe_sharp", False)),
            "spine_reference_clamp": tk.BooleanVar(value=nav_items.get("spine_reference_clamp", True)),
            "flex_array_rod_connector": tk.BooleanVar(value=nav_items.get("flex_array_rod_connector", True)),
        }
        for txt, key in [
            ("7D POINTER, BALL TIP", "pointer_ball_tip"),
            ("7D Lumbar Pedicle Probe", "pedicle_probe_lumbar"),
            ("7D Pedicle Probe (Sharp)", "pedicle_probe_sharp"),
            ("7D Spine Reference Clamp", "spine_reference_clamp"),
            ("7D FLEX ARRAY – FLEX ROD CONNECTOR", "flex_array_rod_connector"),
        ]:
            ttk.Checkbutton(nav, text=txt, variable=nav_vars[key]).pack(anchor="w", padx=12, pady=2)

        suk = ttk.LabelFrame(frame, text="Derotation")
        suk.pack(fill="x", pady=(6,6))
        ttk.Checkbutton(suk, text="SUK™ DVR System – Derotator Clamp (Suk Blue on XIA Cart #1)",
                        variable=suk_on).pack(anchor="w", padx=8, pady=(8,4))

        xray2 = ttk.LabelFrame(frame, text="Post-rod Insertion Imaging")
        xray2.pack(fill="x", pady=(6,8))
        ttk.Checkbutton(xray2,
            text="3-foot AP and lateral radiograph after convex rod inserted  (Pager: 416-713-0188)",
            variable=long_radiographs_on).pack(anchor="w", padx=8, pady=(8,8))

        def persist(*_):
            self.plan_data["additional_equipment"] = {
                "neuro_on": bool(neuro_on.get()),
                "neuro_modalities": {k: bool(v.get()) for k, v in modal_vars.items()},
                "neuro_baseline": baseline_var.get(),  # "supine" or "prone"
                "small_cassette_on": bool(small_cassette_on.get()),
                "sonopet_on": bool(sonopet_on.get()),
                "nav7d_on": bool(nav7d_on.get()),
                "nav7d_items": {k: bool(v.get()) for k, v in nav_vars.items()},
                "suk_on": bool(suk_on.get()),
                "long_radiographs_on": bool(long_radiographs_on.get()),
            }

        # Traces
        for v in [neuro_on, small_cassette_on, sonopet_on, nav7d_on, suk_on, long_radiographs_on, baseline_var, *modal_vars.values(), *nav_vars.values()]:
            v.trace_add("write", lambda *_: persist())
        persist()

    def _build_tab_pain_reduction(self, frame):
        pain = self.plan_data.setdefault("pain_reduction", {})

        ttk.Label(frame, text="Select pathway:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(8,4))
        path = tk.StringVar(value=pain.get("pathway", ""))  # "", "intrathecal_morphine", "methadone"

        rb_row = ttk.Frame(frame); rb_row.pack(fill="x", padx=8, pady=(0,8))
        ttk.Radiobutton(rb_row, text="Intra-thecal morphine pathway", variable=path, value="intrathecal_morphine").pack(side="left", padx=(0,18))
        ttk.Radiobutton(rb_row, text="Methadone pathway", variable=path, value="methadone").pack(side="left")

        notes = tk.StringVar(value=pain.get("notes", ""))
        ttk.Label(frame, text="Notes (optional):").pack(anchor="w", padx=8)
        entry = ttk.Entry(frame, textvariable=notes); entry.pack(fill="x", padx=8, pady=(0,8))

        def persist(*_):
            self.plan_data["pain_reduction"] = {"pathway": path.get(), "notes": notes.get().strip()}
        path.trace_add("write", lambda *_: persist())
        notes.trace_add("write", lambda *_: persist())
        persist()


    def _build_tab_infection_reduction(self, frame):
        inf = self.plan_data.setdefault("infection_reduction", {})
        is_nms = self._diagnosis_is_nms()

        # Core checklist (all default checked unless specified below)
        def_bool = lambda key, default=True: tk.BooleanVar(value=bool(inf.get(key, default)))

        pre_abx = def_bool("pre_incision_abx", True)  # cefazolin per kg; re-dose q4h
        ns_after_levelcheck = def_bool("ns_after_level_check", True)
        new_gloves_1 = def_bool("new_gloves_1", True)
        ns_after_facets = def_bool("ns_after_facetectomies", True)
        ns_after_final = def_bool("ns_after_final_radiographs", True)
        new_gloves_2 = def_bool("new_gloves_2", True)
        povidone_paint = def_bool("povidone_paint_implants", True)
        ns_after_povidone = def_bool("ns_after_povidone", True)
        vanc_wound = def_bool("vanc_wound_500mg", True)
        vanc_allograft = def_bool("vanc_allograft_500mg", True)

        core = ttk.LabelFrame(frame, text="Intra-op (defaults)")
        core.pack(fill="x", pady=(8,6))
        for text, var in [
            ("Pre-incision Antibiotics – Cefazolin 30 mg/kg prior (re-dose q4h)", pre_abx),
            ("Normal Saline irrigation 250 ml (warmed) after level check x-ray", ns_after_levelcheck),
            ("New Gloves", new_gloves_1),
            ("Normal Saline irrigation 250 ml (warmed) after facetectomies", ns_after_facets),
            ("Normal Saline irrigation 250 ml (warmed) after final radiographs", ns_after_final),
            ("New Gloves", new_gloves_2),
            ("10% Povidone Iodine Solution painting of implants prior to final closure", povidone_paint),
            ("Normal Saline irrigation 500 ml (warmed) after Povidone Iodine painting", ns_after_povidone),
            ("Vancomycin powder 500 mg at wound closure", vanc_wound),
            ("If allograft used, add Vancomycin powder 500 mg to allograft", vanc_allograft),
        ]:
            ttk.Checkbutton(core, text=text, variable=var).pack(anchor="w", padx=8, pady=2)

        # After incision closed — defaults depend on AIS vs NMS
        post = ttk.LabelFrame(frame, text="After incision closed")
        post.pack(fill="x", pady=(8,6))

        # Steri-Strips (AIS: checked; NMS: checked) x3
        steri_on = tk.BooleanVar(value=bool(inf.get("steristrip_on", True)))
        steri_qty = tk.IntVar(value=int(inf.get("steristrip_qty", 3)))
        row1 = ttk.Frame(post); row1.pack(fill="x", padx=8, pady=(8,4))
        ttk.Checkbutton(row1, text="3M Steri-Strip™ (12 mm × 100 mm)", variable=steri_on).pack(side="left")
        ttk.Label(row1, text="Quantity:").pack(side="left", padx=(10,4))
        ttk.Spinbox(row1, from_=0, to=20, textvariable=steri_qty, width=6).pack(side="left")

        # Dermabond (AIS: unchecked; NMS: checked) x3
        derm_default = True if is_nms else False
        derm_on = tk.BooleanVar(value=bool(inf.get("dermabond_on", derm_default)))
        derm_qty = tk.IntVar(value=int(inf.get("dermabond_qty", 3)))
        row2 = ttk.Frame(post); row2.pack(fill="x", padx=8, pady=4)
        ttk.Checkbutton(row2, text="Ethicon Dermabond", variable=derm_on).pack(side="left")
        ttk.Label(row2, text="Quantity:").pack(side="left", padx=(10,4))
        ttk.Spinbox(row2, from_=0, to=20, textvariable=derm_qty, width=6).pack(side="left")

        # OPSITE sizes (AIS: unchecked; NMS: checked) — default 45×55 checked
        op_default = True if is_nms else False
        op_on = tk.BooleanVar(value=bool(inf.get("opsite_on", op_default)))
        row3 = ttk.Frame(post); row3.pack(fill="x", padx=8, pady=4)
        ttk.Checkbutton(row3, text="OPSITE™", variable=op_on).pack(side="left", padx=(0,12))

        op_size = tk.StringVar(value=inf.get("opsite_size", "45x55"))
        for txt, val in [("45×28 cm","45x28"), ("45×55 cm (Default)","45x55"), ("84×56 cm","84x56")]:
            ttk.Radiobutton(row3, text=txt, variable=op_size, value=val).pack(side="left", padx=(0,12))

        # Steri-Drape (AIS: unchecked; NMS: checked)
        sd_default = True if is_nms else False
        steri_drape_on = tk.BooleanVar(value=bool(inf.get("steri_drape_on", sd_default)))
        row4 = ttk.Frame(post); row4.pack(fill="x", padx=8, pady=(4,8))
        ttk.Checkbutton(row4, text="3M Steri-Drape™ 1010 (45 cm × 60 cm)", variable=steri_drape_on).pack(side="left")

        def persist(*_):
            self.plan_data["infection_reduction"] = {
                "pre_incision_abx": bool(pre_abx.get()),
                "ns_after_level_check": bool(ns_after_levelcheck.get()),
                "new_gloves_1": bool(new_gloves_1.get()),
                "ns_after_facetectomies": bool(ns_after_facets.get()),
                "ns_after_final_radiographs": bool(ns_after_final.get()),
                "new_gloves_2": bool(new_gloves_2.get()),
                "povidone_paint_implants": bool(povidone_paint.get()),
                "ns_after_povidone": bool(ns_after_povidone.get()),
                "vanc_wound_500mg": bool(vanc_wound.get()),
                "vanc_allograft_500mg": bool(vanc_allograft.get()),
                "steristrip_on": bool(steri_on.get()), "steristrip_qty": int(steri_qty.get()),
                "dermabond_on": bool(derm_on.get()), "dermabond_qty": int(derm_qty.get()),
                "opsite_on": bool(op_on.get()), "opsite_size": op_size.get(),
                "steri_drape_on": bool(steri_drape_on.get()),
            }

        for v in [pre_abx, ns_after_levelcheck, new_gloves_1, ns_after_facets, ns_after_final, new_gloves_2,
                povidone_paint, ns_after_povidone, vanc_wound, vanc_allograft,
                steri_on, derm_on, op_on, steri_drape_on, steri_qty, derm_qty, op_size]:
            v.trace_add("write", lambda *_: persist())
        persist()

    def _build_tab_blood_conservation(self, frame):
        blood = self.plan_data.setdefault("blood_conservation", {})

        # TXA (leave dose entry fields, set per-protocol)
        txa_on = tk.BooleanVar(value=blood.get("txa_on", True))
        txa_frame = ttk.LabelFrame(frame, text="Tranexamic Acid (default: ON)")
        txa_frame.pack(fill="x", pady=(8,6))
        ttk.Checkbutton(txa_frame, text="Enable TXA", variable=txa_on).pack(anchor="w", padx=8, pady=(8,4))

        txa_row = ttk.Frame(txa_frame); txa_row.pack(fill="x", padx=8, pady=(0,8))
        txa_bolus = tk.StringVar(value=blood.get("txa_bolus_mg_per_kg", ""))       # e.g., "10"
        txa_infusion = tk.StringVar(value=blood.get("txa_infusion_mg_per_kg_hr", ""))  # e.g., "1"
        ttk.Label(txa_row, text="Bolus (mg/kg):").pack(side="left"); ttk.Entry(txa_row, textvariable=txa_bolus, width=8).pack(side="left", padx=(4,16))
        ttk.Label(txa_row, text="Infusion (mg/kg/hr):").pack(side="left"); ttk.Entry(txa_row, textvariable=txa_infusion, width=8).pack(side="left", padx=4)

        # Cell Saver
        cell_on = tk.BooleanVar(value=blood.get("cell_saver_on", True))
        ttk.Checkbutton(frame, text="Cell Saver – default ON", variable=cell_on).pack(anchor="w", padx=8, pady=(6,8))

        # Floseal
        floseal_on = tk.BooleanVar(value=blood.get("floseal_on", True))
        floseal_frame = ttk.LabelFrame(frame, text='Floseal')
        floseal_frame.pack(fill="x", pady=(4,6))
        ttk.Checkbutton(floseal_frame, text='Enable Floseal', variable=floseal_on)\
            .pack(anchor="w", padx=8, pady=(8,4))
        floseal_loc = tk.StringVar(value=blood.get("floseal_location", "in_room"))  # "in_room" or "open"

        # Floseal quantity (boxes)
        floseal_boxes = tk.IntVar(value=int(blood.get("floseal_boxes", 3)))

        qty_row = ttk.Frame(floseal_frame)
        qty_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(qty_row, text="Quantity (boxes):").pack(side="left", padx=(0, 8))

        SpinboxWidget = getattr(ttk, "Spinbox", tk.Spinbox)
        boxes_spin = SpinboxWidget(qty_row, from_=0, to=20, increment=1, width=6, textvariable=floseal_boxes)
        boxes_spin.pack(side="left")

        loc_row = ttk.Frame(floseal_frame); loc_row.pack(fill="x", padx=8, pady=(0,8))
        rb_in = ttk.Radiobutton(loc_row, text="In Room", variable=floseal_loc, value="in_room")
        rb_op = ttk.Radiobutton(loc_row, text="Open", variable=floseal_loc, value="open")
        rb_in.pack(side="left", padx=(0,12)); rb_op.pack(side="left")

        def _toggle_floseal(*_):
            state = ("normal" if floseal_on.get() else "disabled")
            for w in qty_row.winfo_children():
                try: w.configure(state=state)
                except tk.TclError: pass
            for rb in (rb_in, rb_op):
                rb.configure(state=state)

        _toggle_floseal()
        floseal_on.trace_add("write", lambda *_: _toggle_floseal())

        # Infiltration calculator
        infil_on = tk.BooleanVar(value=blood.get("infiltration_on", False))
        infil = ttk.LabelFrame(frame, text="Infiltration of Bupivacaine / Lidocaine / Epinephrine")
        infil.pack(fill="x", pady=(6,8))
        ttk.Checkbutton(infil, text="Enable Infiltration Calculator", variable=infil_on)\
            .pack(anchor="w", padx=8, pady=(8,4))

        w_row = ttk.Frame(infil); w_row.pack(fill="x", padx=8, pady=(0,8))
        ttk.Label(w_row, text="Patient weight (kg):").pack(side="left")
        infil_w_kg = tk.StringVar(value=str(blood.get("infiltration_weight_kg", "")))
        ttk.Entry(w_row, textvariable=infil_w_kg, width=10).pack(side="left", padx=(6,12))

        # Outputs
        out = ttk.Label(infil, text="", justify="left")
        out.pack(fill="x", padx=8, pady=(0,6))

        notes_lbl = ttk.Label(infil, text="Additional notes:"); notes_lbl.pack(anchor="w", padx=8)
        notes_var = tk.StringVar(value=blood.get("infiltration_notes", ""))
        notes_ent = ttk.Entry(infil, textvariable=notes_var); notes_ent.pack(fill="x", padx=8, pady=(0,8))


        def _compute_infiltration_text():
            """Uses your spec: Bupi 0.5% 1 mg/kg (5 mg/ml); Lido 1% 2 mg/kg (10 mg/ml); Epi 5 mcg/ml × total vol; + 200 ml NS."""
            try:
                W = float(infil_w_kg.get())
            except Exception:
                return "Enter a valid weight (kg) to compute infiltration volumes."

            bupi_mg = 1.0 * W
            lido_mg = 2.0 * W
            bupi_ml = bupi_mg / 5.0    # 0.5% = 5 mg/ml
            lido_ml = lido_mg / 10.0   # 1% = 10 mg/ml
            # total volume (drug volumes + NS)
            total_ml = bupi_ml + lido_ml + 200.0
            epi_conc = 5.0  # mcg/ml
            epi_total_mcg = epi_conc * total_ml
            if epi_total_mcg > 1000.0:
                epi_total_mcg = 1000.0  # round to 1000 mcg if over

            return (
                f"Bupivacaine 0.5%: {bupi_mg:.1f} mg → {bupi_ml:.1f} ml\n"
                f"Lidocaine 1%: {lido_mg:.1f} mg → {lido_ml:.1f} ml\n"
                f"Epinephrine: 5 mcg/ml × {total_ml:.1f} ml = {epi_total_mcg:.0f} mcg total\n"
                f"Normal Saline: 200 ml\n"
                f"Total Volume: {total_ml:.1f} ml"
            )

        def refresh_outputs(*_):
            out.configure(text=_compute_infiltration_text())
            persist()

        def persist(*_):
            self.plan_data["blood_conservation"] = {
                "txa_on": bool(txa_on.get()),
                "txa_bolus_mg_per_kg": txa_bolus.get().strip(),
                "txa_infusion_mg_per_kg_hr": txa_infusion.get().strip(),
                "cell_saver_on": bool(cell_on.get()),
                "floseal_on": bool(floseal_on.get()),
                "floseal_location": floseal_loc.get(),
                "floseal_boxes": int(floseal_boxes.get()),
                "infiltration_on": bool(infil_on.get()),
                "infiltration_weight_kg": infil_w_kg.get().strip(),
                "infiltration_notes": notes_var.get().strip(),
                "infiltration_summary": out.cget("text"),
            }

        # Traces
        for v in [txa_on, txa_bolus, txa_infusion, cell_on, floseal_on, floseal_loc, floseal_boxes,
                infil_on, infil_w_kg, notes_var]:
            v.trace_add("write", lambda *_: refresh_outputs())
        refresh_outputs()

    def _build_tab_post_op_recovery(self, frame):
        rec = self.plan_data.setdefault("post_op_recovery", {})
        is_nms = self._diagnosis_is_nms()

        default_sel = rec.get("destination", "ICU_overnight" if is_nms else "5A_constant_obs")

        ttk.Label(frame, text="Select initial post-operative location:", font=("Segoe UI", 12, "bold"))\
            .pack(anchor="w", padx=8, pady=(8,4))

        dest = tk.StringVar(value=default_sel)
        rb = ttk.Frame(frame); rb.pack(fill="x", padx=8, pady=(0,8))
        ttk.Radiobutton(rb, text="5A Constant Observation (Default if AIS)", variable=dest, value="5A_constant_obs")\
            .pack(anchor="w", pady=2)
        ttk.Radiobutton(rb, text="Pediatric Intensive Care Unit (PICU)", variable=dest, value="PICU")\
            .pack(anchor="w", pady=2)
        ttk.Radiobutton(rb, text="Overnight Intensive Care Unit (Default if NMS)", variable=dest, value="ICU_overnight")\
            .pack(anchor="w", pady=2)

        notes = tk.StringVar(value=rec.get("notes", ""))
        ttk.Label(frame, text="Notes (optional):").pack(anchor="w", padx=8)
        entry = ttk.Entry(frame, textvariable=notes); entry.pack(fill="x", padx=8, pady=(0,8))

        def persist(*_):
            self.plan_data["post_op_recovery"] = {"destination": dest.get(), "notes": notes.get().strip()}
        dest.trace_add("write", lambda *_: persist())
        notes.trace_add("write", lambda *_: persist())
        persist()
        
    def _ensure_contacts_block(self):
        contacts = self.plan_data.setdefault("contacts", {})

        defaults = {
            "anaesthesiologist": {"name": "", "email": "", "enabled": True},
            "perfusionist": {"name": "", "email": "", "enabled": True},
            "orthopaedic_technologist": {"name": "", "email": "", "enabled": True},
            "scrub_nurse": {"name": "", "email": "", "enabled": True},
            "neurophysiologist": {"name": "", "email": "", "enabled": True},
            "supply_chain_manager": {"name": "", "email": "", "enabled": True},
            "industry_spine_implants": {"name": "", "email": "", "enabled": True},
            "industry_navigation": {"name": "", "email": "", "enabled": True},
        }

        for k, v in defaults.items():
            if k not in contacts or not isinstance(contacts.get(k), dict):
                contacts[k] = v.copy()
            else:
                contacts[k].setdefault("name", "")
                contacts[k].setdefault("email", "")
                contacts[k].setdefault("enabled", True)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlowbiWanApp(root)
    root.mainloop()