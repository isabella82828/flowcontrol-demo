import pyodbc

conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=ORTDOCSQLSVAPRD;"
    "DATABASE=SK_TDOC;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        i.ITEMITEM, i.ITEMTEXT,
        s.STOONSTOCK, s.STOSTOKKEYID, st.STOKNAME,
        s.STOPLACEMENT
    FROM dbo.TITEM i
    JOIN dbo.TSTOCK s ON s.STOREFITEMKEYID = i.ITEMKEYID
    JOIN dbo.TSTOCKS st ON st.STOKKEYID = s.STOSTOKKEYID
    WHERE i.ITEMITEM = 'S-05609'
""")
for row in cursor.fetchall():
    print(row)

conn.close()