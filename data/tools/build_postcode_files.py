import csv
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "..", "data", "pcode_brma_lookup_clean.csv")
CSV_PATH = os.path.normpath(CSV_PATH)

def normalise_postcode(p):
    return p.replace(" ", "").upper().strip()

def load_and_sort_postcodes():
    postcodes = []
    brma_list = []
    country_list = []
    brma_name_map = {}

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pcd = normalise_postcode(row["PCD"])
            brma = row["brma"].strip().upper()
            country = row["country"].strip().upper()

            # If your CSV has a BRMA name column, change this key accordingly
            # If not, the BRMA code will be used as the name (safe fallback)
            brma_name = row.get("brma_name", brma).strip()

            postcodes.append(pcd)
            brma_list.append(brma)
            country_list.append(country)

            # Build BRMA code → BRMA name mapping
            if brma not in brma_name_map:
                brma_name_map[brma] = brma_name

    # Sort by postcode (keeping BRMA/country aligned)
    combined = list(zip(postcodes, brma_list, country_list))
    combined.sort(key=lambda x: x[0])

    postcodes, brma_list, country_list = zip(*combined)

    return list(postcodes), list(brma_list), list(country_list), brma_name_map

def build_compact_files(postcodes, brma_list, country_list, brma_name_map):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    idx_path = os.path.join(base_dir, "postcodes.idx")
    data_path = os.path.join(base_dir, "postcodes_data.bin")
    brma_dict_path = os.path.join(base_dir, "brma_dict.json")
    country_dict_path = os.path.join(base_dir, "country_dict.json")
    brma_names_path = os.path.join(base_dir, "brma_names.json")

    print("\nWriting compact postcode index:", idx_path)

    with open(idx_path, "wb") as f:
        prev = ""
        for p in postcodes:
            prefix_len = 0
            max_len = min(len(prev), len(p))
            while prefix_len < max_len and prev[prefix_len] == p[prefix_len]:
                prefix_len += 1

            suffix = p[prefix_len:]

            f.write(bytes([prefix_len]))
            f.write(bytes([len(suffix)]))
            f.write(suffix.encode("ascii"))

            prev = p

    print("postcodes.idx written.")

    print("\nWriting BRMA/country data:", data_path)

    brma_dict = {}
    country_dict = {}

    brma_id_list = []
    country_id_list = []

    for brma, country in zip(brma_list, country_list):
        if brma not in brma_dict:
            brma_dict[brma] = len(brma_dict)

        if country not in country_dict:
            country_dict[country] = len(country_dict)

        brma_id_list.append(brma_dict[brma])
        country_id_list.append(country_dict[country])

    with open(data_path, "wb") as f:
        for b_id, c_id in zip(brma_id_list, country_id_list):
            f.write(bytes([b_id]))
            f.write(bytes([c_id]))

    print("postcodes_data.bin written.")

    # Write BRMA and country dictionaries
    with open(brma_dict_path, "w", encoding="utf-8") as f:
        json.dump(brma_dict, f, indent=2)

    with open(country_dict_path, "w", encoding="utf-8") as f:
        json.dump(country_dict, f, indent=2)

    # NEW: write BRMA code → BRMA name mapping
    with open(brma_names_path, "w", encoding="utf-8") as f:
        json.dump(brma_name_map, f, indent=2)

    print("Dictionaries written.")
    print("\n--- Compact file build complete ---\n")

if __name__ == "__main__":
    print("Loading and sorting postcodes...")
    postcodes, brma_list, country_list, brma_name_map = load_and_sort_postcodes()

    print("Total postcodes loaded:", len(postcodes))
    print("First 5:", postcodes[:5])
    print("Last 5:", postcodes[-5:])
    print("Done loading.\n")

    build_compact_files(postcodes, brma_list, country_list, brma_name_map)
