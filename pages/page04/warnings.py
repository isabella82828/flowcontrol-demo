from tkinter import messagebox

def confirm_soft_stop(missing_by_tab: dict) -> bool:
    lines = []
    for tab, fields in missing_by_tab.items():
        lines.append(f"{tab}:\n  - " + "\n  - ".join(fields))

    msg = (
        "Some required radiographic fields are missing:\n\n"
        + "\n\n".join(lines)
        + "\n\nYou can still continue, but recommendations may be less accurate.\nContinue?"
    )
    return messagebox.askyesno("Incomplete Radiographic Data", msg)
