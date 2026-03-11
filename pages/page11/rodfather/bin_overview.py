BINS = (100, 200, 300, 400, 600)

def bin_length(length_mm: float) -> int:
    try:
        L = float(length_mm)
    except Exception:
        return -1

    for b in BINS:
        if L <= b:
            return b
    return 600


def compute_bin_overview(offcuts: list[dict]) -> dict:
    overview = {
        b: {"available": 0, "reserved": 0, "total": 0}
        for b in BINS
    }

    for o in offcuts:
        b = bin_length(o.get("length"))
        if b not in overview:
            continue

        status = (o.get("status") or "").strip().lower()

        if status == "available":
            overview[b]["available"] += 1
        else:
            overview[b]["reserved"] += 1

        overview[b]["total"] += 1

    return overview
