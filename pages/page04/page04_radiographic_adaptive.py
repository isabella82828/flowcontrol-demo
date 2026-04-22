import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
import os
from PIL import Image, ImageTk 
import subprocess
from tkinter import messagebox

from pages.page04.logic.lebel_v3 import compute_lebel_v3
from pages.page04.logic.baldwin_v2 import compute_baldwin_v2
from pages.page04.help_popup import show_help_popup 
from pages.page04.help_texts import get_help
from pages.page04.help_texts import get_help_item
from shared.shared_measurements import import_slicer_measurements_into_plan_data

WHITE = "#FFFFFF"
FONT = ("Segoe UI", 12)

VERTEBRA_LEVELS = [
    "-",
    "T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12",
    "L1","L2","L3","L4","L5",
    "S1"
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELP_ICON_PATH = os.path.join(BASE_DIR, "assets", "question-mark.png")


def _help_icon(parent, tab: str, key: str, fallback_title: str, size: int = 20):
    img = Image.open(HELP_ICON_PATH).resize((size, size), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)

    lbl = tk.Label(parent, image=photo, bg=WHITE, cursor="hand2")
    lbl.image = photo

    item = get_help_item(tab, key)
    title = item.title if item else fallback_title
    body = item.body if item else ""
    image_path = _abs_from_rel(item.image_relpath) if (item and item.image_relpath) else None

    def _open(_evt=None):
        show_help_popup(parent, title, body, image_path=image_path)

    lbl.bind("<Button-1>", _open)
    return lbl

def _ensure_dict(d, key):
   if key not in d or not isinstance(d[key], dict):
       d[key] = {}
   return d[key]


def _rp_get(app, tab, key, default=""):
   rp = app.plan_data.get("radiographic_parameters", {})
   return (rp.get(tab, {}) or {}).get(key, default)


def _rp_set(app, tab, key, value):
   rp = _ensure_dict(app.plan_data, "radiographic_parameters")
   t = _ensure_dict(rp, tab)
   t[key] = value
   app.is_dirty = True


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _abs_from_rel(rel: str) -> str:
    return str(PROJECT_ROOT / rel)

class Page04RadiographicAdaptive:
   def __init__(self, app):
       self.app = app
       self.sections = {}
       self.frames = {}        
       self.vars = {}
       self.preview_vars = {}


   def setup(self):
       scrollable = self.app.create_standard_page(
           title_text="Radiographic Parameters",
           back_command=self.app.setup_page_3,
           next_command=self.on_next
       )
       # -----------------------------
       # Slicer Import Button
       # -----------------------------
       btn_frame = tk.Frame(scrollable, bg=WHITE)
       btn_frame.pack(fill="x", pady=(4, 10), padx=6)

       tk.Button(
            btn_frame,
            text="Open 4D Slicer Measurement Module",
            font=("Segoe UI", 11, "bold"),
            command=self.on_open_slicer_angle,
            bg="#E8F0FE"
        ).pack(side="left", padx=(0, 8))

       tk.Button(
            btn_frame,
            text="Import Slicer Measurements",
            font=("Segoe UI", 11, "bold"),
            command=self.on_import_slicer_measurements,
            bg="#E8F0FE"
        ).pack(side="left")

       # -----------------------------
       # Helpers to add fields
       # -----------------------------
       
       def add_entry(parent, label, tab, key, width=10, help_text: Optional[str] = None):
            row = tk.Frame(parent, bg=WHITE)
            row.pack(fill="x", pady=4)

            left = tk.Frame(row, bg=WHITE)
            left.pack(side="left", fill="x", expand=True)

            tk.Label(left, text=label, bg=WHITE, font=FONT).pack(side="left")

            item = get_help_item(tab, key)
            if item and item.body:
                _help_icon(left, tab, key, label).pack(side="left", padx=6)

            var = tk.StringVar(value=_rp_get(self.app, tab, key, ""))
            ent = ttk.Entry(row, textvariable=var, width=width)
            ent.pack(side="right")

            def _on_write(*_):
                _rp_set(self.app, tab, key, var.get().strip())
                self.refresh()

            var.trace_add("write", _on_write)
            self.vars.setdefault((tab, key), []).append(var)
            return var, row

       def add_combo(parent, label, tab, key, options, width=18, default=None,
                    write_default=True, help_text: Optional[str] = None):
            row = tk.Frame(parent, bg=WHITE)
            row.pack(fill="x", pady=4)

            left = tk.Frame(row, bg=WHITE)
            left.pack(side="left", fill="x", expand=True)

            tk.Label(left, text=label, bg=WHITE, font=FONT).pack(side="left")

            item = get_help_item(tab, key)
            if item and item.body:
                _help_icon(left, tab, key, label).pack(side="left", padx=6)

            var = tk.StringVar(value=_rp_get(self.app, tab, key, default or options[0]))
            cb = ttk.Combobox(row, values=options, textvariable=var, state="readonly", width=width)
            cb.pack(side="right")

            def _on_select(_=None):
                _rp_set(self.app, tab, key, var.get().strip())
                self.refresh()

            cb.bind("<<ComboboxSelected>>", _on_select)
            self.vars.setdefault((tab, key), []).append(var)

            if write_default:
                _rp_set(self.app, tab, key, var.get().strip())

            return var, row

       # -----------------------------
       # Section: Lenke inputs (always visible)
       # -----------------------------
       sec_lenke = ttk.LabelFrame(scrollable, text="Radiographic Parameters")
       sec_lenke.pack(fill="x", pady=(10, 8), padx=6)
       self.sections["lenke"] = sec_lenke

       # --- Subframes per scolimaster ---
       lenke_lebel = tk.Frame(sec_lenke, bg=WHITE)
       lenke_lebel.pack(fill="x")
       self.frames["lenke_lebel"] = lenke_lebel

       lenke_baldwin = tk.Frame(sec_lenke, bg=WHITE)
       lenke_baldwin.pack(fill="x")
       self.frames["lenke_baldwin"] = lenke_baldwin


       # Standing coronal
       add_entry(lenke_lebel, "PT Cobb (standing)", "standing_coronal", "pt_cobb")
       add_entry(lenke_lebel, "MT Cobb (standing)", "standing_coronal", "mt_cobb")
       add_entry(lenke_lebel, "TL/L Cobb (standing)", "standing_coronal", "tl_l_cobb")
       add_entry(lenke_lebel, "T1 tilt", "standing_coronal", "t1_tilt")

       add_combo(
           lenke_lebel,
           "CSVL at TL/L Apex Position",
           "standing_coronal",
           "csvl_tll_apex_position",
           ["Between Pedicles", "Touches apical body", "Completely medial"],
           width=22
       )


       # Standing sagittal
       add_entry(lenke_lebel, "T2–T5 Kyphosis", "standing_sagittal", "t2_5_kyphosis")
       add_entry(lenke_lebel, "T5–T12 Kyphosis", "standing_sagittal", "t5_12_kyphosis")
       add_entry(lenke_lebel, "T10–L2 Kyphosis", "standing_sagittal", "t10_l2_kyphosis")


       add_combo(
            lenke_lebel,
            "PT Apex Level",
            "standing_sagittal",
            "pt_apex_level",
            ["T1", "T2", "T3", "T4", "T5"],
            width=8,
            default="T4"
        )

       # Bending (coronal)
       add_entry(lenke_lebel, "PT Cobb - Bending", "bending", "pt_cobb")
       add_entry(lenke_lebel, "MT Cobb - Bending", "bending", "mt_cobb")
       add_entry(lenke_lebel, "TL/L Cobb - Bending", "bending", "tl_l_cobb")

       add_entry(lenke_lebel, "Risser score", "standing_coronal", "risser_score")

       add_combo(
           lenke_lebel,
           "Shoulder Elevation",
           "standing_coronal",
           "shoulder_elevation",
           ["Left", "Right", "Neither"],
           width=10,
           default="Neither"
       )

       add_combo(
           lenke_lebel,
           "Trunk Shift Direction",
           "standing_coronal",
           "trunk_shift",
           ["Left", "Right", "Neither"],
           width=10,
           default="Neither"
       )

       add_combo(
           lenke_lebel,
           "Variant vertebral anatomy present?",
           "additional_standing_coronal",
           "variant_vertebral_anatomy",
           ["No", "Yes"],
           width=8,
           default="No"
       )

       self.variant_detail_lebel_frame = tk.Frame(lenke_lebel, bg=WHITE)
       self.variant_detail_lebel_frame.pack(fill="x")

       add_combo(
            self.variant_detail_lebel_frame,
            "Lumbar vertebral variant",
            "additional_standing_coronal",
            "lumbar_variant_type",
            ["4 lumbar vertebrae", "6 lumbar vertebrae", "Other"],
            width=20,
            default="Other"
        )


       # -----------------------------
       # Baldwin Lenke inputs (minimal)
       # -----------------------------
       add_entry(lenke_baldwin, "MT Cobb (standing)", "standing_coronal", "mt_cobb")
       add_entry(lenke_baldwin, "TL/L Cobb (standing)", "standing_coronal", "tl_l_cobb")

       add_combo(
           lenke_baldwin,
           "CSVL at TL/L apex position",
           "standing_coronal",
           "csvl_tll_apex_position",
           ["Centered", "Shifted", "Lateral"],
           width=12,
           default="Centered",
           write_default=False
       )

       add_entry(lenke_baldwin, "T2–T5 Kyphosis", "standing_sagittal", "t2_5_kyphosis")
       add_entry(lenke_baldwin, "T5–T12 Kyphosis", "standing_sagittal", "t5_12_kyphosis")
       add_entry(lenke_baldwin, "T10–L2 Kyphosis", "standing_sagittal", "t10_l2_kyphosis")

       add_entry(lenke_baldwin, "PT Cobb - Bending", "bending", "pt_cobb")
       add_entry(lenke_baldwin, "MT Cobb - Bending", "bending", "mt_cobb")
       add_entry(lenke_baldwin, "TL/L Cobb - Bending", "bending", "tl_l_cobb")

       add_combo(
           lenke_baldwin,
           "Shoulder Elevation",
           "standing_coronal",
           "shoulder_elevation",
           ["Left", "Right", "Neither"],
           width=10,
           default="Neither",
           write_default=False
       )

       add_combo(
           lenke_baldwin,
           "Trunk shift direction",
           "standing_coronal",
           "trunk_shift",
           ["Left", "Right", "Neither"],
           width=10,
           default="Neither",
           write_default=False
       )
    
       add_combo(
           lenke_baldwin,
           "Variant vertebral anatomy present",
           "additional_standing_coronal",
           "variant_vertebral_anatomy",
           ["No", "Yes"],
           width=8,
           default="No",
           write_default=False
       )

       self.variant_detail_baldwin_frame = tk.Frame(lenke_baldwin, bg=WHITE)
       self.variant_detail_baldwin_frame.pack(fill="x")

       add_combo(
            self.variant_detail_baldwin_frame,
            "Lumbar vertebral variant",
            "additional_standing_coronal",
            "lumbar_variant_type",
            ["4 lumbar vertebrae", "6 lumbar vertebrae", "Other"],
            width=20,
            default="Other",
            write_default=False
        )


       # Start with Baldwin hidden (Lebel default)
       self._hide(self.frames["lenke_baldwin"])


       # -----------------------------
       # Live preview outputs
       # -----------------------------
       prev = ttk.LabelFrame(scrollable, text="Lenke Classification")
       prev.pack(fill="x", pady=(6, 8), padx=6)


       def add_preview_row(label, key):
           row = tk.Frame(prev, bg=WHITE)
           row.pack(fill="x", pady=3)
           tk.Label(row, text=label + ":", bg=WHITE, font=FONT).pack(side="left")
           v = tk.StringVar(value="—")
           ttk.Label(row, textvariable=v, font=FONT).pack(side="left", padx=10)
           self.preview_vars[key] = v


       add_preview_row("Lenke type", "lenke_type")
       add_preview_row("Lumbar modifier", "lumbar_modifier")
       add_preview_row("Sagittal modifier", "sagittal_modifier")

       # -----------------------------
       # Anatomy warning box
       # -----------------------------
       sec_warning = ttk.LabelFrame(scrollable, text="Anatomy Warning")
       sec_warning.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["anatomy_warning"] = sec_warning

       self.preview_vars["anatomy_warning"] = tk.StringVar(value="")

       ttk.Label(
           sec_warning,
           textvariable=self.preview_vars["anatomy_warning"],
           wraplength=900,
           justify="left"
       ).pack(anchor="w", padx=8, pady=(6, 8))

       # -----------------------------
       # Shared: Apical translations (used by STF + SLF)
       # -----------------------------
       sec_trans = ttk.LabelFrame(scrollable, text="Apical Translations")
       sec_trans.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["translations"] = sec_trans


       add_entry(sec_trans, "MT apical translation (mm)", "standing_coronal", "mt_apical_translation_mm")
       add_entry(sec_trans, "TL/L apical translation (mm)", "standing_coronal", "tll_apical_translation_mm")


       # -----------------------------
       # STF section
       # -----------------------------
       sec_stf = ttk.LabelFrame(scrollable, text="Selective Thoracic Fusion (STF)")
       sec_stf.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["stf"] = sec_stf


       add_entry(sec_stf, "MT Nash-Moe grade", "standing_coronal", "mt_nashmoe_grade")
       add_entry(sec_stf, "TL/L Nash-Moe grade", "standing_coronal", "tll_nashmoe_grade")


       add_combo(sec_stf, "Lordotic disc below MT-LTV", "additional_standing_sagittal", "lordotic_disc_below_mt_ltv",
                 ["Yes", "No"], width=8, default="No")


       add_combo(sec_stf, "Proceed with STF? (patient preference)", "additional_standing_coronal", "selective_thoracic_pref",
                 ["Yes", "No"], width=8, default="No")


       # STF status text
       self.preview_vars["stf_eligible"] = tk.StringVar(value="—")
       ttk.Label(sec_stf, textvariable=self.preview_vars["stf_eligible"]).pack(anchor="w", padx=8, pady=(6, 2))
       self.preview_vars["stf_summary"] = tk.StringVar(value="")
       ttk.Label(sec_stf, textvariable=self.preview_vars["stf_summary"], wraplength=900, justify="left").pack(anchor="w", padx=8, pady=(0, 2))

       self.stf_box = tk.Text(sec_stf, height=6, wrap="word", font=("Segoe UI", 10))
       self.stf_box.pack(fill="x", padx=8, pady=(2, 8))
       self.stf_box.config(state="disabled")


       # -----------------------------
       # SLF section
       # -----------------------------
       sec_slf = ttk.LabelFrame(scrollable, text="Selective Lumbar Fusion (SLF)")
       sec_slf.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["slf"] = sec_slf


       self.preview_vars["slf"] = tk.StringVar(value="—")
       ttk.Label(sec_slf, textvariable=self.preview_vars["slf"]).pack(anchor="w", padx=8, pady=(6, 8))


       # -----------------------------
       # UIV section
       # -----------------------------
       sec_uiv = ttk.LabelFrame(scrollable, text="Upper Instrumented Vertebra (UIV)")
       sec_uiv.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["uiv"] = sec_uiv

       self.preview_vars["uiv"] = tk.StringVar(value="—")
       ttk.Label(
           sec_uiv,
           textvariable=self.preview_vars["uiv"],
           font=("Segoe UI", 12, "bold")
       ).pack(anchor="w", padx=8, pady=(6, 2))

       self.uiv_reason = tk.StringVar(value="")
       ttk.Label(
           sec_uiv,
           textvariable=self.uiv_reason
       ).pack(anchor="w", padx=8, pady=(0, 8))

       # Baldwin-only UIV input(s)
       self.uiv_baldwin_frame = tk.Frame(sec_uiv, bg=WHITE)
       self.uiv_baldwin_frame.pack(fill="x")

       add_entry(
            self.uiv_baldwin_frame,
            "TL/L UEV",
            "additional_standing_coronal",
            "tll_uev",
            width=10
        )

       # -----------------------------
       # LIV section
       # -----------------------------
       sec_liv = ttk.LabelFrame(scrollable, text="Lowest Instrumented Vertebra (LIV)")
       sec_liv.pack(fill="x", pady=(6, 8), padx=6)
       self.sections["liv"] = sec_liv
       
       # Lebel Lenke 1/2 LIV inputs
       self.liv_lebel_12_frame = tk.Frame(sec_liv, bg=WHITE)
       self.liv_lebel_12_frame.pack(fill="x")

       add_combo(
            self.liv_lebel_12_frame,
            "L4 tilt direction",
            "additional_standing_coronal",
            "l4_tilt_direction",
            ["Left", "Right", "Neutral"],
            width=10,
            default="Neutral"
        )
       
       add_combo(
            self.liv_lebel_12_frame,
            "MT-LTV",
            "standing_coronal",
            "mt_ltv",
            VERTEBRA_LEVELS,
            width=10,
            default="-"
        )

       add_combo(
            self.liv_lebel_12_frame,
            "Supine Last Touched Vertebrae (SLTV)",
            "additional_supine_coronal",
            "sltv",
            VERTEBRA_LEVELS,
            width=10,
            default="-"
        )

       add_combo(
            self.liv_lebel_12_frame,
            "Last substantially touched vertebra (LSTV)",
            "standing_coronal",
            "last_substantially_touched_vertebra",
            VERTEBRA_LEVELS,
            width=10,
            default="-"
        )

       # Baldwin STF-path LIV inputs
       self.liv_baldwin_12_frame = tk.Frame(sec_liv, bg=WHITE)
       self.liv_baldwin_12_frame.pack(fill="x")
       
       add_entry(
            self.liv_baldwin_12_frame,
            "Supine Last Touched Vertebrae (SLTV)",
            "additional_standing_coronal",
            "stable_vertebra",
            width=10
        )
       
       add_combo(
            self.liv_baldwin_12_frame,
            "MT-LTV",
            "additional_standing_coronal",
            "mt_ltv",
            VERTEBRA_LEVELS,
            width=10,
            default="-",
            write_default=False
        )

       # Non-STF LIV inputs, Baldwin 3–6 path, and Lebel 3–6 path
       self.liv_36_frame = tk.Frame(sec_liv, bg=WHITE)
       self.liv_36_frame.pack(fill="x")

       add_entry(self.liv_36_frame, "Lumbar apex level (e.g., L1, L2)", "standing_sagittal", "lumbar_apex_level", width=10)
       add_entry(self.liv_36_frame, "Bending L3-4 disc angle", "additional_bending", "bending_l3_4_disc_angle", width=10)
       
       add_combo(
            self.liv_36_frame,
            "NV grade (≥ -4 passes)",
            "additional_standing_coronal",
            "nv_grade",
            ["0", "-1", "-2", "-3", "-4"],
            width=6,
            default="0"
        )

       # Lebel-only S1 plumb line check inputs
       self.liv_lebel_s1_frame = tk.Frame(sec_liv, bg=WHITE)
       self.liv_lebel_s1_frame.pack(fill="x")

       add_combo(
            self.liv_lebel_s1_frame,
            "S1 plumb line relation at L3",
            "additional_standing_sagittal",
            "s1_plumb_line_l3_relation",
            ["Intersected", "Anterior", "Posterior"],
            width=12,
            default="Intersected"
        )

       add_combo(
            self.liv_lebel_s1_frame,
            "S1 plumb line relation at L4",
            "additional_standing_sagittal",
            "s1_plumb_line_l4_relation",
            ["Intersected", "Anterior", "Posterior"],
            width=12,
            default="Intersected"
        )

       add_combo(
            self.liv_lebel_s1_frame,
            "S1 plumb line relation at L5",
            "additional_standing_sagittal",
            "s1_plumb_line_l5_relation",
            ["Intersected", "Anterior", "Posterior"],
            width=12,
            default="Intersected"
        ) 

       # LIV preview
       self.preview_vars["liv"] = tk.StringVar(value="—")
       ttk.Label(sec_liv, textvariable=self.preview_vars["liv"], font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
       self.liv_reason = tk.StringVar(value="")
       ttk.Label(sec_liv, textvariable=self.liv_reason).pack(anchor="w", padx=8, pady=(0, 8))

       # Start hidden sections
       self._hide(self.sections["translations"])
       self._hide(self.sections["stf"])
       self._hide(self.sections["liv"])
       self._hide(self.sections["slf"])
       self._hide(self.sections["uiv"])
       self._hide(self.sections["anatomy_warning"])
       self._hide(self.uiv_baldwin_frame)
       self._hide(self.liv_baldwin_12_frame)
       self._hide(self.liv_36_frame)
       self._hide(self.liv_lebel_s1_frame)
       self._hide(self.liv_lebel_12_frame)
       self._hide(self.variant_detail_lebel_frame)
       self._hide(self.variant_detail_baldwin_frame)


       # Initial compute
       self.refresh()
      
   def _hide(self, w):
       try:
           w.pack_forget()
       except Exception:
           pass


   def _show(self, w):
       if not w.winfo_ismapped():
           w.pack(fill="x", pady=(6, 8), padx=6)


   def _has_value(self, v) -> bool:
       return v is not None and str(v).strip() != ""


   def _all_present(self, d: Dict[str, str], keys) -> bool:
       return all(self._has_value(d.get(k)) for k in keys)


   def _flatten_inputs_for_lebel(self) -> Dict[str, str]:
       rp = self.app.plan_data.get("radiographic_parameters", {})

       stand = rp.get("standing_coronal", {}) or {}
       sag = rp.get("standing_sagittal", {}) or {}
       bend = rp.get("bending", {}) or {}
       sup = rp.get("additional_supine_coronal", {}) or {}
       add_stand = rp.get("additional_standing_coronal", {}) or {}
       add_sag = rp.get("additional_standing_sagittal", {}) or {}
       add_bend = rp.get("additional_bending", {}) or {}


       return {
           # Standing cobbs
           "pt_cobb": stand.get("pt_cobb"),
           "mt_cobb": stand.get("mt_cobb"),
           "tll_cobb": stand.get("tl_l_cobb"),


           # Bending cobbs
           "pt_bend": bend.get("pt_cobb"),
           "mt_bend": bend.get("mt_cobb"),
           "tll_bend": bend.get("tl_l_cobb"),


           # Sagittal
           "t2_5_kyphosis": sag.get("t2_5_kyphosis"),
           "t5_12_kyphosis": sag.get("t5_12_kyphosis"),
           "t10_l2_kyphosis": sag.get("t10_l2_kyphosis"),
           "pt_apex_level": sag.get("pt_apex_level"),


           # Modifiers
           "csvl_apex_position": stand.get("csvl_tll_apex_position"),
           "shoulder_elevation": stand.get("shoulder_elevation"),
           "t1_tilt_direction": self._t1_tilt_to_dir(stand.get("t1_tilt")),
           "uev": add_stand.get("tll_uev"),
           "risser_score": stand.get("risser_score"),
           "variant_vertebral_anatomy": add_stand.get("variant_vertebral_anatomy"),
           "lumbar_variant_type": add_stand.get("lumbar_variant_type"),


           # STF
           "mt_apical_translation_mm": stand.get("mt_apical_translation_mm"),
           "tll_apical_translation_mm": stand.get("tll_apical_translation_mm"),
           "mt_nashmoe_grade": stand.get("mt_nashmoe_grade"),
           "tll_nashmoe_grade": stand.get("tll_nashmoe_grade"),
           "trunk_shift_direction": stand.get("trunk_shift"),
           "lordotic_disc_below_mt_ltv": add_sag.get("lordotic_disc_below_mt_ltv"),
           "wants_stf": add_stand.get("selective_thoracic_pref"),


           # LIV (Lenke 1/2)
           "l4_tilt_direction": add_stand.get("l4_tilt_direction"),
           "sltv": sup.get("sltv"),
           "lstv": stand.get("last_substantially_touched_vertebra"),
           "mt_ltv": stand.get("mt_ltv"),


           # LIV (Lenke 3–6)
           "l3_deviation_csvl_mm": stand.get("l3_deviation_csvl_mm"),
           "l3_rotation_grade": add_stand.get("l3_rotation_grade"),
           "sv_grade": add_stand.get("sv_grade"),
           "nv_grade": add_stand.get("nv_grade"),
           "upright_l3_4_disc_angle": sag.get("l3_4_disc_angle_upright"),
           "bending_l3_4_disc_angle": add_bend.get("bending_l3_4_disc_angle"),
           "s1_plumb_line_l3_relation": add_sag.get("s1_plumb_line_l3_relation"),
           "s1_plumb_line_l4_relation": add_sag.get("s1_plumb_line_l4_relation"),
           "s1_plumb_line_l5_relation": add_sag.get("s1_plumb_line_l5_relation"),
       }

   def _present_for_baldwin(self) -> Dict[tuple, str]:
       rp = self.app.plan_data.get("radiographic_parameters", {}) or {}
       present = {}
       for tab, data in rp.items():
           if isinstance(data, dict):
               for k, v in data.items():
                   present[(tab, k)] = v
       return present
   
   def _t1_tilt_to_dir(self, v):
       try:
           if v is None or str(v).strip() == "":
               return "Neither"
           x = float(v)
           if x > 0:
               return "Left"
           if x < 0:
               return "Right"
           return "Neither"
       except Exception:
           return "Neither"

   def refresh(self):
        logic_source = (self.app.plan_data.get("logic_source") or "Lebel")

        if logic_source == "Lebel":
            self._show(self.frames["lenke_lebel"])
            self._hide(self.frames["lenke_baldwin"])
        else:
            self._hide(self.frames["lenke_lebel"])
            self._show(self.frames["lenke_baldwin"])

            variant_flag = self.app.plan_data.get("radiographic_parameters", {}) \
            .get("additional_standing_coronal", {}) \
            .get("variant_vertebral_anatomy", "No")

            if variant_flag == "Yes":
                if not self.variant_detail_baldwin_frame.winfo_ismapped():
                    self.variant_detail_baldwin_frame.pack(fill="x")
            else:
                self.variant_detail_baldwin_frame.pack_forget()

            present = self._present_for_baldwin()
            results = compute_baldwin_v2(present)
            
            warning_text = results.get("anatomy_warning", "").strip()
            if warning_text:
                self.preview_vars["anatomy_warning"].set(warning_text)
                self._show(self.sections["anatomy_warning"])
            else:
                self.preview_vars["anatomy_warning"].set("")
                self._hide(self.sections["anatomy_warning"])

            # Preview updates
            self.preview_vars["lenke_type"].set(results.get("lenke_type", "—"))
            self.preview_vars["lumbar_modifier"].set(results.get("lumbar_modifier", "—"))
            self.preview_vars["sagittal_modifier"].set(results.get("sagittal_modifier", "—"))

            hints = results.get("ui_hints", {}) or {}
            sections = hints.get("sections", {}) or {}

            # Show or hide sections based on Baldwin gating
            if sections.get("translations"):
                self._show(self.sections["translations"])
            else:
                self._hide(self.sections["translations"])

            if sections.get("stf"):
                self._show(self.sections["stf"])
                self.preview_vars["stf_eligible"].set(
                    f"STF eligible: {results.get('stf_eligible', '—')}"
                )

                passed = results.get("stf_passed_count", 0)
                total = results.get("stf_total_count", 0)
                suggestion = results.get("stf_suggestion", "")
                note = results.get("stf_suggestion_note", "")

                summary = f"STF criteria met: {passed}/{total}"
                if suggestion:
                    summary += f" | {suggestion}"
                if note:
                    summary += f" | {note}"

                self.preview_vars["stf_summary"].set(summary)
                self._fill_text(self.stf_box, results.get("stf_reasons", []))
           
            else:
                self._hide(self.sections["stf"])
                self.preview_vars["stf_summary"].set("")

            if sections.get("slf"):
                self._show(self.sections["slf"])
                self.preview_vars["slf"].set(
                    f"SLF eligible: {results.get('slf_eligible', '—')}  |  {results.get('slf_reason', '')}"
                )
            else:
                self._hide(self.sections["slf"])

            if sections.get("uiv"):
                self._show(self.sections["uiv"])
                self.preview_vars["uiv"].set(f"UIV: {results.get('uiv', '—')}")
                self.uiv_reason.set(results.get("uiv_rationale", ""))

                lenke_type = results.get("lenke_type", "Unclassified")
                t10_l2_raw = self.app.plan_data.get("radiographic_parameters", {}) \
                    .get("standing_sagittal", {}) \
                    .get("t10_l2_kyphosis", "")

                try:
                    t10_l2_val = float(t10_l2_raw)
                except Exception:
                    t10_l2_val = None

                # Baldwin needs TL/L UEV only for Lenke 5 when T10-L2 <= 20
                if lenke_type == "Lenke 5" and (t10_l2_val is None or t10_l2_val <= 20):
                    self._show(self.uiv_baldwin_frame)
                else:
                    self._hide(self.uiv_baldwin_frame)

            else:
                self._hide(self.sections["uiv"])
                self._hide(self.uiv_baldwin_frame)

            if sections.get("liv"):
                self._show(self.sections["liv"])
                self._hide(self.liv_lebel_s1_frame)
                self.preview_vars["liv"].set(f"LIV: {results.get('liv', '—')}")

                self.liv_reason.set(results.get("liv_rationale", ""))
                self._hide(self.liv_lebel_s1_frame)

                # Pick which LIV input subframe to show (Baldwin)
                lenke_type = results.get("lenke_type", "Unclassified")
                stf_eligible = results.get("stf_eligible", "No")  

                show_12 = False

                # Lenke 1/2 always use the STF-path style LIV inputs
                if lenke_type in ("Lenke 1", "Lenke 2"):
                    show_12 = True

                # Lenke 3 uses STF-path only when STF is eligible (and then patient preference matters)
                elif lenke_type == "Lenke 3" and stf_eligible == "Yes":
                    wants_stf = self.app.plan_data.get("radiographic_parameters", {}) \
                        .get("additional_standing_coronal", {}) \
                        .get("selective_thoracic_pref", "No")
                    show_12 = (wants_stf == "Yes")

                # Otherwise (Lenke 3 not STF-eligible, Lenke 4/5/6), use the non-STF LIV inputs
                else:
                    show_12 = False

                if show_12:
                    self.liv_36_frame.pack_forget()
                    self.liv_lebel_12_frame.pack_forget()
                    if not self.liv_baldwin_12_frame.winfo_ismapped():
                        self.liv_baldwin_12_frame.pack(fill="x")
                else:
                    self.liv_baldwin_12_frame.pack_forget()
                    self.liv_lebel_12_frame.pack_forget()
                    if not self.liv_36_frame.winfo_ismapped():
                        self.liv_36_frame.pack(fill="x")

            else:
                self._hide(self.sections["liv"])

            # Save for Page 5
            self.app.plan_data["level_selection"] = {
                "lenke_type": results.get("lenke_type"),
                "lumbar_modifier": results.get("lumbar_modifier"),
                "sagittal_modifier": results.get("sagittal_modifier"),
                "uiv": results.get("uiv"),
                "uiv_rationale": results.get("uiv_rationale"),
                "liv": results.get("liv"),
                "liv_rationale": results.get("liv_rationale"),
                "liv_warning": results.get("liv_warning"),
                "stf_eligible": results.get("stf_eligible"),
                "stf_reasons": results.get("stf_reasons"),
                "slf_eligible": results.get("slf_eligible"),
                "slf_reason": results.get("slf_reason"),
            }
            return

        variant_flag = self.app.plan_data.get("radiographic_parameters", {}) \
            .get("additional_standing_coronal", {}) \
            .get("variant_vertebral_anatomy", "No")

        if variant_flag == "Yes":
            if not self.variant_detail_lebel_frame.winfo_ismapped():
                self.variant_detail_lebel_frame.pack(fill="x")
        else:
            self.variant_detail_lebel_frame.pack_forget()

        inputs = self._flatten_inputs_for_lebel()
        results = compute_lebel_v3(inputs)
        lenke = results.get("lenke_type")
        lumbar = results.get("lumbar_modifier")

        warning_text = results.get("anatomy_warning", "").strip()
        if warning_text:
            self.preview_vars["anatomy_warning"].set(warning_text)
            self._show(self.sections["anatomy_warning"])
        else:
            self.preview_vars["anatomy_warning"].set("")
            self._hide(self.sections["anatomy_warning"])

        slf_gated = (lenke in ("Lenke 5", "Lenke 6")) and (lumbar == "C")
        stf_possible = (results.get("stf_possible") == "Yes")

        if stf_possible or slf_gated:
            self._show(self.sections["translations"])
        else:
            self._hide(self.sections["translations"])

        # Preview updates
        self.preview_vars["lenke_type"].set(results.get("lenke_type", "—"))
        self.preview_vars["lumbar_modifier"].set(results.get("lumbar_modifier", "—"))
        self.preview_vars["sagittal_modifier"].set(results.get("sagittal_modifier", "—"))

        # STF visibility
        if results.get("stf_possible") == "Yes":
            self._show(self.sections["stf"])
            self.preview_vars["stf_eligible"].set(
                f"STF eligible: {results.get('stf_eligible')}"
            )

            passed = results.get("stf_passed_count", 0)
            total = results.get("stf_total_count", 0)
            suggestion = results.get("stf_suggestion", "")
            note = results.get("stf_suggestion_note", "")

            summary = f"STF criteria met: {passed}/{total}"
            if suggestion:
                summary += f" | {suggestion}"
            if note:
                summary += f" | {note}"

            self.preview_vars["stf_summary"].set(summary)
            self._fill_text(self.stf_box, results.get("stf_reasons", []))
        else:
            self._hide(self.sections["stf"])
            self.preview_vars["stf_summary"].set("")

        # LIV visibility
        if results.get("lenke_type") not in ("Unclassified", None, ""):
            self._show(self.sections["liv"])
            self._show(self.liv_lebel_s1_frame)
            self.preview_vars["liv"].set(f"LIV: {results.get('liv', '—')}")
            liv_reason = results.get("liv_rationale", "")
            liv_warning = results.get("liv_warning", "")

            if liv_warning:
                self.liv_reason.set(f"{liv_reason}\n{liv_warning}")
            else:
                self.liv_reason.set(liv_reason)

            # LIV subframe selection
            lenke = results.get("lenke_type")
            if lenke in ("Lenke 1", "Lenke 2"):
                self.liv_36_frame.pack_forget()
                self.liv_baldwin_12_frame.pack_forget()
                if not self.liv_lebel_12_frame.winfo_ismapped():
                    self.liv_lebel_12_frame.pack(fill="x")
            else:
                self.liv_lebel_12_frame.pack_forget()
                self.liv_baldwin_12_frame.pack_forget()
                if not self.liv_36_frame.winfo_ismapped():
                    self.liv_36_frame.pack(fill="x")
        else:
            self._hide(self.sections["liv"])            
            self._hide(self.liv_lebel_s1_frame)

        # SLF visibility
        slf_gated = (
            results.get("lenke_type") == "Lenke 5"
            and results.get("lumbar_modifier") == "C"
        )

        slf_required_inputs = [
            "trunk_shift_direction",
            "shoulder_elevation",
            "t10_l2_kyphosis",
        ]

        slf_ready = slf_gated and self._all_present(inputs, slf_required_inputs)
        if slf_gated and slf_ready:
            self._show(self.sections["slf"])
            self.preview_vars["slf"].set(
                f"SLF eligible: {results.get('slf_eligible')}  |  {results.get('slf_reason')}"
            )
        else:
            self._hide(self.sections["slf"])

        # UIV visibility
        if results.get("lenke_type") not in ("Unclassified", None, ""):
            self._show(self.sections["uiv"])
            self._hide(self.uiv_baldwin_frame)
            self.preview_vars["uiv"].set(f"UIV: {results.get('uiv', '—')}")
            self.uiv_reason.set(results.get("uiv_rationale", ""))
        else:
            self._hide(self.sections["uiv"])
            self._hide(self.uiv_baldwin_frame)

        # Save latest results for Page 5 and export
        self.app.plan_data["level_selection"] = {
            "lenke_type": results.get("lenke_type"),
            "lumbar_modifier": results.get("lumbar_modifier"),
            "sagittal_modifier": results.get("sagittal_modifier"),
            "uiv": results.get("uiv"),
            "uiv_rationale": results.get("uiv_rationale"),
            "liv": results.get("liv"),
            "liv_rationale": results.get("liv_rationale"),
            "liv_warning": results.get("liv_warning"),
            "stf_eligible": results.get("stf_eligible"),
            "stf_reasons": results.get("stf_reasons"),
            "slf_eligible": results.get("slf_eligible"),
            "slf_reason": results.get("slf_reason"),
        }

   def _fill_text(self, box: tk.Text, content):
       box.config(state="normal")
       box.delete("1.0", "end")
       if isinstance(content, list):
           box.insert("1.0", "\n".join(content))
       else:
           box.insert("1.0", str(content or ""))
       box.config(state="disabled")
    
   def _sync_vars_from_plan_data(self):
       for (tab, key), var_list in self.vars.items():
           new_value = _rp_get(self.app, tab, key, "")
           for var in var_list:
               if var.get() != new_value:
                   var.set(new_value)

   def on_next(self):
       self.app.setup_page_5()
   
   def on_import_slicer_measurements(self):
       success, message = import_slicer_measurements_into_plan_data(self.app.plan_data)

       print("standing_coronal:", self.app.plan_data.get("radiographic_parameters", {}).get("standing_coronal", {}))
       print("standing_sagittal:", self.app.plan_data.get("radiographic_parameters", {}).get("standing_sagittal", {}))

       if success:
           self.app.is_dirty = True
           self._sync_vars_from_plan_data()
           self.refresh()
           print(message)
       else:
           print(message)
        
   def on_open_slicer_angle(self):
       slicer_path = self.app.plan_data.get("slicer_path", "").strip()

       possible_paths = []
       if slicer_path:
           possible_paths.append(slicer_path)

       possible_paths.extend([
           os.path.join(
               os.environ.get("ProgramFiles", r"C:\Program Files"),
               "4D Slicer v2.0",
               "Slicer.exe",
           ),
           os.path.join(
               os.environ.get("LOCALAPPDATA", ""),
               "slicer.org",
               "4D Slicer v2.0",
               "Slicer.exe",
           ),
       ])

       slicer_exe = next((p for p in possible_paths if p and os.path.exists(p)), None)

       if not slicer_exe:
           messagebox.showerror(
               "4D Slicer Not Found",
               "Could not find 4D Slicer.\n\nPlease install it or set the path first."
           )
           return

       try:
           env = os.environ.copy()
           env["FOURD_SLICER_MODE"] = "angle"

           subprocess.Popen([slicer_exe], env=env)

           self.app.plan_data["slicer_path"] = slicer_exe
           self.app.is_dirty = True

           messagebox.showinfo(
               "4D Slicer Opened",
               "4D Slicer was opened in angle mode.\n\n"
               "After taking measurements, come back and click 'Import Slicer Measurements'."
           )
       except Exception as e:
           messagebox.showerror("Launch Failed", str(e))