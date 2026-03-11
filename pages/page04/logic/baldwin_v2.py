from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Normalization + parsing
# -----------------------------
def _s(x: Any) -> str:
    return "" if x is None else str(x).strip()

def to_float(x: Any) -> Optional[float]:
    s = _s(x)
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None

def to_int(x: Any) -> Optional[int]:
    s = _s(x)
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def norm_yes_no(x: Any) -> str:
    s = _s(x).lower()
    if s in ("yes", "y", "true", "1"):
        return "Yes"
    if s in ("no", "n", "false", "0"):
        return "No"
    return _s(x)

def norm_side(x: Any) -> str:
    s = _s(x).lower()
    if s in ("left", "l"):
        return "Left"
    if s in ("right", "r"):
        return "Right"
    if s in ("neither", "none", "level", "0", ""):
        return "Neither"
    return _s(x)

def norm_csvl_pos(x: Any) -> str:
    # Baldwin uses Centered / Shifted / Lateral
    s = _s(x).lower()
    if "center" in s:
        return "Centered"
    if "shift" in s:
        return "Shifted"
    if "lateral" in s:
        return "Lateral"
    return _s(x)

_VERTEBRA_ORDER = {f"T{i}": i for i in range(1, 13)}
_VERTEBRA_ORDER.update({f"L{i}": 100 + i for i in range(1, 6)})

def v_rank(v: Any) -> Optional[int]:
    s = _s(v).upper()
    if not s:
        return None
    return _VERTEBRA_ORDER.get(s)

def v_le(a: Any, b: Any) -> Optional[bool]:
    ra, rb = v_rank(a), v_rank(b)
    if ra is None or rb is None:
        return None
    return ra <= rb

def safe_ratio(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den == 0:
        return None
    return num / den


# -----------------------------
# UI field identifiers
# -----------------------------
FieldRef = Tuple[str, str]  # (tab, key)

F_STAND_MT: FieldRef = ("standing_coronal", "mt_cobb")
F_STAND_TLL: FieldRef = ("standing_coronal", "tl_l_cobb")
F_BEND_PT: FieldRef = ("bending", "pt_cobb")
F_BEND_MT: FieldRef = ("bending", "mt_cobb")
F_BEND_TLL: FieldRef = ("bending", "tl_l_cobb")
F_T2_5: FieldRef = ("standing_sagittal", "t2_5_kyphosis")
F_T5_12: FieldRef = ("standing_sagittal", "t5_12_kyphosis")
F_T10_L2: FieldRef = ("standing_sagittal", "t10_l2_kyphosis")
F_CSVL_POS: FieldRef = ("standing_coronal", "csvl_tll_apex_position")

# UIV extras
F_SHOULDER: FieldRef = ("standing_coronal", "shoulder_elevation")
F_UEV_TLL: FieldRef = ("additional_standing_coronal", "tll_uev")

# STF extras
F_MT_TRANS: FieldRef = ("standing_coronal", "mt_apical_translation_mm")
F_TLL_TRANS: FieldRef = ("standing_coronal", "tll_apical_translation_mm")
F_MT_NASH: FieldRef = ("standing_coronal", "mt_nashmoe_grade")
F_TLL_NASH: FieldRef = ("standing_coronal", "tll_nashmoe_grade")
F_TRUNK_SHIFT: FieldRef = ("standing_coronal", "trunk_shift")
F_LORD_DISC: FieldRef = ("additional_standing_sagittal", "lordotic_disc_below_mt_ltv")

# LIV extras
F_MT_LTV: FieldRef = ("additional_standing_coronal", "mt_ltv")
F_STABLE_V: FieldRef = ("additional_standing_coronal", "stable_vertebra")
F_WANTS_STF: FieldRef = ("additional_standing_coronal", "selective_thoracic_pref")

F_LUMBAR_APEX: FieldRef = ("standing_sagittal", "lumbar_apex_level")
F_BEND_L3_4: FieldRef = ("additional_bending", "bending_l3_4_disc_angle")
F_NV_GRADE: FieldRef = ("additional_standing_coronal", "nv_grade")

# SLF extras (these are not currently in your UI, you will add fields)
F_THOR_FLEX: FieldRef = ("additional_bending", "thoracic_flexibility_pct")
F_COBB_RATIO: FieldRef = ("additional_standing_coronal", "tll_thoracic_cobb_ratio")
F_TRANS_RATIO: FieldRef = ("additional_standing_coronal", "tll_thoracic_translation_ratio")


# -----------------------------
# Result containers
# -----------------------------
@dataclass
class StageResult:
    ok: bool
    missing: List[FieldRef]
    data: Dict[str, Any]

def _missing_fields(present: Dict[FieldRef, Any], needed: List[FieldRef]) -> List[FieldRef]:
    miss = []
    for f in needed:
        v = present.get(f)
        if v is None or str(v).strip() == "":
            miss.append(f)
    return miss


# -----------------------------
# Stage 1: Lenke + modifiers
# -----------------------------
def compute_lenke_stage(p: Dict[FieldRef, Any]) -> StageResult:
    needed = [
        F_STAND_MT, F_STAND_TLL,
        F_BEND_PT, F_BEND_MT, F_BEND_TLL,
        F_T2_5, F_T10_L2, F_T5_12,
        F_CSVL_POS,
    ]
    missing = _missing_fields(p, needed)
    if missing:
        return StageResult(ok=False, missing=missing, data={})

    stand_mt = to_float(p[F_STAND_MT])
    stand_tll = to_float(p[F_STAND_TLL])
    bend_pt = to_float(p[F_BEND_PT])
    bend_mt = to_float(p[F_BEND_MT])
    bend_tll = to_float(p[F_BEND_TLL])
    t2_5 = to_float(p[F_T2_5])
    t10_l2 = to_float(p[F_T10_L2])
    t5_12 = to_float(p[F_T5_12])
    csvl_pos = norm_csvl_pos(p[F_CSVL_POS])

    # Structural flags
    structural_pt = "Yes" if ((bend_pt is not None and bend_pt > 25) or (t2_5 is not None and t2_5 > 20)) else "No"
    structural_mt = "Yes" if (bend_mt is not None and bend_mt > 25) else "No"
    structural_tll = "Yes" if ((bend_tll is not None and bend_tll > 25) or (t10_l2 is not None and t10_l2 > 20)) else "No"

    # Rare fallback:
    if (
            structural_pt == "No"
            and structural_mt == "No"
            and structural_tll == "No"
            and stand_mt is not None
            and stand_tll is not None
            and stand_mt < 25
            and stand_tll < 25
        ):
            if stand_mt >= stand_tll:
                structural_mt = "Yes"
            else:
                structural_tll = "Yes"
                
    # Lenke type
    lenke_type = "Check"
    if structural_pt == "No" and structural_mt == "Yes" and structural_tll == "No":
        lenke_type = "Lenke 1"
    elif structural_pt == "Yes" and structural_mt == "Yes" and structural_tll == "No":
        lenke_type = "Lenke 2"
    elif structural_pt == "No" and structural_mt == "Yes" and structural_tll == "Yes":
        if stand_mt is not None and stand_tll is not None and stand_mt < stand_tll:
            lenke_type = "Lenke 6"
        else:
            lenke_type = "Lenke 3"
    elif structural_pt == "Yes" and structural_mt == "Yes" and structural_tll == "Yes":
        lenke_type = "Lenke 4"
    elif structural_pt == "No" and structural_mt == "No" and structural_tll == "Yes":
        lenke_type = "Lenke 5"

    # Lumbar modifier
    lumbar_modifier = "Check"
    if csvl_pos == "Centered":
        lumbar_modifier = "A"
    elif csvl_pos == "Shifted":
        lumbar_modifier = "B"
    elif csvl_pos == "Lateral":
        lumbar_modifier = "C"

    # Sagittal modifier (T5-12)
    if t5_12 is None:
        sagittal_modifier = "—"
    else:
        if t5_12 < 10:
            sagittal_modifier = "–"
        elif t5_12 <= 40:
            sagittal_modifier = "N"
        else:
            sagittal_modifier = "+"

    if lenke_type == "Check" or lumbar_modifier == "Check":
        return StageResult(
            ok=True,
            missing=[],
            data={
                "lenke_type": "Unclassified",
                "lumbar_modifier": "—",
                "sagittal_modifier": sagittal_modifier,
                "structural_pt": structural_pt,
                "structural_mt": structural_mt,
                "structural_tll": structural_tll,
            },
        )

    return StageResult(
        ok=True,
        missing=[],
        data={
            "lenke_type": lenke_type,
            "lumbar_modifier": lumbar_modifier,
            "sagittal_modifier": sagittal_modifier,
            "structural_pt": structural_pt,
            "structural_mt": structural_mt,
            "structural_tll": structural_tll,
        },
    )

# -----------------------------
# Stage 2: UIV
# -----------------------------
def compute_uiv_stage(p: Dict[FieldRef, Any], lenke_type: str) -> StageResult:
    # Always need shoulder for non-Lenke5
    needed: List[FieldRef] = [F_SHOULDER]

    missing = _missing_fields(p, needed)
    if missing:
        return StageResult(ok=False, missing=missing, data={})

    shoulder = norm_side(p[F_SHOULDER])
    t10_l2 = to_float(p.get(F_T10_L2))

    uiv = "—"
    rationale = ""

    if lenke_type in ("Lenke 1", "Lenke 3", "Lenke 6"):
        uiv = "T3" if shoulder == "Left" else "T4"
        rationale = "Left shoulder elevation → T3" if shoulder == "Left" else "Right/level shoulder elevation → T4"
        return StageResult(ok=True, missing=[], data={"uiv": uiv, "uiv_rationale": rationale})

    if lenke_type in ("Lenke 2", "Lenke 4"):
        uiv = "T2" if shoulder == "Left" else "T3"
        rationale = "Left shoulder elevation → T2" if shoulder == "Left" else "Right/level shoulder elevation → T3"
        return StageResult(ok=True, missing=[], data={"uiv": uiv, "uiv_rationale": rationale})

    if lenke_type == "Lenke 5":
        if t10_l2 is not None and t10_l2 > 20:
            return StageResult(ok=True, missing=[], data={"uiv": "T4", "uiv_rationale": "T10–L2 kyphosis > 20° → T4"})
        # else need UEV
        missing2 = _missing_fields(p, [F_UEV_TLL])
        if missing2:
            return StageResult(ok=False, missing=missing2, data={})
        uev = _s(p[F_UEV_TLL]).upper()
        if not uev:
            return StageResult(ok=False, missing=[F_UEV_TLL], data={})
        return StageResult(ok=True, missing=[], data={"uiv": uev, "uiv_rationale": f"Low kyphosis → UEV ({uev})"})

    return StageResult(ok=True, missing=[], data={"uiv": "—", "uiv_rationale": ""})

# -----------------------------
# Stage 3: STF eligibility (Baldwin Lumbar C rule)
# -----------------------------
def compute_stf_stage(p: Dict[FieldRef, Any], lenke_type: str, lumbar_modifier: str) -> StageResult:
    if not (lenke_type in ("Lenke 1", "Lenke 2", "Lenke 3") and lumbar_modifier == "C"):
        return StageResult(
            ok=True,
            missing=[],
            data={
                "stf_eligible": "No",
                "stf_reasons": ["Not evaluated: STF (this rule) applies to Lenke 1–3 with Lumbar modifier C."],
            },
        )

    needed = [F_MT_TRANS, F_TLL_TRANS, F_MT_NASH, F_TLL_NASH, F_TRUNK_SHIFT, F_LORD_DISC]
    missing = _missing_fields(p, needed)
    if missing:
        return StageResult(ok=False, missing=missing, data={})

    stand_mt = to_float(p.get(F_STAND_MT))
    stand_tll = to_float(p.get(F_STAND_TLL))
    bend_tll = to_float(p.get(F_BEND_TLL))
    t10_l2 = to_float(p.get(F_T10_L2))

    mt_trans = to_float(p.get(F_MT_TRANS))
    tll_trans = to_float(p.get(F_TLL_TRANS))
    mt_nm = to_float(p.get(F_MT_NASH))
    tll_nm = to_float(p.get(F_TLL_NASH))

    trunk_shift = norm_side(p.get(F_TRUNK_SHIFT))
    lord_disc = norm_yes_no(p.get(F_LORD_DISC))

    mt_minus_tll = None
    if stand_mt is not None and stand_tll is not None:
        mt_minus_tll = stand_mt - stand_tll

    atr = safe_ratio(mt_trans, tll_trans)
    avrr = safe_ratio(mt_nm, tll_nm)

    checks: List[Tuple[bool, str]] = []
    checks.append((bend_tll is not None and bend_tll < 25, "Bending TL/L Cobb < 25°"))
    checks.append((mt_minus_tll is not None and mt_minus_tll > 10, "MT − TL/L Cobb > 10°"))
    checks.append((atr is not None and atr > 1.2, "ATR > 1.2"))
    checks.append((avrr is not None and avrr > 1.2, "AVRR > 1.2"))
    checks.append((t10_l2 is not None and t10_l2 < 10, "T10–L2 kyphosis < 10°"))
    checks.append((stand_tll is not None and stand_tll < 50, "Standing TL/L Cobb < 50°"))
    checks.append((trunk_shift == "Right", "Trunk shift = Right"))
    checks.append((lord_disc == "Yes", "Lordotic disc below MT-LTV = Yes"))

    failed = [msg for ok, msg in checks if not ok]
    if not failed:
        return StageResult(ok=True, missing=[], data={"stf_eligible": "Yes", "stf_reasons": ["All Baldwin STF criteria met."]})

    return StageResult(ok=True, missing=[], data={"stf_eligible": "No", "stf_reasons": ["Not eligible: " + "; ".join(failed)]})


# -----------------------------
# Stage 4: LIV 
# -----------------------------
def compute_liv_stage(
    p: Dict[FieldRef, Any],
    lenke_type: str,
    lumbar_modifier: str,
    stf_eligible: str,
) -> StageResult:
    wants_stf_needed = (lenke_type == "Lenke 3" and stf_eligible == "Yes")
    base_needed = [F_MT_LTV, F_STABLE_V] if lenke_type in ("Lenke 1", "Lenke 2", "Lenke 3") else []
    if wants_stf_needed:
        base_needed = base_needed + [F_WANTS_STF]

    missing = _missing_fields(p, base_needed)
    if missing:
        return StageResult(ok=False, missing=missing, data={})

    stable_v = _s(p.get(F_STABLE_V)).upper()
    mt_ltv = _s(p.get(F_MT_LTV)).upper()
    wants_stf = norm_yes_no(p.get(F_WANTS_STF))

    # STF-path 
    liv_stf = ""
    if lenke_type in ("Lenke 1", "Lenke 2"):
        liv_stf = stable_v if lumbar_modifier in ("A", "B") else mt_ltv if lumbar_modifier == "C" else ""
    elif lenke_type == "Lenke 3" and stf_eligible == "Yes" and wants_stf == "Yes":
        liv_stf = stable_v if lumbar_modifier in ("A", "B") else mt_ltv if lumbar_modifier == "C" else ""

    # If we are Lenke 1/2, done
    if lenke_type in ("Lenke 1", "Lenke 2"):
        if lumbar_modifier in ("A", "B"):
            return StageResult(ok=True, missing=[], data={"liv": liv_stf or "—", "liv_rationale": f"{lenke_type} mod {lumbar_modifier} → LIV = SV ({stable_v})"})
        if lumbar_modifier == "C":
            return StageResult(ok=True, missing=[], data={"liv": liv_stf or "—", "liv_rationale": f"{lenke_type} mod C → LIV = LTV ({mt_ltv})"})
        return StageResult(ok=True, missing=[], data={"liv": "—", "liv_rationale": ""})

    # Lenke 3 with STF eligible and patient agrees routes to STF path
    if lenke_type == "Lenke 3" and stf_eligible == "Yes" and wants_stf == "Yes":
        if lumbar_modifier in ("A", "B"):
            return StageResult(ok=True, missing=[], data={"liv": liv_stf or "—", "liv_rationale": f"Lenke 3 mod {lumbar_modifier} + STF eligible, patient agrees → LIV = SV ({stable_v})"})
        if lumbar_modifier == "C":
            return StageResult(ok=True, missing=[], data={"liv": liv_stf or "—", "liv_rationale": f"Lenke 3 mod C + STF eligible, patient agrees → LIV = LTV ({mt_ltv})"})
        return StageResult(ok=True, missing=[], data={"liv": "—", "liv_rationale": ""})

    # Otherwise non-STF path for Lenke 3–6
    if lenke_type in ("Lenke 3", "Lenke 4", "Lenke 5", "Lenke 6"):
        needed2 = [F_LUMBAR_APEX, F_BEND_L3_4, F_NV_GRADE, F_LORD_DISC]
        missing2 = _missing_fields(p, needed2)
        if missing2:
            return StageResult(ok=False, missing=missing2, data={})

        lumbar_apex = _s(p.get(F_LUMBAR_APEX)).upper()
        bend_l3_4 = to_float(p.get(F_BEND_L3_4))
        nv = to_int(p.get(F_NV_GRADE))
        lord_disc = norm_yes_no(p.get(F_LORD_DISC))

        apex_ok = v_le(lumbar_apex, "L2") is True
        disc_ok = bend_l3_4 is not None and bend_l3_4 < 0
        nv_ok = nv is not None and nv >= -4
        lord_ok = lord_disc == "Yes"

        if apex_ok and disc_ok and nv_ok and lord_ok:
            return StageResult(ok=True, missing=[], data={"liv": "L3", "liv_rationale": "LIV = L3: apex ≤ L2, lordotic disc, bending L3–4 < 0, NV ≥ –4"})
        return StageResult(ok=True, missing=[], data={"liv": "L4", "liv_rationale": "LIV = L4: one or more risk factors present (apex, disc, lordosis, NV)"})

    return StageResult(ok=True, missing=[], data={"liv": "—", "liv_rationale": ""})


# -----------------------------
# Stage 5: SLF eligibility (Lenke 5C/6C)
# -----------------------------
def compute_slf_stage(p: Dict[FieldRef, Any], lenke_type: str, lumbar_modifier: str) -> StageResult:
    if not (lenke_type in ("Lenke 5", "Lenke 6") and lumbar_modifier == "C"):
        return StageResult(ok=True, missing=[], data={"slf_eligible": "No", "slf_reason": "Not eligible: Lenke type ≠ 5/6 or lumbar modifier ≠ C"})

    needed = [F_TRUNK_SHIFT, F_SHOULDER, F_COBB_RATIO, F_TRANS_RATIO, F_THOR_FLEX]
    missing = _missing_fields(p, needed)
    if missing:
        return StageResult(ok=False, missing=missing, data={})

    trunk = norm_side(p.get(F_TRUNK_SHIFT))
    shoulder = norm_side(p.get(F_SHOULDER))
    cobb_ratio = to_float(p.get(F_COBB_RATIO))
    trans_ratio = to_float(p.get(F_TRANS_RATIO))
    thor_flex = to_float(p.get(F_THOR_FLEX))

    stand_mt = to_float(p.get(F_STAND_MT))
    t10_l2 = to_float(p.get(F_T10_L2))

    failed: List[str] = []
    if trunk != "Left":
        failed.append("Trunk shift ≠ Left")
    if shoulder != "Left":
        failed.append("Shoulder ≠ Left")
    if cobb_ratio is None or cobb_ratio <= 1.25:
        failed.append("Cobb ratio ≤ 1.25")
    if trans_ratio is None or trans_ratio <= 1.25:
        failed.append("Translation ratio ≤ 1.25")
    if stand_mt is None or stand_mt >= 40:
        failed.append("Thoracic (MT) Cobb ≥ 40°")
    if t10_l2 is None or t10_l2 >= 10:
        failed.append("T10–L2 kyphosis ≥ 10°")
    if thor_flex is None or thor_flex < 30:
        failed.append("Thoracic flexibility < 30%")

    if not failed:
        return StageResult(ok=True, missing=[], data={"slf_eligible": "Yes", "slf_reason": "Eligible (all Baldwin SLF criteria met)"})
    return StageResult(ok=True, missing=[], data={"slf_eligible": "No", "slf_reason": "Not eligible: " + "; ".join(failed)})

# -----------------------------
# Page 4
# -----------------------------
def compute_baldwin_v2(present: Dict[FieldRef, Any]) -> Dict[str, Any]:
    """
    present: mapping from (tab, key) -> raw UI values

    Returns:
      - results compatible with your existing Page04 'level_selection' schema
      - ui_hints: which fields are needed now, and which sections should show
    """

    ui_needed: List[FieldRef] = []
    ui_sections: Dict[str, bool] = {
        "lenke": True,
        "translations": False,
        "stf": False,
        "slf": False,
        "uiv": False,
        "liv": False,
        "baldwin_extras": False,
    }

    # Default outputs
    out = {
        "lenke_type": "Unclassified",
        "lumbar_modifier": "—",
        "sagittal_modifier": "—",
        "uiv": "—",
        "uiv_rationale": "",
        "stf_eligible": "No",
        "stf_reasons": [],
        "liv": "—",
        "liv_rationale": "",
        "slf_eligible": "No",
        "slf_reason": "",
        "anatomy_warning": "",
    }
    
    variant_vertebral_anatomy = norm_yes_no(
        present.get(("additional_standing_coronal", "variant_vertebral_anatomy"))
    )

    if variant_vertebral_anatomy == "Yes":
        out["anatomy_warning"] = (
            "Variant vertebral anatomy is present. Please double check level suggestions, "
            "as the algorithm is based on typical vertebral anatomy."
        )
    else:
        out["anatomy_warning"] = ""

    # 1) Lenke stage
    r1 = compute_lenke_stage(present)
    if not r1.ok:
        ui_needed.extend(r1.missing)
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out

    out.update({k: v for k, v in r1.data.items() if k in out})
    lenke_type = r1.data.get("lenke_type", "Unclassified")
    lumbar_modifier = r1.data.get("lumbar_modifier", "—")

    if lenke_type == "Unclassified" or lumbar_modifier == "—":
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out

    ui_sections["uiv"] = True
    ui_sections["liv"] = True

    # 2) UIV stage 
    r2 = compute_uiv_stage(present, lenke_type)
    if not r2.ok:
        ui_needed.extend(r2.missing)
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out
    out.update(r2.data)

    # 3) STF stage (only if Lenke 1–3 and lumbar C)
    stf_should_eval = (lenke_type in ("Lenke 1", "Lenke 2", "Lenke 3") and lumbar_modifier == "C")
    ui_sections["translations"] = stf_should_eval
    ui_sections["stf"] = stf_should_eval

    r3 = compute_stf_stage(present, lenke_type, lumbar_modifier)
    if not r3.ok:
        ui_needed.extend(r3.missing)
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out
    out.update(r3.data)

    # 4) LIV stage depends on STF result for Lenke 3
    stf_eligible = out.get("stf_eligible", "No")
    r4 = compute_liv_stage(present, lenke_type, lumbar_modifier, stf_eligible)
    if not r4.ok:
        ui_needed.extend(r4.missing)
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out
    out.update(r4.data)

    # 5) SLF stage only for Lenke 5C/6C
    slf_should_eval = (lenke_type in ("Lenke 5", "Lenke 6") and lumbar_modifier == "C")
    ui_sections["slf"] = slf_should_eval

    r5 = compute_slf_stage(present, lenke_type, lumbar_modifier)
    if not r5.ok:
        ui_needed.extend(r5.missing)
        out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
        return out
    out.update(r5.data)

    out["ui_hints"] = {"needed_fields": ui_needed, "sections": ui_sections}
    return out