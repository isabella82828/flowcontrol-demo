import csv
import pyodbc
import os

SERVER        = "ORTDOCSQLSVAPRD"
DATABASE      = "SK_TDOC"
DRIVER        = "SQL Server"
MDRD_STOCK_ID = 1005

def export_inventory_to_shared_folder(shared_root: str) -> tuple[bool, str]:
    output_path = os.path.join(shared_root, "mdrd_screw_inventory.csv")

    try:
        conn_str = (
            f"DRIVER={{{DRIVER}}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.ITEMKEYID, i.ITEMITEM, i.ITEMTEXT, i.ITEMSUPPLIERNO,
                s.STOONSTOCK, s.STOMAXCOUNT, s.STOMINCOUNT, s.STOPLACEMENT
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
        """, MDRD_STOCK_ID)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        os.makedirs(shared_root, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        return True, f"Inventory exported ({len(rows)} rows) to:\n{output_path}"

    except Exception as e:
        return False, f"Inventory export failed: {e}"