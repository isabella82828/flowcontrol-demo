def _get(plan_data: dict, key: str, default=""):
    if not plan_data:
        return default
    return plan_data.get(key, default)

def _is_missing(val) -> bool:
    return val is None or (isinstance(val, str) and val.strip() == "")

def _is_lenke_type1(plan_data: dict) -> bool:
    cls = str(_get(plan_data, "lenke.classification", "")).strip()
    if cls.startswith("1"):
        return True
    return bool(_get(plan_data, "lenke.is_type1", False))


# Required fields by tab
REQUIRED_FIELDS = {
    "Standing Coronal": [
        ("standing.pt_cobb", "Proximal Thoracic Cobb Angle", None),
        ("standing.mt_cobb", "Main Thoracic Cobb Angle", None),
        ("standing.tl_l_cobb", "Thoracolumbar/Lumbar Cobb Angle", None),
    ],
    "Standing Sagittal": [
        ("standing.t2_5_kyphosis", "T1/T2–T5 Kyphosis (Proximal Thoracic Kyphosis)", None),
        ("standing.t5_12_kyphosis", "T5–T12 Kyphosis (Thoracic Kyphosis)", None),
        ("standing.t10_l2_kyphosis", "T10–L2 Kyphosis (Thoracolumbar Kyphosis)", None),
    ],
    "Supine Coronal": [
        ("supine.last_touched_vertebra", "Supine Last Touched Vertebra (SLTV)", None),
    ],
    "Additional Standing Coronal": [
        # Only required if Lenke type 1
        ("lenke.l4_slope_direction", "L4 Tilt Direction", _is_lenke_type1),
    ],
    "Bending": [
        ("bending.pt_cobb", "Bending Proximal Thoracic Cobb Angle", None),
        ("bending.mt_cobb", "Bending Main Thoracic Cobb Angle", None),
        ("bending.tl_l_cobb", "Bending Thoracolumbar/Lumbar Cobb Angle", None),
    ],
}

def validate_required_fields(plan_data: dict):
    missing_by_tab = {}
    ok = True

    for tab_title, fields in REQUIRED_FIELDS.items():
        missing_labels = []

        for key, label, cond_fn in fields:
            if cond_fn is not None and not cond_fn(plan_data):
                continue

            val = _get(plan_data, key, "")
            if _is_missing(val):
                missing_labels.append(label)

        if missing_labels:
            ok = False
            missing_by_tab[tab_title] = missing_labels

    return ok, missing_by_tab
