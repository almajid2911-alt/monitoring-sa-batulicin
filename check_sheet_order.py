import requests
import csv
import io

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQhJ14Fz-jQmorjsI3LYacfF-URCZ_vdh9vKiv0arRSri8PSsmkslChsUWKkPTyD5hXQX1A_gQO_8cA/"
    "pub?gid=0&single=true&output=csv"
)

def fetch_sheet_rows():
    response = requests.get(SHEET_CSV_URL, timeout=30)
    response.raise_for_status()
    content = response.content.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(content)))

rows = fetch_sheet_rows()
print(f"Total rows in sheet: {len(rows)}")

target_id = "AOi4260407093146766c19260"
partial = "9260"
found = False

for r in rows:
    track_order = r.get("track_order") or r.get("SC Order No/Track ID/CSRM No", "")
    if target_id in track_order or target_id.lower() in track_order.lower() or partial in track_order:
        print(f"\nFound in sheet!")
        print(f"track_order: '{track_order}'")
        print(f"Status: '{r.get('Status')}'")
        print(f"status morning: '{r.get('status morning') or r.get('Status Morning')}'")
        print(f"TIM: '{r.get('TIM')}'")
        found = True

if not found:
    print(f"\nOrder {target_id} NOT FOUND in the Google Sheet!")
