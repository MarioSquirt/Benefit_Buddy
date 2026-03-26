import csv

INPUT = "data/pcode_brma_lookup.csv"
OUTPUT = "data/pcode_brma_lookup_clean.csv"

def normalise_postcode(p):
    return p.replace(" ", "").upper().strip()

def normalise_text(t):
    return t.strip().upper()

def normalise_country(c):
    c = c.strip().upper()
    if c.startswith("E"): return "E"
    if c.startswith("S"): return "S"
    if c.startswith("W"): return "W"
    if c.startswith("N"): return "N"
    return c

seen = set()

with open(INPUT, newline="", encoding="utf-8") as fin, \
     open(OUTPUT, "w", newline="", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)
    writer = csv.writer(fout)

    # Only keep the essential columns
    writer.writerow(["country", "PCD", "brma", "brma_name"])

    for row in reader:
        pcd = normalise_postcode(row["PCD"])
        brma = normalise_text(row["brma"])
        brma_name = normalise_text(row["brma_name"])
        country = normalise_country(row["country"])

        # Deduplicate by postcode + BRMA + country
        key = (pcd, brma, country)
        if key in seen:
            continue
        seen.add(key)

        writer.writerow([country, pcd, brma, brma_name])

print("Cleaned CSV written to:", OUTPUT)
