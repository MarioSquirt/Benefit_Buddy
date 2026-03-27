import sqlite3
import csv
import os
import re
import zlib

def clean_brma(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", value, flags=re.UNICODE)
    value = value.replace("\u00A0", " ")
    return value.strip().upper()

def normalise(p):
    return p.replace(" ", "").upper().strip()

def build_database(csv_path, db_path):
    print(">>> USING HASH BUILDER WITH BRMA CODE <<<")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Dictionary tables
    cur.execute("CREATE TABLE brma_dict (id INTEGER PRIMARY KEY, name TEXT UNIQUE);")
    cur.execute("CREATE TABLE country_dict (id INTEGER PRIMARY KEY, code TEXT UNIQUE);")

    # Postcodes stored as hash + original text
    cur.execute("""
        CREATE TABLE postcodes (
            pcd_hash INTEGER,
            pcd TEXT,
            brma_id INTEGER,
            country_id INTEGER,
            FOREIGN KEY(brma_id) REFERENCES brma_dict(id),
            FOREIGN KEY(country_id) REFERENCES country_dict(id)
        );
    """)

    # Unique index on hash (not primary key)
    cur.execute("CREATE INDEX idx_postcodes_hash ON postcodes(pcd_hash);")

    brma_cache = {}
    country_cache = {}

    skipped_rows = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pcd = normalise(row["PCD"])
            pcd_hash = zlib.crc32(pcd.encode("ascii"))

            brma_code = row["brma"].strip().upper()
            country = row["country"].strip().upper()

            # Insert BRMA code
            if brma_code not in brma_cache:
                cur.execute("INSERT INTO brma_dict (name) VALUES (?)", (brma_code,))
                brma_cache[brma_code] = cur.lastrowid

            # Insert country code
            if country not in country_cache:
                cur.execute("INSERT INTO country_dict (code) VALUES (?)", (country,))
                country_cache[country] = cur.lastrowid

            # Insert postcode row
            cur.execute(
                "INSERT INTO postcodes (pcd_hash, pcd, brma_id, country_id) VALUES (?, ?, ?, ?)",
                (pcd_hash, pcd, brma_cache[brma_code], country_cache[country])
            )

    if skipped_rows:
        log_path = os.path.join("app_data", "skipped_rows.log")
        with open(log_path, "w", encoding="utf-8") as log:
            for line in skipped_rows:
                log.write(line + "\n")
        print(f"Skipped {len(skipped_rows)} rows. Details written to {log_path}")
    else:
        print("No rows were skipped.")

    conn.commit()

    # Ensure vacuum can shrink the file
    cur.execute("PRAGMA journal_mode=DELETE;")
    conn.commit()

    # Shrink the file
    cur.execute("VACUUM;")
    conn.commit()

    conn.close()
