import os
import json
import shutil

SHARED_FOLDER = r"C:\ProgramData\flowcontrol\exchange"

def ensure_shared_folder():
    os.makedirs(SHARED_FOLDER, exist_ok=True)

def write_plan(data: dict, subfolder: str = None):
    ensure_shared_folder()
    if subfolder:
        folder = os.path.join(SHARED_FOLDER, "dicom", subfolder)
        os.makedirs(folder, exist_ok=True)
    else:
        folder = SHARED_FOLDER
    tmp   = os.path.join(folder, "plan_data.json.tmp")
    final = os.path.join(folder, "plan_data.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, final)

def read_slicer_output() -> dict:
    path = os.path.join(SHARED_FOLDER, "slicer_output.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_slicer_output():
    path = os.path.join(SHARED_FOLDER, "slicer_output.json")
    if os.path.exists(path):
        os.remove(path)

def copy_dicom_folder(src_folder: str, name: str, patient_folder: str = "unknown_patient") -> str:
    ensure_shared_folder()
    dest = os.path.join(SHARED_FOLDER, "dicom", patient_folder, name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src_folder, dest)
    return dest