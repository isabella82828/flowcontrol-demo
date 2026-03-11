from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Tuple, List, Any, Optional

import pyodbc

# ── connection defaults ────────────────────────────────────────────────────────
_SERVER   = "ORTDOCSQLSVAPRD"
_DATABASE = "SK_TDOC"
_DRIVER   = "SQL Server"          # built-in Windows driver; works with Windows Auth
_MDRD_STOCK_ID = 1005             # 'MDRD IMPLANTS'

Key = Tuple[str, float, int]      # (screw_type, diameter_mm, length_mm)


# ──────────────────────────────────────────────────────────────────────────────
# Public API 
# ──────────────────────────────────────────────────────────────────────────────

def get_default_inventory_path() -> str:
    return ""


def load_inventory_sql(
    server:   str = _SERVER,
    database: str = _DATABASE,
    driver:   str = _DRIVER,
    stock_id: int = _MDRD_STOCK_ID,
) -> Tuple[Dict[Key, int], Dict[Key, List[Dict[str, Any]]]]:

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )
    conn   = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute(_SCREW_QUERY, stock_id)
    raw_rows = cursor.fetchall()
    conn.close()

    return _build_dicts(raw_rows)


# Alias so Page10 can call load_inventory_excel(path) and we just ignore path
def load_inventory_excel(filepath: str, sheet_name: Optional[str] = None):
    return load_inventory_sql()


# ──────────────────────────────────────────────────────────────────────────────
# SQL query
# ──────────────────────────────────────────────────────────────────────────────

_SCREW_QUERY = """
SELECT
    i.ITEMKEYID,
    i.ITEMITEM,
    i.ITEMTEXT,
    i.ITEMSUPPLIERNO,
    s.STOONSTOCK,
    s.STOMAXCOUNT,
    s.STOMINCOUNT,
    s.STOPLACEMENT
FROM dbo.TITEM i
JOIN dbo.TSTOCK s ON s.STOREFITEMKEYID = i.ITEMKEYID
                  AND s.STOSTOKKEYID = ?
WHERE (
      LOWER(i.ITEMTEXT) LIKE '%mono axial%xia%'
   OR LOWER(i.ITEMTEXT) LIKE '%poly axial%xia%'
   OR LOWER(i.ITEMTEXT) LIKE '%monoaxial%xia%'
   OR LOWER(i.ITEMTEXT) LIKE '%polyaxial%xia%'
   OR LOWER(i.ITEMTEXT) LIKE '%cannulated%xia%'
   OR LOWER(i.ITEMTEXT) LIKE '%uniaxial%xia%'
)
AND s.STOONSTOCK IS NOT NULL
AND s.STOONSTOCK >= 0
ORDER BY i.ITEMTEXT
"""

# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers
# ──────────────────────────────────────────────────────────────────────────────

# e.g. "4.5MMX30MM" or "4.5 MM X 30 MM"
_DIM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*mm\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm",
    re.IGNORECASE,
)


def _parse_screw_type(text: str) -> Optional[str]:
    t = text.upper()
    if "MONO" in t:
        return "Monoaxial"
    if "POLY" in t:
        return "Polyaxial"
    if "CANN" in t:
        return "Cannulated"
    if "UNI"  in t:
        return "Uniaxial"
    return None


def _parse_dims(text: str) -> Optional[Tuple[float, int]]:
    """Return (diameter_mm, length_mm) or None if not found."""
    m = _DIM_RE.search(text)
    if not m:
        return None
    try:
        dia = float(m.group(1))
        length = int(round(float(m.group(2))))
        return dia, length
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Build return dicts
# ──────────────────────────────────────────────────────────────────────────────

def _build_dicts(
    raw_rows,
) -> Tuple[Dict[Key, int], Dict[Key, List[Dict[str, Any]]]]:

    totals_by_key: Dict[Key, int]                   = defaultdict(int)
    rows_by_key:   Dict[Key, List[Dict[str, Any]]]  = defaultdict(list)

    for row in raw_rows:
        (item_keyid, itemitem, itemtext,
         supplierno, on_stock, max_count, min_count, placement) = row

        text = (itemtext or "").strip()

        screw_type = _parse_screw_type(text)
        dims       = _parse_dims(text)

        if screw_type is None or dims is None:
            continue

        dia, length = dims
        key: Key = (screw_type, dia, length)

        qty = int(on_stock) if on_stock is not None else 0

        totals_by_key[key] += qty

        rows_by_key[key].append({
            "type":               screw_type,
            "diameter_mm":        dia,
            "length_mm":          length,
            "item_keyid":         item_keyid,
            "product_number":     supplierno or "",
            "item_code":          itemitem   or "",
            "description":        text,
            "stock_location":     placement  or "",
            "total_in_hospital":  qty,
            "max_par":            int(max_count) if max_count else None,
            "min_par":            int(min_count) if min_count else None,
        })

    return dict(totals_by_key), dict(rows_by_key)


# ──────────────────────────────────────────────────────────────────────────────
# Validation  
# ──────────────────────────────────────────────────────────────────────────────

def validate_inventory_data(
    totals_by_key: Dict[Key, int],
    rows_by_key:   Dict[Key, List[Dict[str, Any]]],
):

    if not rows_by_key:
        return (
            False,
            "No screw rows found. Check the SQL connection and stock filter.",
            {},
        )

    total_rows  = sum(len(v) for v in rows_by_key.values())
    zero_totals = sum(1 for v in totals_by_key.values() if v <= 0)

    stats = {
        "groups": len(rows_by_key),
        "rows":   total_rows,
        "groups_with_zero_total": zero_totals,
    }

    warn = ""
    if zero_totals / max(1, len(rows_by_key)) > 0.5:
        warn = " Note: many groups have zero stock – counts may be out of date."

    return (
        True,
        f"SQL inventory loaded. {total_rows} rows across {len(rows_by_key)} screw groups.{warn}",
        stats,
    )