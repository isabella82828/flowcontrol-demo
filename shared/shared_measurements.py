import os
import csv

SHARED_FOLDER = r"C:\ProgramData\FlowControl\exchange"


def get_latest_patient_folder(shared_root: str = SHARED_FOLDER) -> str | None:
    dicom_root = os.path.join(shared_root, "dicom")
    if not os.path.exists(dicom_root):
        return None

    folders = [f for f in os.scandir(dicom_root) if f.is_dir()]
    if not folders:
        return None

    return max(folders, key=lambda f: f.stat().st_mtime).path


def get_measurements_csv_path(shared_root: str = SHARED_FOLDER) -> str | None:
    patient_folder = get_latest_patient_folder(shared_root)
    if not patient_folder:
        return None

    csv_path = os.path.join(patient_folder, "measurements.csv")
    if not os.path.exists(csv_path):
        return None

    return csv_path

def read_measurements_csv(csv_path: str) -> dict:
    if not csv_path or not os.path.exists(csv_path):
        return {}

    measurements = {}
    in_summary_section = False

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue

            first_cell = row[0].strip() if len(row) > 0 else ""

            if first_cell == "Summary Measurements":
                in_summary_section = True
                continue

            if not in_summary_section:
                continue

            if first_cell == "Measurement":
                continue

            if len(row) < 2:
                continue

            key = row[0].strip()
            value = row[1].strip()
            measurements[key] = value
    
    print("Parsed measurements from CSV:", measurements)
    return measurements

def apply_measurements_to_plan_data(plan_data: dict, measurements: dict) -> bool:
    if not isinstance(plan_data, dict) or not measurements:
        return False

    rp = plan_data.setdefault("radiographic_parameters", {})
    standing_coronal = rp.setdefault("standing_coronal", {})
    standing_sagittal = rp.setdefault("standing_sagittal", {})

    mapping = {
        "PT Cobb": ("standing_coronal", "pt_cobb"),
        "MT Cobb": ("standing_coronal", "mt_cobb"),
        "TL/L Cobb": ("standing_coronal", "tl_l_cobb"),
        "T2-T5 Kyphosis": ("standing_sagittal", "t2_5_kyphosis"),
        "T5-T12 Kyphosis": ("standing_sagittal", "t5_12_kyphosis"),
        "T10-L2 Kyphosis": ("standing_sagittal", "t10_l2_kyphosis"),
    }

    updated = False

    for csv_name, (section, field) in mapping.items():
        raw_value = measurements.get(csv_name, "")
        if raw_value == "":
            continue

        try:
            value = f"{float(raw_value):.2f}"
        except Exception:
            value = raw_value

        if section == "standing_coronal":
            if standing_coronal.get(field) != value:
                standing_coronal[field] = value
                updated = True
        elif section == "standing_sagittal":
            if standing_sagittal.get(field) != value:
                standing_sagittal[field] = value
                updated = True

    return updated

def import_slicer_measurements_into_plan_data(plan_data: dict, shared_root: str = SHARED_FOLDER) -> tuple[bool, str]:
    csv_path = get_measurements_csv_path(shared_root)
    if not csv_path:
        return False, "No measurements.csv file found in the shared patient folder."

    measurements = read_measurements_csv(csv_path)
    if not measurements:
        return False, f"No summary measurements found in CSV: {csv_path}"

    updated = apply_measurements_to_plan_data(plan_data, measurements)
    if not updated:
        return True, f"CSV read successfully, but no values were changed: {csv_path}"

    return True, f"Imported Slicer measurements from:\n{csv_path}"

def get_screw_info_csv_path(shared_root: str = SHARED_FOLDER) -> str | None:
    patient_folder = get_latest_patient_folder(shared_root)
    if not patient_folder:
        return None

    csv_path = os.path.join(patient_folder, "screw_info.csv")
    if not os.path.exists(csv_path):
        return None

    return csv_path


def import_screw_info_into_plan_data(plan_data: dict, shared_root: str = SHARED_FOLDER) -> tuple[bool, str]:
    csv_path = get_screw_info_csv_path(shared_root)
    if not csv_path:
        return False, "No screw_info.csv found in the shared patient folder."

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        return False, f"Failed to read screw_info.csv: {e}"

    if not rows:
        return False, f"screw_info.csv is empty: {csv_path}"

    ap = plan_data.setdefault("anchor_planning", {})

    levels_seen = []
    anchors = {}

    for row in rows:
        level   = (row.get("Level")        or "").strip()
        side    = (row.get("Side")         or "").strip().lower()   # "left" / "right"
        cat     = (row.get("Category")     or "").strip()           # "Screw", "Hook", "Tape"
        typ     = (row.get("Type")         or "").strip()
        dia     = (row.get("Diameter (mm)") or "").strip()
        length  = (row.get("Length (mm)")  or "").strip()
        notes   = (row.get("Notes")        or "").strip()

        if not level or side not in ("left", "right"):
            continue

        if level not in levels_seen:
            levels_seen.append(level)

        anchors.setdefault(level, {})
        anchors[level].setdefault("left",  {"anchor_type": "None", "notes": ""})
        anchors[level].setdefault("right", {"anchor_type": "None", "notes": ""})

        # First row wins for each level+side (duplicates are unexpected)
        if anchors[level][side].get("anchor_type", "None") != "None":
            continue

        if cat == "Screw":
            anchors[level][side] = {
                "anchor_type": "Screw",
                "screw_type":   typ,
                "diameter_mm":  dia,
                "length_mm":    length,
                "tap":          False,
                "notes":        notes,
            }
        elif cat == "Hook":
            anchors[level][side] = {
                "anchor_type": "Hook",
                "hook_type":   typ,
                "notes":       notes,
            }
        elif cat == "Tape":
            anchors[level][side] = {
                "anchor_type": "Tape",
                "tape_type":   typ,
                "notes":       notes,
            }
        else:
            anchors[level][side] = {
                "anchor_type": "None",
                "notes":       notes,
            }

    if not levels_seen:
        return False, "screw_info.csv had no usable rows (check Level/Side columns)."

    # Replace everything
    ap["levels"]  = levels_seen
    ap["anchors"] = anchors

    return True, f"Imported screw selections from:\n{csv_path}"