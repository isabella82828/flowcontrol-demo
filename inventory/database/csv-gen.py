import csv
import pyodbc

SERVER   = "ORTDOCSQLSVAPRD"
DATABASE = "SK_TDOC"
DRIVER   = "SQL Server"
MDRD_STOCK_ID = 1005

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

output_file = "mdrd_screw_inventory.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"Done! {len(rows)} rows written to {output_file}")