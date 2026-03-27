import bisect
import json
from kivy.resources import resource_find

# ============================================================
# Helpers to load packaged files safely on Android
# ============================================================

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

# ============================================================
# Globals (lazy-loaded)
# ============================================================

idx_bytes = None
data_bytes = None
all_postcodes = None
brma_dict = None
country_dict = None
brma_names = None
brma_rev = None
country_rev = None

# ============================================================
# Normalisation
# ============================================================

def normalise_postcode(p):
    return p.replace(" ", "").upper().strip()

# ============================================================
# Reconstruct postcode list from compressed index
# ============================================================

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

# ============================================================
# Public loader (called from DisclaimerScreen thread)
# ============================================================

def load_all_postcode_data(progress=None, status=None):
    """
    Loads all postcode data with optional progress + status callbacks.
    Designed to run in a background thread.
    """

    global idx_bytes, data_bytes, all_postcodes
    global brma_dict, country_dict, brma_names
    global brma_rev, country_rev

    # 1) Load index
    if status: status("Loading postcode index…")
    idx_bytes = load_binary("postcodes.idx")
    if progress: progress(0.10)

    # 2) Load data
    if status: status("Loading postcode data…")
    data_bytes = load_binary("postcodes_data.bin")
    if progress: progress(0.20)

    # 3) Reconstruct postcodes (heavy step)
    if status: status("Reconstructing postcodes…")
    all_postcodes = reconstruct_all_postcodes(idx_bytes)
    if progress: progress(0.80)

    # 4) Load dictionaries
    if status: status("Loading BRMA dictionaries…")
    brma_dict = load_json("brma_dict.json")
    country_dict = load_json("country_dict.json")
    brma_names = load_json("brma_names.json")

    # Reverse lookup maps
    brma_rev = {v: k for k, v in brma_dict.items()}
    country_rev = {v: k for k, v in country_dict.items()}

    if progress: progress(1.0)
    if status: status("Postcode data ready")

# ============================================================
# Public lookup function
# ============================================================

def lookup_postcode(pcd):
    if all_postcodes is None:
        raise RuntimeError("Postcode data not loaded. Call load_all_postcode_data() first.")

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
