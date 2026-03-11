import json
from datetime import datetime
from tkinter import filedialog, messagebox

def _safe_str(x, default=""):
    if x is None:
        return default
    s = str(x).strip()
    return s if s else default

def _parse_date_to_ddmmyyyy(date_str: str) -> str:
    date_str = _safe_str(date_str, "")
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%d%m%Y")
        except Exception:
            pass
    return datetime.today().strftime("%d%m%Y")

def save_plan_json(plan_data):
    if not plan_data:
        messagebox.showwarning("Nothing to save", "No plan data to save.")
        return

    # --- FILE NAME ---
    patient = plan_data.get("patient", {}) or {}
    op_id = _safe_str(patient.get("id"), "UNKNOWN")
    surgery_date_raw = _safe_str(patient.get("surgery_date"), "")
    ddmmyyyy = _parse_date_to_ddmmyyyy(surgery_date_raw)

    default_name = f"{op_id} {ddmmyyyy} PLAN.json"
    # -----------------------

    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        initialfile=default_name, 
        filetypes=[("FlowControl Plan", "*.json")]
    )

    if not filepath:
        return

    try:
        with open(filepath, "w") as f:
            json.dump(plan_data, f, indent=2)
        messagebox.showinfo("Saved", "Plan saved successfully.")
    except Exception as e:
        messagebox.showerror("Save failed", f"Could not save plan:\n{e}")
