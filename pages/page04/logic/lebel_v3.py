from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List


def _f(x, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def _i(x, default: Optional[int] = None) -> Optional[int]:
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except Exception:
        return default


def _norm_dir(s: str) -> str:
    s = (s or "").strip()
    if s in ("", "0", "Neutral", "Neither"):
        return "Neither"
    if s.lower().startswith("l"):
        return "Left"
    if s.lower().startswith("r"):
        return "Right"
    return s

def _norm_l4_tilt(s: str) -> str:
    s = (s or "").strip()
    if s in ("", "0", "Neutral", "Neither"):
        return "Left"
    if s.lower().startswith("l"):
        return "Left"
    if s.lower().startswith("r"):
        return "Right"
    return s

_VERTEBRA_ORDER = {f"T{i}": i for i in range(1, 13)}
_VERTEBRA_ORDER.update({f"L{i}": 100 + i for i in range(1, 6)})

_ORDER_TO_VERTEBRA = {v: k for k, v in _VERTEBRA_ORDER.items()}

def _next_distal_level(level: str) -> str:
    s = (level or "").strip().upper()
    rank = _VERTEBRA_ORDER.get(s)
    if rank is None:
        return s
    nxt = _ORDER_TO_VERTEBRA.get(rank + 1)
    return nxt or s

def _norm_s1_relation(s: str) -> str:
    s = (s or "").strip().lower()
    if s in ("intersected", "intersects", "through"):
        return "Intersected"
    if s in ("anterior", "in front", "front"):
        return "Anterior"
    if s in ("posterior", "behind", "back"):
        return "Posterior"
    return ""

def _apex_plus_one(level: str) -> str:
    s = (level or "").strip().upper()
    m = _VERTEBRA_ORDER.get(s)
    if m is None:
        return ""
    prev_level = _ORDER_TO_VERTEBRA.get(m - 1)
    return prev_level or s

# Choosing the more proximal of two levels
def _more_proximal(a: str, b: str) -> str:
    ra = _VERTEBRA_ORDER.get((a or "").strip().upper())
    rb = _VERTEBRA_ORDER.get((b or "").strip().upper())
    if ra is None:
        return b
    if rb is None:
        return a
    return a if ra < rb else b

def compute_lebel_v3(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs should be a flattened dict of the Lebel fields (you can map from plan_data into this).
    This function mirrors the Excel logic (Level Selection Algorithm Version 3).
    """

    # ----------------------------
    # Core inputs 
    # ----------------------------
    pt_cobb   = _f(inputs.get("pt_cobb"), 0.0) or 0.0
    mt_cobb   = _f(inputs.get("mt_cobb"), 0.0) or 0.0
    tll_cobb  = _f(inputs.get("tll_cobb"), 0.0) or 0.0

    pt_bend   = _f(inputs.get("pt_bend"), 0.0) or 0.0
    mt_bend   = _f(inputs.get("mt_bend"), 0.0) or 0.0
    tll_bend  = _f(inputs.get("tll_bend"), 0.0) or 0.0

    pt_kyph   = _f(inputs.get("t2_5_kyphosis"), 0.0) or 0.0
    t5_12     = _f(inputs.get("t5_12_kyphosis"), 0.0) or 0.0
    t10_l2    = _f(inputs.get("t10_l2_kyphosis"), 0.0) or 0.0

    csvl_pos  = (inputs.get("csvl_apex_position") or "").strip()   # A/B/C mapping in Excel
    shoulder  = _norm_dir(inputs.get("shoulder_elevation"))
    t1_tilt   = _norm_dir(inputs.get("t1_tilt_direction"))
    pt_apex   = (inputs.get("pt_apex_level") or "").strip()        # T1..T5
    uev       = (inputs.get("uev") or "").strip()                  # Used for Lenke 5
    risser = _i(inputs.get("risser_score"))
    variant_vertebral_anatomy = (inputs.get("variant_vertebral_anatomy") or "").strip()

    # STF-related
    mt_apical_trans  = _f(inputs.get("mt_apical_translation_mm"))
    tll_apical_trans = _f(inputs.get("tll_apical_translation_mm"))
    mt_nash_moe      = _f(inputs.get("mt_nashmoe_grade"))
    tll_nash_moe     = _f(inputs.get("tll_nashmoe_grade"))

    trunk_shift = _norm_dir(inputs.get("trunk_shift_direction"))
    lordotic_disc = (inputs.get("lordotic_disc_below_mt_ltv") or "").strip()  # Yes/No
    wants_stf = (inputs.get("wants_stf") or "").strip()  # Yes/No

    # LIV-related (Lenke 1/2 path)
    l4_tilt = _norm_l4_tilt(inputs.get("l4_tilt_direction"))    
    sltv = (inputs.get("sltv") or "").strip()
    lstv = (inputs.get("lstv") or "").strip()
    mt_ltv = (inputs.get("mt_ltv") or "").strip()

    # LIV-related (Lenke 3–6 risk path)
    l3_dev = _f(inputs.get("l3_deviation_csvl_mm"))
    l3_rot = _i(inputs.get("l3_rotation_grade"))
    sv = _i(inputs.get("sv_grade"))
    nv = _i(inputs.get("nv_grade"))

    upright_l3_4 = _f(inputs.get("upright_l3_4_disc_angle"))
    bending_l3_4 = _f(inputs.get("bending_l3_4_disc_angle"))

    s1_l3_relation = _norm_s1_relation(inputs.get("s1_plumb_line_l3_relation"))
    s1_l4_relation = _norm_s1_relation(inputs.get("s1_plumb_line_l4_relation"))
    s1_l5_relation = _norm_s1_relation(inputs.get("s1_plumb_line_l5_relation"))

    s1_relation_by_level = {
        "L3": s1_l3_relation,
        "L4": s1_l4_relation,
        "L5": s1_l5_relation,
    }

    # SLF-related
    cobb_ratio = (mt_cobb / tll_cobb) if tll_cobb else None
    translation_ratio = (mt_apical_trans / tll_apical_trans) if (mt_apical_trans and tll_apical_trans) else None
    thoracic_flex = None
    if mt_cobb:
        thoracic_flex = ((mt_cobb - mt_bend) / mt_cobb) * 100.0

    # ----------------------------
    # Structural flags
    # ----------------------------
    structural_pt = (pt_bend > 25) or (pt_kyph > 20)
    structural_mt = (mt_bend > 25)
    structural_tll = (tll_bend > 25) or (t10_l2 > 20)

    # Rare fallback:
    if (
        not structural_pt
        and not structural_mt
        and not structural_tll
        and pt_cobb < 25
        and mt_cobb < 25
        and tll_cobb < 25
    ):
        max_standing = max(pt_cobb, mt_cobb, tll_cobb)

        if pt_cobb == max_standing:
            structural_pt = True
        elif mt_cobb == max_standing:
            structural_mt = True
        else:
            structural_tll = True

    # ----------------------------
    # Lenke curve type 
    # ----------------------------
    lenke = "Unclassified"
    if structural_mt and (not structural_pt) and (not structural_tll):
        lenke = "Lenke 1"
    elif structural_pt and structural_mt and (not structural_tll):
        lenke = "Lenke 2"
    elif structural_mt and structural_tll and (not structural_pt):
        lenke = "Lenke 3"
        if mt_cobb < tll_cobb:
            lenke = "Lenke 6"
    elif structural_pt and structural_mt and structural_tll:
        lenke = "Lenke 4"
    elif structural_tll and (not structural_mt) and (not structural_pt):
        lenke = "Lenke 5"

    # ----------------------------
    # Lumbar modifier 
    # ----------------------------
    if csvl_pos == "Between Pedicles":
        lumbar_modifier = "A"
    elif csvl_pos == "Touches apical body":
        lumbar_modifier = "B"
    elif csvl_pos == "Completely medial":
        lumbar_modifier = "C"
    else:
        lumbar_modifier = "?"

    # ----------------------------
    # Sagittal modifier 
    # ----------------------------
    if t5_12 < 10:
        sagittal_modifier = "-"
    elif t5_12 <= 40:
        sagittal_modifier = "N"
    else:
        sagittal_modifier = "+"

    # ----------------------------
    # UIV 
    # ----------------------------
    uiv = ""
    uiv_rationale = ""

    if lenke == "Lenke 4" and pt_kyph > 20:
        apex_plus_one = _apex_plus_one(pt_apex)
        if apex_plus_one:
            uiv = _more_proximal("T2", apex_plus_one)
            uiv_rationale = f"Lenke 4 with significant proximal kyphosis (T2–T5 > 20°) → UIV = more proximal of T2 and apex+1 ({apex_plus_one})"
        else:
            uiv = "T2"
            uiv_rationale = "Lenke 4 with significant proximal kyphosis (T2–T5 > 20°) → T2"

    elif lenke in ("Lenke 1", "Lenke 3", "Lenke 4", "Lenke 6"):
        if shoulder == t1_tilt:
            if pt_apex == "T4":
                uiv = "T3"
                uiv_rationale = "Concordant: PT apex T4 → T3"
            else:
                uiv = "T4"
                uiv_rationale = "Concordant: PT apex ≠ T4 → T4"
        else:
            uiv = "T2"
            uiv_rationale = "Discordant shoulder vs T1 tilt → T2"

    elif lenke == "Lenke 2":
        uiv = "T2"
        uiv_rationale = "Lenke 2 → T2"

    elif lenke == "Lenke 5":
        if t10_l2 > 0:
            uiv = "T4"
            uiv_rationale = "Lenke 5, T10–L2 > 0 → T4"
        else:
            uiv = uev or ""
            uiv_rationale = "Lenke 5, T10–L2 ≤ 0 → UEV"
    # ----------------------------
    # STF eligibility
    # ----------------------------
    stf_criteria: List[Tuple[str, bool]] = []
    stf_possible = (lenke in ("Lenke 1", "Lenke 2", "Lenke 3", "Lenke 4")) and (lumbar_modifier == "C")

    atr = (mt_apical_trans / tll_apical_trans) if (mt_apical_trans and tll_apical_trans) else None
    avrr = (mt_nash_moe / tll_nash_moe) if (mt_nash_moe and tll_nash_moe) else None
    mt_minus_tll = mt_cobb - tll_cobb

    stf_eligible = "No"
    stf_reasons: List[str] = []

    if stf_possible:
        stf_criteria = [
            ("TL/L bend < 25°", tll_bend < 25),
            ("MT–TL/L > 10°", mt_minus_tll > 10),
            ("ATR > 1.2", (atr is not None) and (atr > 1.2)),
            ("AVRR > 1.2", (avrr is not None) and (avrr > 1.2)),
            ("T10–L2 < 10°", t10_l2 < 10),
            ("TL/L Cobb < 50°", tll_cobb < 50),
            ("Trunk shift = Right", trunk_shift == "Right"),
            ("Lordotic disc below MT-LTV = Yes", lordotic_disc == "Yes"),
        ]
        for name, ok in stf_criteria:
            stf_reasons.append(("✓ " if ok else "✗ ") + name)

        all_ok = all(ok for _, ok in stf_criteria)
        if all_ok and wants_stf == "Yes":
            stf_eligible = "Yes"
        elif all_ok and wants_stf != "Yes":
            stf_reasons.append("✗ Patient preference not set to Yes")

    else:
        stf_reasons.append("Not applicable (requires Lenke 1–4 and lumbar modifier C)")

    # ----------------------------
    # Disc Flexibility Index + TSS 
    # ----------------------------
    disc_flex = None
    if upright_l3_4 and upright_l3_4 != 0 and bending_l3_4 is not None:
        disc_flex = ((upright_l3_4 - bending_l3_4) / upright_l3_4) * 100.0

    tss = None
    if sv is not None and nv is not None:
        tss = sv + nv

    # ----------------------------
    # LIV 
    # ----------------------------
    liv_12_or_stf = ""
    liv_36 = ""

    # Lenke 1/2 logic
    if lenke in ("Lenke 1", "Lenke 2"):
        if lumbar_modifier == "A":
            # Excel: IF L4 tilt = Left → SLTV else → LSTV
            liv_12_or_stf = sltv if l4_tilt == "Left" else lstv
        elif lumbar_modifier in ("B", "C"):
            liv_12_or_stf = mt_ltv if (stf_eligible == "Yes") else sltv

    # Lenke 3/4 selective thoracic fusion 
    if lenke in ("Lenke 3", "Lenke 4") and stf_eligible == "Yes":
        liv_12_or_stf = mt_ltv

    # Lenke 3–6 risk criteria 
    if lenke in ("Lenke 3", "Lenke 4", "Lenke 5", "Lenke 6"):
        risk = []
        if l3_dev is not None and l3_dev > 20:
            risk.append("L3 deviation > 20 mm")
        if l3_rot is not None and l3_rot >= 2:
            risk.append("L3 rotation ≥ 2")
        if tss is not None and tss <= -5:
            risk.append("TSS ≤ -5")
        if disc_flex is not None and disc_flex < 25:
            risk.append("Disc flexibility < 25%")
        if risser is not None and risser < 2:
            risk.append("Risser < 2")

        liv_36 = "L4" if risk else "L3"
        liv_36_rationale = ("L4 due to: " + "; ".join(risk)) if risk else "L3: No risk criteria"
    else:
        liv_36_rationale = ""

    # Master LIV output 
    if lenke in ("Lenke 1", "Lenke 2"):
        liv = liv_12_or_stf or ""
        liv_rationale = "Lenke 1/2 pathway"
    elif lenke in ("Lenke 3", "Lenke 4") and stf_eligible == "Yes":
        liv = liv_12_or_stf or ""
        liv_rationale = "Lenke 3/4 STF pathway"
    else:
        liv = liv_36 or ""
        liv_rationale = liv_36_rationale

    # ----------------------------
    # S1 plumb line distal check
    # LIV must be intersected by or anterior to the S1 plumb line, not posterior
    # If posterior, move distally until satisfied
    # ----------------------------
    liv_adjustment_note = ""

    if liv:
        checked_levels = []
        while liv in s1_relation_by_level:
            rel = s1_relation_by_level.get(liv, "")
            checked_levels.append(f"{liv}:{rel or 'Unknown'}")

            if rel in ("Intersected", "Anterior"):
                break

            if rel == "Posterior":
                old_liv = liv
                new_liv = _next_distal_level(liv)
                if new_liv == liv:
                    liv_adjustment_note = (
                        f"S1 plumb line check found {old_liv} posterior to the plumb line, "
                        f"but no more distal predefined level is available. Please review sagittal alignment."
                    )
                    break
                liv = new_liv
                liv_adjustment_note = (
                    f"S1 plumb line check adjusted LIV distally from {old_liv} to {new_liv}. "
                    f"Please review sagittal alignment."
                )
                continue
            break
    # ----------------------------
    # SLF eligibility 
    # Only Lenke 5/6 and lumbar C
    # ----------------------------
    slf_eligible = "No"
    slf_reason = "Not eligible"
    if lenke in ("Lenke 5", "Lenke 6") and lumbar_modifier == "C":
        reasons = []
        # Required: trunk shift = Left and shoulder elevation = Left
        if trunk_shift != "Left":
            reasons.append("Trunk shift ≠ Left")
        if shoulder != "Left":
            reasons.append("Shoulder elevation ≠ Left")
        if cobb_ratio is None or cobb_ratio <= 1.25:
            reasons.append("Cobb ratio ≤ 1.25")
        if translation_ratio is None or translation_ratio <= 1.25:
            reasons.append("Translation ratio ≤ 1.25")
        if mt_cobb >= 40:
            reasons.append("MT Cobb ≥ 40°")
        if t10_l2 >= 10:
            reasons.append("T10–L2 ≥ 10°")
        if thoracic_flex is None or thoracic_flex < 30:
            reasons.append("Thoracic curve flexibility < 30%")

        if not reasons:
            slf_eligible = "Yes"
            slf_reason = "Eligible (all criteria met)"
        else:
            slf_reason = "Not eligible: " + "; ".join(reasons)
        
    anatomy_warning = ""
    if variant_vertebral_anatomy == "Yes":
        anatomy_warning = (
            "Variant vertebral anatomy is present. Please double check level suggestions, "
            "as the algorithm is based on typical vertebral anatomy."
        )

    return {
        "lenke_type": lenke,
        "lumbar_modifier": lumbar_modifier,
        "sagittal_modifier": sagittal_modifier,
        "uiv": uiv or "—",
        "uiv_rationale": uiv_rationale,
        "stf_possible": "Yes" if stf_possible else "No",
        "stf_eligible": stf_eligible,
        "stf_reasons": stf_reasons,
        "liv": liv or "—",
        "liv_rationale": liv_rationale,
        "liv_warning": liv_adjustment_note,
        "disc_flex_index_pct": None if disc_flex is None else round(disc_flex, 1),
        "tss": tss,
        "slf_eligible": slf_eligible,
        "slf_reason": slf_reason,
        "anatomy_warning": anatomy_warning,
    }