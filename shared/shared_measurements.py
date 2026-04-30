import os
import csv

SHARED_FOLDER = r"C:\ProgramData\FlowControl\exchange"


def get_latest_patient_folder(shared_root: str = SHARED_FOLDER) -> str | None:
    print("SHARED ROOT:", shared_root)

    dicom_root = os.path.join(shared_root, "dicom")
    print("DICOM ROOT:", dicom_root)

    if not os.path.exists(dicom_root):
        return None

    folders = [f for f in os.scandir(dicom_root) if f.is_dir()]
    if not folders:
        return None

    latest = max(folders, key=lambda f: f.stat().st_mtime).path
    print("Selected latest patient folder:", latest)
    return latest
    return max(folders, key=lambda f: f.stat().st_mtime).path


# def get_measurements_csv_path(shared_root: str = SHARED_FOLDER) -> str | None:
#     patient_folder = get_latest_patient_folder(shared_root)
#     if not patient_folder:
#         return None

#     csv_path = os.path.join(patient_folder, "measurements.csv")
#     if not os.path.exists(csv_path):
#         return None

#     return csv_path

def get_measurements_csv_path(shared_root: str = SHARED_FOLDER, patient_folder_name: str = None) -> str | None:
    if patient_folder_name:
        patient_folder = os.path.join(shared_root, "dicom", patient_folder_name)
    else:
        patient_folder = get_latest_patient_folder(shared_root)

    if not patient_folder or not os.path.exists(patient_folder):
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


    mapping = {
        # Standing coronal
        "PT Cobb": ("standing_coronal", "pt_cobb"),
        "MT Cobb": ("standing_coronal", "mt_cobb"),
        "TL/L Cobb": ("standing_coronal", "tl_l_cobb"),
        "T1 Tilt": ("standing_coronal", "t1_tilt"),
        "CSVL at TL/L Apex Position": ("standing_coronal", "csvl_tll_apex_position"),
        "Risser Score": ("standing_coronal", "risser_score"),

        # Standing sagittal
        "T2-T5 Kyphosis": ("standing_sagittal", "t2_5_kyphosis"),
        "T5-T12 Kyphosis": ("standing_sagittal", "t5_12_kyphosis"),
        "T10-L2 Kyphosis": ("standing_sagittal", "t10_l2_kyphosis"),
        "PT Apex Level": ("standing_sagittal", "pt_apex_level"),

        # Bending
        "PT Cobb Bending": ("bending", "pt_cobb"),
        "MT Cobb Bending": ("bending", "mt_cobb"),
        "TL/L Cobb Bending": ("bending", "tl_l_cobb"),

        # LIV / sagittal checks
        "S1 plumb line relation at L3": ("additional_standing_sagittal", "s1_plumb_line_l3_relation"),
        "S1 plumb line relation at L4": ("additional_standing_sagittal", "s1_plumb_line_l4_relation"),
        "S1 plumb line relation at L5": ("additional_standing_sagittal", "s1_plumb_line_l5_relation"),
        "Lumbar apex level": ("standing_sagittal", "lumbar_apex_level"),
        "Bending L3-L4 Disc Angle": ("additional_bending", "bending_l3_4_disc_angle"),
        "NV Grade": ("additional_standing_coronal", "nv_grade"),

        # Apical translations
        "MT apical translation": ("standing_coronal", "mt_apical_translation_mm"),
        "TL/L Apical Translation": ("standing_coronal", "tll_apical_translation_mm"),
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

        section_dict = rp.setdefault(section, {})

        if section_dict.get(field) != value:
            section_dict[field] = value
            updated = True

    return updated

def import_slicer_measurements_into_plan_data(
    plan_data: dict,
    shared_root: str = SHARED_FOLDER,
    patient_folder_name: str = None
) -> tuple[bool, str]:

    csv_path = get_measurements_csv_path(shared_root, patient_folder_name)
    if not csv_path:
        return False, "No measurements.csv file found in the patient folder."

    measurements = read_measurements_csv(csv_path)
    if not measurements:
        return False, f"No summary measurements found in CSV: {csv_path}"

    updated = apply_measurements_to_plan_data(plan_data, measurements)

    if not updated:
        return True, f"CSV read, but no values changed: {csv_path}"

    return True, f"Imported Slicer measurements from:\n{csv_path}"

def get_screw_info_csv_path(shared_root: str = SHARED_FOLDER, patient_folder_name: str = None) -> str | None:
    print("Looking for screw info file...")

    if patient_folder_name:
        patient_folder = os.path.join(shared_root, "dicom", patient_folder_name)
    else:
        patient_folder = get_latest_patient_folder(shared_root)

    print("Patient folder used:", patient_folder)

    if not patient_folder or not os.path.exists(patient_folder):
        return None

    # --- 1. CHECK ROOT FIRST ---
    files = os.listdir(patient_folder)
    root_candidates = [f for f in files if f.endswith("_Screw_Info.csv")]

    if root_candidates:
        root_candidates.sort(
            key=lambda f: os.path.getmtime(os.path.join(patient_folder, f)),
            reverse=True
        )
        csv_path = os.path.join(patient_folder, root_candidates[0])
        print("Using screw info file (root):", csv_path)
        return csv_path

    # --- 2. FALLBACK TO /screws/ ---
    screws_folder = os.path.join(patient_folder, "screws")
    print("Checking screws folder:", screws_folder)

    if not os.path.exists(screws_folder):
        return None

    files = os.listdir(screws_folder)
    candidates = [f for f in files if f.endswith("_Screw_Info.csv")]

    if not candidates:
        return None

    candidates.sort(
        key=lambda f: os.path.getmtime(os.path.join(screws_folder, f)),
        reverse=True
    )

    csv_path = os.path.join(screws_folder, candidates[0])
    print("Using screw info file (screws folder):", csv_path)
    return csv_path

def import_screw_info_into_plan_data(
    plan_data: dict,
    shared_root: str = SHARED_FOLDER,
    patient_folder_name: str = None
) -> tuple[bool, str]:
    csv_path = get_screw_info_csv_path(shared_root, patient_folder_name)

    if not csv_path:
        return False, "No _Screw_Info.csv file found in the patient's screws folder."

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        return False, f"Failed to read screw_info.csv: {e}"

    if not rows:
        return False, f"Failed to read screw info CSV: {e}"

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