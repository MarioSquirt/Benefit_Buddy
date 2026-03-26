from db_builder import build_database
import os

csv_path = os.path.join("data", "pcode_brma_lookup_clean.csv")
db_path = os.path.join("app_data", "postcodes.db")

build_database(csv_path, db_path)
print("Database built:", db_path)
