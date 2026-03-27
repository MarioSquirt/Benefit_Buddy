import os
import csv
import time
import bisect
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IDX_PATH = os.path.join(BASE_DIR, "postcodes.idx")
DATA_PATH = os.path.join(BASE_DIR, "postcodes_data.bin")
CSV_PATH = os.path.join(BASE_DIR, "..", "..", "data", "pcode_brma_lookup_clean.csv")
CSV_PATH = os.path.normpath(CSV_PATH)

def normalise_postcode(p):
    return p.replace(" ", "").upper().strip()

def load_idx():
    with open(IDX_PATH, "rb") as f:
        return f.read()

def load_data():
    with open(DATA_PATH, "rb") as f:
        return f.read()

def reconstruct_all_postcodes(idx_bytes):
    postcodes = []
    pos = 0
    prev = ""
    total = 2936738

    for _ in range(total):
        prefix_len = idx_bytes[pos]
        suffix_len = idx_bytes[pos + 1]
        pos += 2

        suffix = idx_bytes[pos:pos + suffix_len].decode("ascii")
        pos += suffix_len

        postcode = prev[:prefix_len] + suffix
        postcodes.append(postcode)
        prev = postcode

    return postcodes

def validate_fast():
    print("Loading compact files...")
    idx_bytes = load_idx()
    data_bytes = load_data()

    print("Reconstructing all postcodes (one-time)...")
    start = time.time()
    all_postcodes = reconstruct_all_postcodes(idx_bytes)
    end = time.time()
    print(f"Reconstruction complete in {round(end - start, 2)} seconds")

    print("Loading CSV for validation...")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("Validating using bisect...")
    start = time.time()
    errors = 0

    for i, row in enumerate(rows):
        pcd = normalise_postcode(row["PCD"])

        idx = bisect.bisect_left(all_postcodes, pcd)
        if idx >= len(all_postcodes) or all_postcodes[idx] != pcd:
            print("ERROR: Not found:", pcd)
            errors += 1
            continue

        if i % 500000 == 0:
            print(f"Checked {i} rows...")

    end = time.time()

    print("\nValidation complete.")
    print("Errors:", errors)
    print("Time:", round(end - start, 2), "seconds")

def load_dictionaries():
    with open(os.path.join(BASE_DIR, "brma_dict.json"), "r", encoding="utf-8") as f:
        brma_dict = json.load(f)
    with open(os.path.join(BASE_DIR, "country_dict.json"), "r", encoding="utf-8") as f:
        country_dict = json.load(f)

    brma_rev = {v: k for k, v in brma_dict.items()}
    country_rev = {v: k for k, v in country_dict.items()}

    return brma_rev, country_rev

def load_brma_names():
    with open(os.path.join(BASE_DIR, "brma_names.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def lookup_postcode(pcd, all_postcodes, data_bytes, brma_rev, country_rev, brma_names):
    pcd = normalise_postcode(pcd)

    idx = bisect.bisect_left(all_postcodes, pcd)
    if idx >= len(all_postcodes) or all_postcodes[idx] != pcd:
        return None

    b_id = data_bytes[idx * 2]
    c_id = data_bytes[idx * 2 + 1]

    brma_code = brma_rev[b_id]
    country_code = country_rev[c_id]

    return {
        "postcode": pcd,
        "brma_code": brma_code,
        "brma_name": brma_names.get(brma_code, brma_code),
        "country": country_code
    }

if __name__ == "__main__":
    validate_fast()

    print("\n--- Manual lookup test ---")
    brma_rev, country_rev = load_dictionaries()
    brma_names = load_brma_names()

    idx_bytes = load_idx()
    data_bytes = load_data()
    all_postcodes = reconstruct_all_postcodes(idx_bytes)

    for test_pcd in ["AB101AA", "SW1A1AA", "ZE39XP"]:
        result = lookup_postcode(test_pcd, all_postcodes, data_bytes, brma_rev, country_rev, brma_names)
        print(test_pcd, "→", result)
