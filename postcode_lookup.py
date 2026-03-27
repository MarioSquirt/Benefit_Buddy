import bisect
import json
from kivy.resources import resource_find

# --- Helpers to load packaged files safely on Android ---

def load_binary(name):
    path = resource_find(f"app_data/postcodes/{name}")
    if not path:
        raise FileNotFoundError(f"Missing packaged file: {name}")
    with open(path, "rb") as f:
        return f.read()

def load_json(name):
    path = resource_find(f"app_data/postcodes/{name}")
    if not path:
        raise FileNotFoundError(f"Missing packaged file: {name}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Normalisation ---
def normalise_postcode(p):
    return p.replace(" ", "").upper().strip()

# --- Load all data at startup (Android-safe) ---
idx_bytes = load_binary("postcodes.idx")
data_bytes = load_binary("postcodes_data.bin")

brma_dict = load_json("brma_dict.json")
country_dict = load_json("country_dict.json")
brma_names = load_json("brma_names.json")

# Reverse dictionaries: ID → code
brma_rev = {v: k for k, v in brma_dict.items()}
country_rev = {v: k for k, v in country_dict.items()}

# --- Reconstruct all postcodes ---
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

all_postcodes = reconstruct_all_postcodes(idx_bytes)

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
