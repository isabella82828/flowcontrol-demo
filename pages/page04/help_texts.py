from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

@dataclass(frozen=True)
class HelpItem:
    title: str
    body: str
    image_relpath: Optional[str] = None  # relative to project root, assets

# -----------------------------------------------------------------------------
# Registry: HELP[tab_name][key] -> HelpItem(title, body)
# -----------------------------------------------------------------------------
HELP: Dict[str, Dict[str, HelpItem]] = {
    # -------------------------------------------------------------------------
    # tab: standing_coronal
    # -------------------------------------------------------------------------
    "standing_coronal": {
        "leg_length_discrepancy": HelpItem(
            title="Leg Length Discrepancy",
            body=(
                "Direction: which side is longer, or no clinically significant difference.\n"
                "Magnitude: whether the discrepancy is < 1 cm or ≥ 1 cm.\n\n"
                "If not measured, choose Not assessed / Unknown."
            ),
        ),
        "other_anatomic_considerations": HelpItem(
            title="Other anatomic considerations",
            body="Please enter any anatomic variants or considerations not captured above.",
        ),
        "pt_cobb": HelpItem(
            title="Proximal Thoracic Cobb Angle (deg)",
            body=(
                "The coronal angle between the cranial endplate of the most tilted vertebra above "
                "the proximal thoracic curve apex and the caudal endplate of the most tilted vertebra "
                "below the apex (typically from T1 or T2 to T5)."
            ),
        ),
        "mt_apex_direction": HelpItem(
            title="Main Thoracic Curve Apex Direction",
            body="Direction of Main Thoracic Curve Convexity.",
        ),
        "mt_cobb": HelpItem(
            title="Main Thoracic Cobb Angle (deg)",
            body=(
                "The coronal angle between the upper endplate of the most tilted vertebra above the "
                "main thoracic curve apex and the lower endplate of the most tilted vertebra below the "
                "apex (usually T4 to T12)."
            ),
        ),
        "tl_l_cobb": HelpItem(
            title="Thoracolumbar / Lumbar Cobb Angle (deg)",
            body=(
                "The coronal angle between the most tilted vertebra above the apex (often T10 to T12) "
                "and the most tilted vertebra below the apex (often L3 to L4)."
            ),
        ),
        "risser_score": HelpItem(
            title="Risser Score",
            body=(
                "0 = No ossification of the iliac apophysis\n"
                "1 = Up to 25% ossification (starts at anterolateral crest)\n"
                "2 = 26 to 50% ossification\n"
                "3 = 51 to 75% ossification\n"
                "4 = 76 to 100% ossification\n"
                "5 = Complete ossification and fusion to iliac crest"
            ),
        ),
        "lstv": HelpItem(
            title="Last Substantially Touched Vertebra (LSTV)",
            body="Last vertebra where the CSVL passes medial to the pedicles on the standing radiograph",
        ),
        "lordotic_disc_below_mt_ltv": HelpItem(
            title="Lordotic Disc Below LTV of MT Curve",
            body=(
                "Is the disc immediately below the last touched vertebra (LTV) of the main thoracic curve "
                "lordotic on standing radiograph?\n\n"
                "Yes = disc is lordotic.\n"
                "No = disc is neutral or kyphotic."
            ),
        ),
        "trunk_shift": HelpItem(
            title="Trunk Shift",
            body=(
                "Trunk shift is calculated by measuring the linear distance in millimeters between the "
                "vertical trunk reference line (VTRL) and the CSVL. A trunk shift to the right of the CSVL "
                "is a positive value, and to the left of the CSVL a negative value."
            ),
        ),
        "csvl_tll_apex_position": HelpItem(
            title="CSVL–TL/L Apex Position",
            body="Where is Center Sacral Vertical Line situated compared to the Lumbar Apical Vertebra?",
            image_relpath="assets/csvl.png",
        ),
        "mt_ltv": HelpItem(
            title="MT-LTV",
            body="Last touched vertebra of the main thoracic curve (MT-LTV), measured per the algorithm definition.",
        ),
        "l4_tilt_direction": HelpItem(
            title="L4 Tilt Direction",
            body="Right = L4 endplate slopes down towards right. Left = L4 endplate slopes down towards left",
        ),
        "t1_tilt": HelpItem(
            title="T1 Tilt",
            body=(
                "Coronal angle between the cranial endplate of the most titled vertebra above the proximal "
                "thoracic curve apex and the caudal endplate of the most tilted vertebra below the apex "
                "(typically from T1 or T2 to T5)."
            ),
        ),
        "mt_apical_translation_mm": HelpItem(
            title="MT Apical Translation (mm)",
            body=(
                "Distance (mm) between centroid of the apical vertebra and the reference line. "
                "Use C7 plumbline for main thoraic curve."
            ),
        ),
        "tll_apical_translation_mm": HelpItem(
            title="TL/L Apical Translation (mm)",
            body=(
                "Distance (mm) between centroid of the apical vertebra and the reference line. "
                "Use C7 plumbline for main thoracic curve."
            ),
        ),
        "l3_deviation_csvl_mm": HelpItem(
            title="L3 Deviation from CSVL (mm)",
            body="Distance (mm) between the centroid of the L3 vertebra and the CSVL.",
        ),
        "l3_rotation_nashmoe": HelpItem(
            title="L3 Rotation (Nash Moe)",
            body=(
                "Grade 0 Pedicles symmetric\n"
                "Grade 1 Concave pedicle moves toward midline\n"
                "Grade 2 Concave pedicle at midline\n"
                "Grade 3 Convex pedicle begins to disappear\n"
                "Grade 4 Convex pedicle completely disappears"
            ),
        ),
        "nash_moe_grade": HelpItem(
            title="Nash-Moe rotation grade",
            body=(
                "Nash-Moe rotation grade.\n\n"
                "Grade 0: Pedicles symmetric.\n"
                "Grade 1: Convex pedicle moves toward the midline.\n"
                "Grade 2: Convex pedicle is two-thirds of the way to the midline.\n"
                "Grade 3: Convex pedicle at the midline.\n"
                "Grade 4: Convex pedicle beyond the midline."
            ),
        ),
        "selective_thoracic_fusion": HelpItem(
            title="Selective Thoracic Fusion",
            body="Patient preference: proceed with Selective Thoracic Fusion (Yes or No).",
        ),
    },

    # -------------------------------------------------------------------------
    # tab: bending
    # -------------------------------------------------------------------------
    "bending": {
        "pt_cobb": HelpItem(
            title="Bending Proximal Thoracic Cobb Angle (deg)",
            body=(
                "Angle between the cranial endplate of the most tilted vertebra above the proximal thoracic "
                "curve apex and the caudal endplate of the most tilted vertebra below the apex "
                "(typically T1 or T2 to T5)."
            ),
        ),
        "mt_cobb": HelpItem(
            title="Bending Main Thoracic Cobb Angle (deg)",
            body=(
                "Angle between the upper endplate of the most tilted vertebra above the main thoracic curve "
                "apex and the lower endplate of the most tilted vertebra below the apex (usually T4 to T12)."
            ),
        ),
        "tl_l_cobb": HelpItem(
            title="Bending Thoracolumbar / Lumbar Cobb Angle (deg)",
            body=(
                "Use the same end vertebrae on bending films (towards the convexity of the thoracolumbar/lumbar curve) "
                "as those chosen on the standing radiograph. "
            ),
        ),
        "l3_4_disc_angle": HelpItem(
            title="Bending L3–4 Disc Angle (deg)",
            body=(
                "Angle of the L3–4 disc space on bending films.\n\n"
                "Bending toward convexity of lumbar curve.\n"
                "Left-convex disc angulation: Positive (+) value\n"
                "Right-convex disc angulation: Negative (-) value"
            ),
        ),
    },

    # -------------------------------------------------------------------------
    # tab: standing_sagittal
    # -------------------------------------------------------------------------
    "standing_sagittal": {
        "t2_5_kyphosis": HelpItem(
            title="T2–T5 Kyphosis (deg)",
            body=(
                "Sagittal angle between the superior endplate of T1 or T2 and the inferior endplate of T5.\n\n"
                "Positive value is kyphosis.\n"
                "Negative value is lordosis."
            ),
        ),
        "t5_12_kyphosis": HelpItem(
            title="T5–T12 Kyphosis (deg)",
            body=(
                "Sagittal angle between the superior endplate of T5 and the inferior endplate of T12.\n\n"
                "Positive value is kyphosis.\n"
                "Negative value is lordosis."
            ),
        ),
        "t10_l2_kyphosis": HelpItem(
            title="T10–L2 Kyphosis (deg)",
            body=(
                "Sagittal angle between the superior endplate of T10 and the inferior endplate of L2.\n\n"
                "Positive value is kyphosis.\n"
                "Negative value is lordosis."
            ),
        ),
        "pt_apex_level": HelpItem(
            title="PT Kyphosis Apical Vertebra",
            body="Vertebra at the apex of the proximal thoracic kyphotic segment.",
        ),
        "pelvic_incidence": HelpItem(
            title="Pelvic Incidence",
            body=(
                "Angle between a line perpendicular to the sacral endplate midpoint and a line connecting this "
                "point to the center of the femoral head axis (bicoxofemoral axis)."
            ),
        ),
        "l3_4_disc_angle_upright": HelpItem(
            title="Upright L3–4 Disc Angle (deg)",
            body=(
                "Angle between the inferior endplate of L3 and the superior endplate of L4 on upright (standing) imaging.\n\n"
                "Sign convention:\n"
                "Positive (+): left-convex disc angulation.\n"
                "Negative (–): right-convex disc angulation.\n"
                "0: neutral."
            ),
        ),
    },

    # -------------------------------------------------------------------------
    # tab: supine_coronal
    # -------------------------------------------------------------------------
    "supine_coronal": {
        "supine_last_touched_vertebra": HelpItem(
            title="Supine Last Touched Vertebra",
            body=(
                "Most cephalad thoracolumbar or lumbar vertebra (T12 to L5) that is “touched” by the CSVL "
                "on any portion of the vertebra, measured on the supine radiograph."
            ),
        ),
        "l4_slope_modifier_lenke1": HelpItem(
            title="L4 Slope (Lenke 1AL/1AR)",
            body=(
                "If Lenke 1 curve: determine whether L4 slopes downward toward the left or toward the right.\n\n"
                "Toward the left → classify as 1AL\n"
                "Toward the right → classify as 1AR"
            ),
        ),
    },
}


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def get_help(tab: str, key: str, default: str = "") -> str:
    """
    Return help body text for a (tab, key). If missing, returns default (empty by default).
    """
    item = (HELP.get(tab) or {}).get(key)
    return item.body if item else default

def get_help_item(tab: str, key: str) -> Optional[HelpItem]:
    return (HELP.get(tab) or {}).get(key)

def get_help_pair(tab: str, key: str, default_title: str = "", default_body: str = "") -> Tuple[str, str]:
    item = (HELP.get(tab) or {}).get(key)
    if not item:
        return default_title, default_body
    return item.title, item.body


def has_help(tab: str, key: str) -> bool:
    return key in (HELP.get(tab) or {})


def available_keys(tab: str) -> Tuple[str, ...]:
    return tuple(sorted((HELP.get(tab) or {}).keys()))