import os
import bisect
import json

BASE_DIR = os.path.join(os.path.dirname(__file__), "app_data", "experimental_lookup")

IDX_PATH = os.path.join(BASE_DIR, "postcodes.idx")
DATA_PATH = os.path.join(BASE_DIR, "postcodes_data.bin")
BRMA_DICT_PATH = os.path.join(BASE_DIR, "brma_dict.json")
COUNTRY_DICT_PATH = os.path.join(BASE_DIR, "country_dict.json")
BRMA_NAMES_PATH = os.path.join(BASE_DIR, "brma_names.json")

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
    total = 2936738  # fixed count

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

# --- Load everything once at app startup ---
idx_bytes = load_idx()
data_bytes = load_data()
all_postcodes = reconstruct_all_postcodes(idx_bytes)

with open(BRMA_DICT_PATH, "r", encoding="utf-8") as f:
    brma_dict = json.load(f)
with open(COUNTRY_DICT_PATH, "r", encoding="utf-8") as f:
    country_dict = json.load(f)
with open(BRMA_NAMES_PATH, "r", encoding="utf-8") as f:
    brma_names = json.load(f)

# Reverse dictionaries: ID → code
brma_rev = {v: k for k, v in brma_dict.items()}
country_rev = {v: k for k, v in country_dict.items()}

# --- Public lookup function ---
def lookup_postcode(pcd):
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
