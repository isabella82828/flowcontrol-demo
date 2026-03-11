import json
import os
import re
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

from .page14_export import (
    _safe_str,
    _safe_float,
    _format_date_for_doc,
    _get_num_ribs,
    _get_num_lumbar,
    _get_levels_line,
    build_additional_equipment_line,
    build_positioning_line,
    _build_postop_pain_text,
    _build_anchors_rods_text
)

WHITE = "#FFFFFF"
FONT = ("Segoe UI", 12)

CONTACTS_FILE = "FlowControl_contacts.json"

ROLE_LABELS = [
    ("anaesthesiologist", "Anaesthesiologist"),
    ("perfusionist", "Perfusionist"),
    ("orthopaedic_technologist", "Orthopaedic Technologist"),
    ("scrub_nurse", "Scrub Nurse"),
    ("neurophysiologist", "Neurophysiologist"),
    ("supply_chain_manager", "Surgical Supply Chain Manager"),
    ("industry_spine_implants", "Industry Rep (Spine Implants)"),
    ("industry_navigation", "Industry Rep (Navigation)"),
]

ROLE_TO_SECTIONS = {
    # Anaesthesiologist
    "anaesthesiologist": [
        "patient_summary",
        "positioning_traction",
        "infection_reduction",
        "blood_conservation",
        "postop_pain",
    ],

    # Perfusionist
    "perfusionist": [
        "patient_summary",
        "blood_conservation",
    ],

    # Orthopaedic technologist
    "orthopaedic_technologist": [
        "patient_summary",
        "positioning_traction",
    ],

    # Scrub nurse
    "scrub_nurse": [
        "patient_summary",
        "anchors_rods",
        "additional_equipment",
        "infection_reduction",
        "blood_conservation",
        "positioning_traction",
    ],

    # Neurophysiologist (no curve correction for now)
    "neurophysiologist": [
        "patient_summary",
        "positioning_traction",
        "postop_pain",
    ],

    # Supply chain manager
    "supply_chain_manager": [
        "patient_summary",
        "anchors_rods",
        "additional_equipment",
    ],

    # Industry (spine implants)
    "industry_spine_implants": [
        "patient_summary",
        "anchors_rods",
    ],

    # Industry (navigation)
    "industry_navigation": [
        "patient_summary",
        "additional_equipment",
    ],
}

def _build_email_body_filtered(plan_data: dict, roles: list, section_ids: list) -> str:
    lines = ["Hello,", ""]
    lines.append("This is the OR team communication for the upcoming case.")
    lines.append(f"Role(s): {', '.join(roles)}")
    lines.append("")

    # add blocks
    for sid in section_ids:
        fn = SECTION_BUILDERS.get(sid)
        if not fn:
            continue
        block = (fn(plan_data) or "").strip()
        if block:
            lines.append(block)
            lines.append("")

    lines.append("Please see the exported FlowControl Word document for full details.")
    lines.append("")
    lines.append("Thank you,")
    lines.append("FlowControl Team")
    return "\n".join(lines)


def _default_contacts():
    return {k: {"name": "", "email": "", "enabled": True} for k, _ in ROLE_LABELS}

def _is_valid_email(email: str) -> bool:
    email = (email or "").strip()
    if not email:
        return False
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return _default_contacts()
    try:
        with open(CONTACTS_FILE, "r") as f:
            data = json.load(f)
        base = _default_contacts()
        for k in base.keys():
            if k in data and isinstance(data[k], dict):
                base[k].update(data[k])
        return base
    except Exception:
        return _default_contacts()

def save_contacts(contacts: dict):
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts, f, indent=2)

def _should_email_role(plan_data: dict, role_key: str) -> bool:
    blood = (plan_data or {}).get("blood_conservation", {}) or {}
    setup = (plan_data or {}).get("setup", {}) or {}
    eq = (plan_data or {}).get("additional_equipment", {}) or {}

    if role_key == "perfusionist":
        return bool(blood.get("cell_saver_on", False))
    if role_key == "orthopaedic_technologist":
        return bool(setup.get("traction_on", False))
    if role_key == "neurophysiologist":
        return bool(eq.get("neuro_on", False))
    if role_key == "industry_navigation":
        return bool(eq.get("nav7d_on", False))

    return True

def _build_email_subject(plan_data: dict) -> str:
    patient = (plan_data or {}).get("patient", {}) or {}
    pid = (patient.get("id") or "Patient").strip()
    date = (patient.get("surgery_date") or "").strip()
    return f"FlowControl OR Communication, {pid}, {date}".strip().strip(",")

def _open_mailto(to_email: str, subject: str, body: str):
    params = {"subject": subject, "body": body}
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url = f"mailto:{to_email}?{query}"

    try:
        if sys.platform == "darwin":
            # macOS
            subprocess.run(["open", url], check=True)
        elif sys.platform.startswith("win"):
            # Windows
            # Use the shell to dispatch default mail client
            subprocess.run(["cmd", "/c", "start", "", url], check=True)
        else:
            # Linux 
            subprocess.run(["xdg-open", url], check=True)
    except Exception:
        messagebox.showerror(
            "Email draft failed",
            "Could not open an email draft.\n\n"
            "Fix: set your default Email app to Outlook, then try again."
        )

class Page14TeamCommunication:
    def __init__(self, app):
        self.app = app
        self.vars = {}  # role_key -> dict of tk vars

    def setup(self):
        scrollable = self.app.create_standard_page(
            title_text="Team Communication",
            back_command=self.app.setup_page_14,
            next_command=None,
        )

        ttk.Label(
            scrollable,
            text="Contacts",
            font=("Segoe UI", 14, "bold"),
            background=WHITE,
        ).pack(anchor="w", pady=(6, 10))

        contacts = self.app.plan_data.get("contacts")
        if not isinstance(contacts, dict):
            contacts = load_contacts()
            self.app.plan_data["contacts"] = contacts

        grid = ttk.Frame(scrollable)
        grid.pack(fill="x", pady=(0, 12))

        ttk.Label(grid, text="Role", font=FONT, background=WHITE).grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(grid, text="Name", font=FONT, background=WHITE).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(grid, text="Email", font=FONT, background=WHITE).grid(row=0, column=2, sticky="w", padx=4)
        ttk.Label(grid, text="Enabled", font=FONT, background=WHITE).grid(row=0, column=3, sticky="w", padx=4)

        for i, (key, label) in enumerate(ROLE_LABELS, start=1):
            row = contacts.get(key, {})
            name_var = tk.StringVar(value=row.get("name", ""))
            email_var = tk.StringVar(value=row.get("email", ""))
            enabled_var = tk.BooleanVar(value=bool(row.get("enabled", True)))

            self.vars[key] = {"name": name_var, "email": email_var, "enabled": enabled_var}

            ttk.Label(grid, text=label, font=FONT, background=WHITE).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(grid, textvariable=name_var, width=22).grid(row=i, column=1, sticky="w", padx=4, pady=2)
            ttk.Entry(grid, textvariable=email_var, width=34).grid(row=i, column=2, sticky="w", padx=4, pady=2)
            ttk.Checkbutton(grid, variable=enabled_var).grid(row=i, column=3, sticky="w", padx=4, pady=2)

        btns = tk.Frame(scrollable, bg=WHITE)
        btns.pack(anchor="w", pady=(8, 0))

        # shorter rounded buttons
        self.app._rounded_button(
            btns,
            text="Save Contacts",
            command=self._on_save,
            width=180,
            height=44,
            radius=16,
        ).pack(side="left", padx=(0, 10))

        self.app._rounded_button(
            btns,
            text="Send Emails",
            command=self._on_send,
            width=180,
            height=44,
            radius=16,
        ).pack(side="left")

    def _on_save(self):
        contacts = {}
        for key, _ in ROLE_LABELS:
            contacts[key] = {
                "name": self.vars[key]["name"].get().strip(),
                "email": self.vars[key]["email"].get().strip(),
                "enabled": bool(self.vars[key]["enabled"].get()),
            }

        self.app.plan_data["contacts"] = contacts
        try:
            save_contacts(contacts)
            messagebox.showinfo("Saved", "Contacts saved.")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _on_send(self):
        contacts = self.app.plan_data.get("contacts", {}) or {}
        subject = _build_email_subject(self.app.plan_data)

        # Build recipient groups by email (de-dupe)
        email_to_roles = {}
        for role_key, role_label in ROLE_LABELS:
            row = contacts.get(role_key, {}) or {}
            if not bool(row.get("enabled", True)):
                continue
            if not _should_email_role(self.app.plan_data, role_key):
                continue

            email = (row.get("email") or "").strip()
            if not email:
                continue

            email_norm = email.lower()
            email_to_roles.setdefault(email_norm, {"email": email, "roles": [], "role_keys": []})
            email_to_roles[email_norm]["roles"].append(role_label)
            email_to_roles[email_norm]["role_keys"].append(role_key)

        if not email_to_roles:
            messagebox.showwarning("No recipients", "No eligible recipients with emails found.")
            return

        missing = []
        for role_key, role_label in ROLE_LABELS:
            if not _should_email_role(self.app.plan_data, role_key):
                continue
            row = contacts.get(role_key, {}) or {}
            if not bool(row.get("enabled", True)):
                continue
            email = (row.get("email") or "").strip()
            if not email:
                missing.append(role_label)
            elif not _is_valid_email(email):
                missing.append(role_label + " (invalid email)")

        if missing:
            messagebox.showwarning(
                "Some contacts missing",
                "Some eligible contacts are missing emails or have invalid emails:\n" + "\n".join(missing)
            )

        # Open filtered drafts
        for payload in email_to_roles.values():
            seen = set()
            section_ids = []
            for rk in payload.get("role_keys", []):
                for sid in ROLE_TO_SECTIONS.get(rk, ["patient_summary"]):
                    if sid not in seen:
                        seen.add(sid)
                        section_ids.append(sid)

            body = _build_email_body_filtered(self.app.plan_data, payload["roles"], section_ids)
            _open_mailto(payload["email"], subject, body)

def _build_patient_summary_text(plan_data: dict) -> str:
    patient = (plan_data or {}).get("patient", {}) or {}

    patient_id = _safe_str(patient.get("id"), "UNKNOWN")
    age_years = _safe_str(patient.get("age_years"), "—")
    sex = _safe_str(patient.get("sex"), "—")
    months_post_menarchal = _safe_str(patient.get("months_post_menarchal"), "—")

    date_line = _format_date_for_doc(_safe_str(patient.get("surgery_date"), ""))
    dx = _safe_str(patient.get("diagnosis"), "—")

    ribs = _get_num_ribs(plan_data)
    lumbar = _get_num_lumbar(plan_data)
    lld = _safe_str(plan_data.get("anatomy.lld"), "—")

    weight_kg = patient.get("weight_kg")
    weight_line = f"{weight_kg} kg" if weight_kg not in (None, "", "—") else "—"

    levels_line = _get_levels_line(plan_data)
    aim = _safe_str(patient.get("aim"), "—")

    lines = [
        f"OP {patient_id}",
        f"{age_years} yo {sex}, {months_post_menarchal} months post menarchal.",
        f"{date_line}",
        f"Dx: {dx}",
        f"Anatomy: {ribs} ribs, {lumbar} lumbar vertebra, {lld}",
        f"Weight: {weight_line}",
        f"Levels: {levels_line}",
        f"Aim: {aim}",
    ]
    return "\n".join(lines)

def _build_additional_equipment_text(plan_data: dict) -> str:
    return f"Additional equipment: {build_additional_equipment_line(plan_data)}"

def _build_positioning_text(plan_data: dict) -> str:
    return f"Positioning: {build_positioning_line(plan_data)}"

def _build_infection_reduction_text(plan_data: dict) -> str:
    inf = (plan_data or {}).get("infection_reduction", {}) or {}
    parts = []

    if inf.get("pre_incision_abx", False):
        parts.append("Ancef prior to incision with re-dose during procedure")
    if inf.get("povidone_paint_implants", False):
        parts.append("Betadine painting of implants prior to final closure when we ask for final x-rays")

    vanc_wound = inf.get("vanc_wound_500mg", False)
    vanc_allo = inf.get("vanc_allograft_500mg", False)
    if vanc_wound and vanc_allo:
        parts.append("1g Vancomycin powder [500mg combined with allograft and 500mg for wound closure]")
    elif vanc_allo:
        parts.append("Vancomycin powder 500mg combined with allograft")
    elif vanc_wound:
        parts.append("Vancomycin powder 500mg for wound closure")

    if not parts:
        return "Infection reduction strategies: —"

    return "Infection reduction strategies:\n- " + "\n- ".join(parts)

def _build_blood_conservation_text(plan_data: dict) -> str:
    blood = (plan_data or {}).get("blood_conservation", {}) or {}
    lines = []

    if bool(blood.get("infiltration_on", False)):
        w = _safe_float(blood.get("infiltration_weight_kg"), default=None)
        if w is None:
            w = _safe_float((plan_data or {}).get("patient", {}).get("weight_kg"), default=None)
        if w is not None:
            lines.append(f"Infiltration cocktail planned ({w:.1f} kg)")

    if bool(blood.get("txa_on", True)):
        lines.append("Tranexamic Acid")
    if bool(blood.get("cell_saver_on", True)):
        lines.append("CellSaver")
    if bool(blood.get("floseal_on", True)):
        lines.append("Floseal")

    return "Blood conservation strategies:\n- " + "\n- ".join(lines) if lines else "Blood conservation strategies: —"

SECTION_BUILDERS = {
    "patient_summary": _build_patient_summary_text,
    "additional_equipment": _build_additional_equipment_text,
    "positioning_traction": _build_positioning_text,
    "infection_reduction": _build_infection_reduction_text,
    "blood_conservation": _build_blood_conservation_text,
    "anchors_rods": _build_anchors_rods_text,
    "postop_pain": _build_postop_pain_text,
}
