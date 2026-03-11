from __future__ import annotations
from collections import defaultdict
from typing import Dict, Tuple, List

Key = Tuple[str, float, int]  # (type, diameter_mm, length_mm)

def build_usage_counter() -> Dict[Key, int]:
    return defaultdict(int)


def recompute_usage_from_plan(plan_data: dict) -> Dict[Key, int]:
    usage: Dict[Key, int] = defaultdict(int)

    ap = plan_data.get("anchor_planning", {})
    anchors = ap.get("anchors", {})

    for _level, sides in anchors.items():
        if not isinstance(sides, dict):
            continue

        for side in ("left", "right"):
            a = sides.get(side, {})
            if not isinstance(a, dict):
                continue

            if (a.get("anchor_type") or "").strip() != "Screw":
                continue

            t = (a.get("screw_type") or "").strip()
            d_raw = a.get("diameter_mm")
            L_raw = a.get("length_mm")

            # Skip incomplete selections (common while user is mid-selection)
            if d_raw is None or L_raw is None:
                continue

            d_s = str(d_raw).strip()
            L_s = str(L_raw).strip()

            if not t or d_s == "" or L_s == "":
                continue

            try:
                d_val = float(d_s)
                L_val = int(float(L_s))
            except Exception:
                continue

            key: Key = (t, d_val, L_val)
            usage[key] += 1

    return dict(usage)


def compute_overages(
    usage_counts: Dict[Key, int],
    totals_by_key: Dict[Key, int],
) -> List[dict]:
    over = []
    for key, used in usage_counts.items():
        available = int(totals_by_key.get(key, 0))
        if used > available:
            over.append(
                {
                    "key": key,
                    "used": used,
                    "available": available,
                    "over_by": used - available,
                }
            )

    over.sort(key=lambda x: (x["over_by"], x["used"]), reverse=True)
    return over

def format_overage_messages(overages: List[dict]) -> List[str]:
    msgs = []
    for o in overages:
        t, d, L = o["key"]
        msgs.append(
            f"⚠️ Warning: {o['used']} screws of type {d} × {L} mm {t} exceed stock ({o['available']} available)"
        )
    return msgs
