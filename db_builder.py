import sqlite3
import csv
import os

import re

def clean_brma(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", value, flags=re.UNICODE)
    value = value.replace("\u00A0", " ")
    return value.strip().upper()


def normalise(p):
    return p.replace(" ", "").upper().strip()

def build_database(csv_path, db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Dictionary tables
    cur.execute("CREATE TABLE brma_dict (id INTEGER PRIMARY KEY, name TEXT UNIQUE);")
    cur.execute("CREATE TABLE country_dict (id INTEGER PRIMARY KEY, code TEXT UNIQUE);")
    cur.execute("CREATE TABLE postcodes (pcd TEXT PRIMARY KEY, brma_id INTEGER, country_id INTEGER, FOREIGN KEY(brma_id) REFERENCES brma_dict(id), FOREIGN KEY(country_id) REFERENCES country_dict(id));")

    print("BRMA DICT SCHEMA:")
    for row in cur.execute("PRAGMA table_info(brma_dict)"):
        print(row)

    print("COUNTRY DICT SCHEMA:")
    for row in cur.execute("PRAGMA table_info(country_dict)"):
        print(row)

    print("POSTCODES SCHEMA:")
    for row in cur.execute("PRAGMA table_info(postcodes)"):
        print(row)

    brma_cache = {}
    country_cache = {}
    
    skipped_rows = []
    fallback_mode = "placeholder"  # options: "skip", "placeholder", "use_code"

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pcd = normalise(row["PCD"])
            brma_code = row["brma"].strip()
            brma_name = clean_brma(row["brma_name"])
            country = row["country"].strip().upper()
            
            # Handle missing BRMA name
            if not brma_name:
                reason = (
                    f"Missing BRMA name for postcode={pcd}, "
                    f"brma_code={brma_code}, raw_name={repr(row['brma_name'])}"
                )
                skipped_rows.append(reason)

                if fallback_mode == "skip":
                    continue
                elif fallback_mode == "placeholder":
                    brma_name = "UNKNOWN BRMA"
                elif fallback_mode == "use_code":
                    brma_name = f"BRMA {brma_code}"

            # Insert BRMA
            if brma_name not in brma_cache:
                cur.execute("INSERT INTO brma_dict (name) VALUES (?)", (brma_name,))
                brma_cache[brma_name] = cur.lastrowid

            # Insert country
            if country not in country_cache:
                cur.execute("INSERT INTO country_dict (code) VALUES (?)", (country,))
                country_cache[country] = cur.lastrowid

            # Insert postcode row
            cur.execute(
                "INSERT OR REPLACE INTO postcodes (pcd, brma_id, country_id) VALUES (?, ?, ?)",
                (pcd, brma_cache[brma_name], country_cache[country])
            )

    # Write skipped rows log
    if skipped_rows:
        log_path = os.path.join("app_data", "skipped_rows.log")
        with open(log_path, "w", encoding="utf-8") as log:
            for line in skipped_rows:
                log.write(line + "\n")

        print(f"Skipped {len(skipped_rows)} rows. Details written to {log_path}")
    else:
        print("No rows were skipped.")

    conn.commit()
    conn.execute("VACUUM")
    conn.close()
