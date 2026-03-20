import csv
import sqlite3
import os

def normalise(pc):
    return pc.replace(" ", "").upper()

def build_database(csv_path, db_path):
    if os.path.exists(db_path):
        return  # DB already exists

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE postcodes (
            postcode TEXT PRIMARY KEY,
            brma TEXT,
            brma_name TEXT
        )
    """)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        rows = []
        for row in reader:
            pc = normalise(row["PCD"])
            brma = row["brma"]
            brma_name = row["brma_name"]
            rows.append((pc, brma, brma_name))

        cur.executemany("""
            INSERT INTO postcodes (postcode, brma, brma_name)
            VALUES (?, ?, ?)
        """, rows)

    cur.execute("CREATE INDEX idx_postcode ON postcodes(postcode)")
    conn.commit()
    conn.close()
