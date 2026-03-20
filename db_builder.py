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

    # Correct schema matching your CSV + lookup needs
    cur.execute("""
        CREATE TABLE postcodes (
            postcode TEXT PRIMARY KEY,   -- PCD (normalised)
            pcds TEXT,                   -- PCDS (full formatted postcode)
            brma TEXT,
            brma_name TEXT,
            country TEXT
        )
    """)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pc = normalise(row["PCD"])       # main postcode (no spaces)
            pcds = normalise(row["PCDS"])    # formatted postcode
            brma = row["brma"].strip()
            brma_name = row["brma_name"].strip()
            country = row["country"].strip()

            cur.execute(
                "INSERT INTO postcodes (postcode, pcds, brma, brma_name, country) VALUES (?, ?, ?, ?, ?)",
                (pc, pcds, brma, brma_name, country)
            )

    cur.execute("CREATE INDEX idx_postcode ON postcodes(postcode)")
    conn.commit()
    conn.close()

