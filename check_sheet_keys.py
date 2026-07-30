import requests
import csv
import io

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQhJ14Fz-jQmorjsI3LYacfF-URCZ_vdh9vKiv0arRSri8PSsmkslChsUWKkPTyD5hXQX1A_gQO_8cA/"
    "pub?gid=0&single=true&output=csv"
)

def check_sheet_keys(order_id):
    response = requests.get(SHEET_CSV_URL, timeout=30)
    response.raise_for_status()
    content = response.content.decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(content)))
    
    for row in rows:
        tr = row.get("track_order") or row.get("SC Order No/Track ID/CSRM No")
        if tr == order_id:
            print("Found in Sheet:")
            for k, v in row.items():
                print(f"{k}: '{v}'")
            break

if __name__ == "__main__":
    check_sheet_keys('AOi4260401123616348386c80')
