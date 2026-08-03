from __future__ import annotations

import csv
import io
import json
import os
import re
import threading
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_order = db.Column(db.String(100), unique=True, nullable=False)
    tim = db.Column(db.String(100))
    workorder = db.Column(db.String(100))
    odc = db.Column(db.String(100))
    status = db.Column(db.String(100))
    status_morning = db.Column(db.String(100))
    catatan = db.Column(db.Text)
    jam_re = db.Column(db.String(50))
    jam_ps = db.Column(db.String(50))
    status_date_raw = db.Column(db.String(100))
    status_date_parsed = db.Column(db.String(20))
    date_created_raw = db.Column(db.String(100))
    date_created_parsed = db.Column(db.String(20))
    date_modified_raw = db.Column(db.String(100))
    date_modified_parsed = db.Column(db.String(20))
    crm_order_type = db.Column(db.String(100))
    product_name = db.Column(db.String(255))
    tgl_ps = db.Column(db.String(50))
    tgl_ps_parsed = db.Column(db.String(20))
    workzone = db.Column(db.String(100))
    dispatch_date = db.Column(db.String(20)) # New field for DISPATCH column
    kordinat = db.Column(db.String(100))
    wilsus = db.Column(db.String(100))
    eskal_daman = db.Column(db.String(255))
    validasi = db.Column(db.String(100))
    jenis_order = db.Column(db.String(100))
    service_no = db.Column(db.String(100))

    def to_dict(self):
        return {
            "TIM": self.tim,
            "track_order": self.track_order,
            "Workorder": self.workorder,
            "ODC": self.odc,
            "Status": self.status,
            "status morning": self.status_morning,
            "Catatan": self.catatan,
            "Jam re": self.jam_re,
            "Jam PS": self.jam_ps,
            "Status Date": self.status_date_raw,
            "status_date_parsed": self.status_date_parsed,
            "Date Created": self.date_created_raw,
            "date_created_parsed": self.date_created_parsed,
            "Date Modified": self.date_modified_raw,
            "date_modified_parsed": self.date_modified_parsed,
            "crm_order_type": self.crm_order_type,
            "product_name": self.product_name,
            "tgl_ps": self.tgl_ps,
            "tgl_ps_parsed": self.tgl_ps_parsed,
            "workzone": self.workzone,
            "dispatch_date": self.dispatch_date,
            "kordinat": self.kordinat,
            "wilsus": self.wilsus,
            "eskal_daman": self.eskal_daman,
            "validasi": self.validasi,
            "jenis_order": self.jenis_order or "",
            "service_no": self.service_no or ""
        }


def clean_odc_real(dev_name: str | None, odc_real: str | None) -> str:
    # Example: ODP-PGT-FD/030 FD/D02/030.01 -> ODP-PGT-FD/030
    src = (dev_name or "").strip()
    if not src:
        src = (odc_real or "").strip()
    if not src:
        return "-"
    parts = src.split()
    return parts[0] if parts else src


class AssuranceTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident = db.Column(db.String(100), unique=True, nullable=False)
    device_name = db.Column(db.String(255))
    service_no = db.Column(db.String(100))
    workzone = db.Column(db.String(100))
    summary = db.Column(db.Text)
    customer_segment = db.Column(db.String(100))
    reported_date = db.Column(db.String(100))
    customer_type = db.Column(db.String(100))
    guarante_status = db.Column(db.String(100))
    status_garansi = db.Column(db.String(100))
    description_assignment = db.Column(db.String(255))
    booking_date = db.Column(db.String(100))
    hasil_ukur = db.Column(db.String(100))
    redaman = db.Column(db.String(100))
    ttr = db.Column(db.String(100))
    flag = db.Column(db.String(100))
    tim = db.Column(db.String(100))
    odc_real = db.Column(db.String(100))
    wilsus = db.Column(db.String(100))
    status_kawan = db.Column(db.String(100))
    catatan = db.Column(db.Text)
    jam_manja = db.Column(db.String(100))
    tim_insera = db.Column(db.String(100))
    tim_kawan = db.Column(db.String(100))

    def to_dict(self):
        return {
            "incident": self.incident,
            "device_name": self.device_name,
            "odc_clean": clean_odc_real(self.device_name, self.odc_real),
            "service_no": self.service_no,
            "workzone": self.workzone,
            "summary": self.summary,
            "customer_segment": self.customer_segment,
            "reported_date": self.reported_date,
            "customer_type": self.customer_type,
            "guarante_status": self.guarante_status,
            "status_garansi": self.status_garansi,
            "description_assignment": self.description_assignment,
            "booking_date": self.booking_date,
            "hasil_ukur": self.hasil_ukur,
            "redaman": self.redaman,
            "ttr": self.ttr,
            "flag": self.flag,
            "tim": self.tim,
            "odc_real": self.odc_real,
            "wilsus": self.wilsus,
            "status_kawan": self.status_kawan,
            "catatan": self.catatan,
            "jam_manja": self.jam_manja,
            "tim_insera": self.tim_insera,
            "tim_kawan": self.tim_kawan,
        }



SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQhJ14Fz-jQmorjsI3LYacfF-URCZ_vdh9vKiv0arRSri8PSsmkslChsUWKkPTyD5hXQX1A_gQO_8cA/"
    "pub?gid=0&single=true&output=csv"
)

ASSURANCE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/1gTlZxWfKlCENvDVEDKS_qHrLqNLBXsFsy0utTv2u_hY/"
    "export?format=csv&gid=422466574"
)



def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def normalize_upper(value: str | None) -> str:
    return normalize_text(value).upper()


def fetch_sheet_rows() -> list[dict[str, str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(SHEET_CSV_URL, headers=headers, timeout=25)
    response.raise_for_status()
    content = response.content.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(content)))


def is_truthy_text(value: str) -> bool:
    return normalize_text(value) != ""


def is_empty_status_m(value: str | None) -> bool:
    s = normalize_upper(value)
    return s in {"", "-", "NONE", "EMPTY", "KOSONG"}


def parse_sheet_date(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""

    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text[:10] if len(text) >= 10 else text


def clean_coordinates(coord_str: str) -> str:
    if not coord_str or str(coord_str).strip() in {"-", "", "None"}:
        return ""
    s = str(coord_str).strip()
    match = re.search(r'(-?\d+)[,\.](\d+)\s*[,\s;:]\s*(1\d+)[,\.](\d+)', s)
    if match:
        lat_int, lat_dec, lng_int, lng_dec = match.groups()
        return f"{lat_int}.{lat_dec},{lng_int}.{lng_dec}"
    match_std = re.search(r'(-?\d+\.\d+)\s*[,\s]\s*(1\d+\.\d+)', s)
    if match_std:
        return f"{match_std.group(1)},{match_std.group(2)}"
    return s.replace(" ", "")

app.jinja_env.filters['clean_coords'] = clean_coordinates


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    preferred_statuses = {
        "COMPWORK": 5,
        "WORKFAIL": 4,
        "STARTWORK": 3,
        "VALCOMP": 2,
        "ACTCOMP": 1,
        "VALSTART": 0,
    }
    buckets: dict[str, dict[str, str]] = {}

    for row in rows:
        track_order = normalize_text(row.get("track_order"))
        if not track_order:
            track_order = normalize_text(row.get("SC Order No/Track ID/CSRM No"))
        if not track_order:
            continue

        current = buckets.get(track_order)
        if current is None:
            buckets[track_order] = row
            continue

        current_score = preferred_statuses.get(normalize_upper(current.get("Status")), -1)
        new_score = preferred_statuses.get(normalize_upper(row.get("Status")), -1)
        if new_score >= current_score:
            buckets[track_order] = row

    return list(buckets.values())

def update_if_changed(obj, attr, new_val):
    if getattr(obj, attr) != new_val:
        setattr(obj, attr, new_val)



def match_status(row: dict[str, str], allowed: set[str]) -> bool:
    val = row.get("Status") or row.get("status")
    return normalize_upper(val) in allowed


def match_status_morning(row: dict[str, str], expected: str) -> bool:
    val = row.get("status morning") or row.get("status_morning")
    return normalize_upper(val) == expected.upper()


def get_product_name_normalized(row: dict) -> str:
    product_name = normalize_upper(row.get("product_name") or row.get("Product Name") or "")
    tr_order = normalize_upper(row.get("track_order") or row.get("track_order") or "")
    if not product_name or product_name in {"-", "UNKNOWN", ""}:
        if tr_order.startswith("PDA"):
            return "PDA"
        elif tr_order.startswith("SC"):
            return "INDIBIZ"
        elif tr_order.startswith("TIF"):
            return "VULA"
        elif tr_order.startswith("AO") or tr_order.startswith("MYIR") or tr_order.startswith("IN"):
            return "INDIHOME"
        else:
            return "UNKNOWN"
    return product_name


def filter_by_date(rows: list[dict[str, str]], start_date: str, end_date: str) -> list[dict[str, str]]:
    if not start_date and not end_date:
        return rows

    filtered = []
    for row in rows:
        row_date = parse_sheet_date(row.get("Status Date", ""))
        if start_date and row_date and row_date < start_date:
            continue
        if end_date and row_date and row_date > end_date:
            continue
        if not row_date and (start_date or end_date):
            continue
        filtered.append(row)
    return filtered


def build_summary(all_rows: list[dict[str, str]], total_ps_rows: list[dict[str, str]]) -> dict[str, any]:
    # Categories for summary breakdown
    categories = {
        "ps": [],
        "potensi": [],
        "ogp": [],
        "oke": [],
        "belum": [],
        "undispatch": []
    }

    for row in total_ps_rows:
        if match_status(row, {"COMPWORK"}):
            categories["ps"].append(row)

    for row in all_rows:
        st_up = normalize_upper(row.get("Status"))
        sm_up = normalize_upper(row.get("status morning"))
        # Keywords for Potensi (strictly Actcomp, Valstart, Valcomp and variations)
        potensi_keywords = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP"}
        is_potensi_st = any(v in st_up for v in potensi_keywords)
        is_potensi_sm = any(v in sm_up for v in potensi_keywords)
        
        if is_potensi_st or is_potensi_sm:
            categories["potensi"].append(row)
        
        if match_status_morning(row, "SEDANG DIKERJAKAN"):
            categories["ogp"].append(row)
        
        is_wf_sw = match_status(row, {"WORKFAIL", "STARTWORK"})
        if is_wf_sw:
            status_m = normalize_upper(row.get("status morning"))
            tim = normalize_text(row.get("TIM"))
            
            if status_m == "OKE TARIK":
                categories["oke"].append(row)
            
            if status_m in {"BELUM DIKERJAKAN", ""} and is_truthy_text(tim) and tim != "-":
                categories["belum"].append(row)
            
            if (not is_truthy_text(tim) or tim == "-") and is_empty_status_m(status_m):
                categories["undispatch"].append(row)

    def get_breakdown(rows):
        counter: Counter[str] = Counter()
        for r in rows:
            pname = get_product_name_normalized(r)
            counter[pname] += 1
        return [{"product": k, "count": v} for k, v in counter.most_common()]

    return {
        "total_ps": len(categories["ps"]),
        "total_potensi": len(categories["potensi"]),
        "sedang_ogp": len(categories["ogp"]),
        "oke_tarik": len(categories["oke"]),
        "belum_dikerjakan": len(categories["belum"]),
        "undispatch": len(categories["undispatch"]),
        "total_rows": len(all_rows),
        "ps_breakdown": get_breakdown(categories["ps"]),
        "potensi_breakdown": get_breakdown(categories["potensi"]),
        "ogp_breakdown": get_breakdown(categories["ogp"]),
        "oke_breakdown": get_breakdown(categories["oke"]),
        "belum_breakdown": get_breakdown(categories["belum"]),
        "undispatch_breakdown": get_breakdown(categories["undispatch"])
    }


def build_sisa_pivot(all_source_rows: list[dict[str, str]]) -> dict:
    from collections import defaultdict
    sisa_rows = []
    for r in all_source_rows:
        st_up = normalize_upper(r.get("Status"))
        sm_up = normalize_upper(r.get("status morning"))

        # Filter: Status in STARTWORK, WORKFAIL
        if st_up in {"STARTWORK", "WORKFAIL"}:
            is_sedang = ("SEDANG" in sm_up and "BELUM" not in sm_up)
            is_belum_or_empty = sm_up in {"", "BELUM DIKERJAKAN"}
            if is_sedang or is_belum_or_empty:
                sisa_rows.append(r)

    all_products = set()
    pivot_matrix = defaultdict(lambda: defaultdict(Counter))

    for r in sisa_rows:
        wz = normalize_text(r.get("workzone") or "BELUM ADA")
        wilsus = normalize_text(r.get("wilsus") or "KOTA")
        if not wilsus or wilsus == "-":
            wilsus = "KOTA"
        pname = get_product_name_normalized(r)
        all_products.add(pname)
        pivot_matrix[wz][wilsus][pname] += 1

    sorted_products = sorted(list(all_products))
    sorted_wz = sorted(pivot_matrix.keys())

    formatted_workzones = []
    col_totals = Counter()

    for wz in sorted_wz:
        wz_rows = []
        wz_totals = Counter()
        sorted_wilsus = sorted(pivot_matrix[wz].keys())

        for wilsus in sorted_wilsus:
            counts = pivot_matrix[wz][wilsus]
            row_tot = sum(counts.values())
            p_counts = {p: counts[p] for p in sorted_products}

            for p in sorted_products:
                wz_totals[p] += counts[p]
                col_totals[p] += counts[p]

            wz_rows.append({
                "wilsus": wilsus,
                "product_counts": p_counts,
                "row_total": row_tot
            })

        wz_tot_dict = {p: wz_totals[p] for p in sorted_products}
        formatted_workzones.append({
            "workzone": wz,
            "wilsus_rows": wz_rows,
            "wz_totals": wz_tot_dict,
            "wz_grand_total": sum(wz_totals.values())
        })

    col_totals_dict = {p: col_totals[p] for p in sorted_products}

    return {
        "products": sorted_products,
        "workzones": formatted_workzones,
        "col_totals": col_totals_dict,
        "grand_total": len(sisa_rows)
    }


def build_hour_chart(rows: list[dict[str, str]], column_name: str) -> dict[str, list]:
    counter: Counter[str] = Counter()
    product_counter: Counter[str] = Counter()
    total_count = 0
    for row in rows:
        value = normalize_text(row.get(column_name))
        if not value:
            continue
        counter[value] += 1
        total_count += 1
        
        pname = get_product_name_normalized(row)
        product_counter[pname] += 1

    def sort_key(item: str) -> tuple[int, str]:
        try:
            return (int(item), item)
        except ValueError:
            return (999, item)

    labels = sorted(counter.keys(), key=sort_key)
    values = [counter[label] for label in labels]
    breakdown = [{"product": k, "count": v} for k, v in product_counter.most_common()]
    return {"labels": labels, "values": values, "total": total_count, "breakdown": breakdown}


def build_table_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    table_rows = []
    for row in rows:
        table_rows.append(
            {
                "workzone": normalize_text(row.get("workzone")),
                "tim": normalize_text(row.get("TIM")),
                "track_order": normalize_text(row.get("track_order")),
                "workorder": normalize_text(row.get("Workorder")),
                "odc": normalize_text(row.get("ODC")),
                "status": normalize_text(row.get("Status")),
                "status_morning": normalize_text(row.get("status morning")),
                "catatan": normalize_text(row.get("Catatan")),
                "jam_re": normalize_text(row.get("Jam re")),
                "jam_ps": normalize_text(row.get("Jam PS")),
                "datevalue": parse_sheet_date(row.get("Status Date", "")),
            }
        )
    return table_rows


def sync_orders():
    rows = fetch_sheet_rows()
    deduped_rows = dedupe_rows(rows)
    
    preferred_statuses = {
        "COMPWORK": 5,
        "WORKFAIL": 4,
        "STARTWORK": 3,
        "VALCOMP": 2,
        "ACTCOMP": 1,
        "VALSTART": 0,
    }

    synced_count = 0
    # Fetch existing to handle upsert quickly
    all_db_orders = Order.query.all()
    existing_orders = {o.track_order: o for o in all_db_orders}
    
    # Track IDs that are present in the current sheet sync
    current_sheet_ids = set()
    
    for row_dict in deduped_rows:
        tr_order = normalize_text(row_dict.get("track_order") or row_dict.get("SC Order No/Track ID/CSRM No"))
        if not tr_order:
            continue

        existing = existing_orders.get(tr_order)
        new_status_score = preferred_statuses.get(normalize_upper(row_dict.get("Status")), -1)
        
        parsed_date = parse_sheet_date(row_dict.get("Status Date", ""))
        date_created_val = row_dict.get("Date Created", "")
        parsed_created_date = parse_sheet_date(date_created_val)
        date_modified_val = row_dict.get("Date Modified", "")
        parsed_modified_date = parse_sheet_date(date_modified_val)
        parsed_tgl_ps = parse_sheet_date(row_dict.get("tgl ps", ""))
        parsed_dispatch = parse_sheet_date(row_dict.get("DISPATCH", ""))

        if existing:
            update_if_changed(existing, "tim", normalize_text(row_dict.get("TIM") or row_dict.get("tim")))
            update_if_changed(existing, "workorder", normalize_text(row_dict.get("Workorder")))
            update_if_changed(existing, "odc", normalize_text(row_dict.get("ODC")))
            update_if_changed(existing, "status", normalize_text(row_dict.get("Status")))
            update_if_changed(existing, "status_morning", normalize_text(row_dict.get("status morning") or row_dict.get("Status Morning") or row_dict.get("status_morning")))
            update_if_changed(existing, "catatan", normalize_text(row_dict.get("Catatan")))
            update_if_changed(existing, "jam_re", normalize_text(row_dict.get("Jam re")))
            update_if_changed(existing, "jam_ps", normalize_text(row_dict.get("Jam PS")))
            update_if_changed(existing, "status_date_raw", normalize_text(row_dict.get("Status Date")))
            update_if_changed(existing, "status_date_parsed", parsed_date)
            update_if_changed(existing, "date_created_raw", normalize_text(date_created_val))
            update_if_changed(existing, "date_created_parsed", parsed_created_date)
            update_if_changed(existing, "date_modified_raw", normalize_text(date_modified_val))
            update_if_changed(existing, "date_modified_parsed", parsed_modified_date)
            update_if_changed(existing, "crm_order_type", normalize_text(row_dict.get("CRM Order Type")))
            update_if_changed(existing, "product_name", normalize_text(row_dict.get("Product Name")))
            update_if_changed(existing, "tgl_ps", normalize_text(row_dict.get("tgl ps")))
            update_if_changed(existing, "tgl_ps_parsed", parsed_tgl_ps)
            update_if_changed(existing, "workzone", normalize_text(row_dict.get("Workzone")))
            update_if_changed(existing, "dispatch_date", parsed_dispatch)
            update_if_changed(existing, "kordinat", clean_coordinates(normalize_text(row_dict.get("KORDINAT") or row_dict.get("kordinat"))))
            update_if_changed(existing, "wilsus", normalize_text(row_dict.get("Wilsus") or row_dict.get("wilsus")))
            update_if_changed(existing, "eskal_daman", normalize_text(row_dict.get("Eskal daman") or row_dict.get("eskal_daman")))
            update_if_changed(existing, "validasi", normalize_text(row_dict.get("cek qc") or row_dict.get("VALIDASI") or row_dict.get("validasi")))
            update_if_changed(existing, "jenis_order", normalize_text(row_dict.get("jenis order") or row_dict.get("Jenis Order")).upper())
            update_if_changed(existing, "service_no", normalize_text(row_dict.get("Service No.") or row_dict.get("Service No") or row_dict.get("service_no")))
        else:
            new_order = Order(
                track_order=tr_order,
                tim=normalize_text(row_dict.get("TIM") or row_dict.get("tim")),
                workorder=normalize_text(row_dict.get("Workorder")),
                odc=normalize_text(row_dict.get("ODC")),
                status=normalize_text(row_dict.get("Status")),
                # Robust mapping for status morning
                status_morning=normalize_text(row_dict.get("status morning") or row_dict.get("Status Morning") or row_dict.get("status_morning")),
                catatan=normalize_text(row_dict.get("Catatan")),
                jam_re=normalize_text(row_dict.get("Jam re")),
                jam_ps=normalize_text(row_dict.get("Jam PS")),
                status_date_raw=normalize_text(row_dict.get("Status Date")),
                status_date_parsed=parsed_date,
                date_created_raw=normalize_text(date_created_val),
                date_created_parsed=parsed_created_date,
                date_modified_raw=normalize_text(date_modified_val),
                date_modified_parsed=parsed_modified_date,
                crm_order_type=normalize_text(row_dict.get("CRM Order Type")),
                product_name=normalize_text(row_dict.get("Product Name")),
                tgl_ps=normalize_text(row_dict.get("tgl ps")),
                tgl_ps_parsed=parsed_tgl_ps,
                workzone=normalize_text(row_dict.get("Workzone")),
                dispatch_date=parsed_dispatch,
                kordinat=clean_coordinates(normalize_text(row_dict.get("KORDINAT") or row_dict.get("kordinat"))),
                wilsus=normalize_text(row_dict.get("Wilsus") or row_dict.get("wilsus")),
                eskal_daman=normalize_text(row_dict.get("Eskal daman") or row_dict.get("eskal_daman")),
                validasi=normalize_text(row_dict.get("cek qc") or row_dict.get("VALIDASI") or row_dict.get("validasi")),
                jenis_order=normalize_text(row_dict.get("jenis order") or row_dict.get("Jenis Order")).upper(),
                service_no=normalize_text(row_dict.get("Service No.") or row_dict.get("Service No") or row_dict.get("service_no"))
            )
            db.session.add(new_order)
            existing_orders[tr_order] = new_order
        
        current_sheet_ids.add(tr_order)
        synced_count += 1
        
    # Identify and delete "ghost" records no longer in the Google Sheet
    db_ids = set(existing_orders.keys())
    ids_to_delete = db_ids - current_sheet_ids
    
    if ids_to_delete:
        print(f"Sync: Deleting {len(ids_to_delete)} ghost records not found in Google Sheet.")
        Order.query.filter(Order.track_order.in_(ids_to_delete)).delete(synchronize_session=False)

    db.session.commit()
    return synced_count


def sync_assurance_tickets() -> int:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(ASSURANCE_SHEET_CSV_URL, headers=headers, timeout=25)
        resp.raise_for_status()
        content = resp.content.decode('utf-8-sig', errors='replace')
        
        rows = list(csv.DictReader(io.StringIO(content)))
        valid_rows = [r for r in rows if normalize_text(r.get("INCIDENT"))]


        existing_tickets = {t.incident: t for t in AssuranceTicket.query.all()}
        seen_incidents = set()
        synced_count = 0

        for r in valid_rows:
            inc = normalize_text(r.get("INCIDENT"))
            if not inc or inc in seen_incidents:
                continue
            seen_incidents.add(inc)

            t = existing_tickets.get(inc)
            if not t:
                t = AssuranceTicket(incident=inc)
                db.session.add(t)
                existing_tickets[inc] = t

            update_if_changed(t, "device_name", normalize_text(r.get("DEVICE NAME")))
            update_if_changed(t, "service_no", normalize_text(r.get("SERVICE NO")))
            update_if_changed(t, "workzone", normalize_text(r.get("WORKZONE")))
            update_if_changed(t, "summary", normalize_text(r.get("SUMMARY")))
            update_if_changed(t, "customer_segment", normalize_text(r.get("CUSTOMER SEGMENT")))
            update_if_changed(t, "reported_date", normalize_text(r.get("REPORTED DATE")))
            update_if_changed(t, "customer_type", normalize_text(r.get("CUSTOMER TYPE")))
            update_if_changed(t, "guarante_status", normalize_text(r.get("GUARANTE STATUS")))
            update_if_changed(t, "status_garansi", normalize_text(r.get("STATUS GARANSI")))
            update_if_changed(t, "description_assignment", normalize_text(r.get("DESCRIPTION ASSIGMENT")))
            update_if_changed(t, "booking_date", normalize_text(r.get("BOOKING DATE")))
            update_if_changed(t, "hasil_ukur", normalize_text(r.get("HASIL UKUR")))
            update_if_changed(t, "redaman", normalize_text(r.get("REDAMAN")))
            update_if_changed(t, "ttr", normalize_text(r.get("TTR")))
            update_if_changed(t, "flag", normalize_text(r.get("FLAG")))
            update_if_changed(t, "tim", normalize_text(r.get("TIM") or r.get("TIM KAWAN")))
            update_if_changed(t, "odc_real", normalize_text(r.get("ODC REAL")))
            update_if_changed(t, "wilsus", normalize_text(r.get("WILSUS")))
            update_if_changed(t, "status_kawan", normalize_text(r.get("STATUS KAWAN")))
            update_if_changed(t, "catatan", normalize_text(r.get("CATATAN")))
            update_if_changed(t, "jam_manja", normalize_text(r.get("JAM MANJA")))
            update_if_changed(t, "tim_insera", normalize_text(r.get("TIM INSERA")))
            update_if_changed(t, "tim_kawan", normalize_text(r.get("TIM KAWAN")))

            synced_count += 1


        db_incidents = set(existing_tickets.keys())
        ids_to_delete = db_incidents - seen_incidents
        if ids_to_delete:
            AssuranceTicket.query.filter(AssuranceTicket.incident.in_(ids_to_delete)).delete(synchronize_session=False)

        db.session.commit()
        return synced_count
    except Exception as e:
        print(f"Error syncing assurance tickets: {e}")
        return 0


def get_jenis_tiket(r: dict) -> str:
    summary = normalize_upper(r.get("summary"))
    cust_type = normalize_upper(r.get("customer_type"))
    if "SQM" in summary: return "SQM"
    if "UNSPEC" in summary or "UNSPEK" in summary: return "UNSPEC"
    if "GAMAS" in summary: return "GAMAS"
    if "GOLD" in cust_type: return "HVC Gold"
    if "DIAMOND" in cust_type: return "HVC Diamond"
    if "PLATINUM" in cust_type: return "HVC Platinum"
    if "REGULER" in cust_type or "REGULAR" in cust_type: return "REGULER"
    return "REGULER"


def parse_ttr_val(val_str: str) -> float:
    if not val_str or str(val_str).strip() in {"-", "", "None"}: return 0.0
    try:
        return float(str(val_str).replace(',', '.').strip())
    except:
        return 0.0


def parse_redaman_val(val_str: str) -> float:
    if not val_str or str(val_str).strip() in {"-", "", "None"}: return 0.0
    try:
        return float(str(val_str).replace(',', '.').strip())
    except:
        return 0.0


def is_gamas_ticket(r: dict) -> bool:
    sum_str = normalize_upper(r.get("summary"))
    cat_str = normalize_upper(r.get("catatan"))
    desc_str = normalize_upper(r.get("description_assignment"))
    ctype_str = normalize_upper(r.get("customer_type"))
    jt_str = normalize_upper(r.get("jenis_tiket"))
    return ("GAMAS" in sum_str) or ("GAMAS" in cat_str) or ("GAMAS" in desc_str) or ("GAMAS" in ctype_str) or ("GAMAS" in jt_str)


def get_is_manja(r: dict) -> str:
    desc = normalize_upper(r.get("description_assignment"))
    return "YES" if "CUSTOMER ASSIGN" in desc else "NO"


def load_assurance_data(sektor: str = "", wilsus: str = "", jenis_tiket: str = "") -> dict:
    query = AssuranceTicket.query
    all_tickets = query.all()
    rows = [t.to_dict() for t in all_tickets]

    for r in rows:
        r["jenis_tiket"] = get_jenis_tiket(r)
        r["is_manja"] = get_is_manja(r)

    all_wilsus = sorted(list(set(normalize_text(t.wilsus) for t in all_tickets if t.wilsus and t.wilsus.strip() != "-")))

    if sektor:
        sektor_map = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }
        allowed_wz = sektor_map.get(sektor.lower())
        if allowed_wz:
            rows = [r for r in rows if normalize_upper(r.get("workzone")) in allowed_wz]

    if wilsus:
        rows = [r for r in rows if normalize_upper(r.get("wilsus")) == normalize_upper(wilsus)]

    if jenis_tiket:
        jt_up = normalize_upper(jenis_tiket)
        if jt_up == "REGULER":
            rows = [r for r in rows if r["jenis_tiket"] not in {"SQM", "UNSPEC", "UNSPEK"}]
        elif jt_up == "SQM":
            rows = [r for r in rows if r["jenis_tiket"] == "SQM" or "SQM" in normalize_upper(r.get("summary"))]
        elif jt_up == "UNSPEC":
            rows = [r for r in rows if r["jenis_tiket"] in {"UNSPEC", "UNSPEK"} or "UNSPEC" in normalize_upper(r.get("summary")) or "UNSPEK" in normalize_upper(r.get("summary"))]
        else:
            rows = [r for r in rows if normalize_upper(r["jenis_tiket"]) == jt_up]



    def parse_ttr_val(val_str: str) -> float:
        if not val_str: return 0.0
        try:
            return float(val_str.replace(',', '.').strip())
        except:
            return 0.0

    def parse_redaman_val(val_str: str) -> float:
        if not val_str or val_str.strip() in {"-", ""}: return 0.0
        try:
            return float(val_str.replace(',', '.').strip())
        except:
            return 0.0

    def is_sqm_or_unspec(summary_str: str) -> bool:
        s = (summary_str or "").upper()
        return ("SQM" in s) or ("UNSPEC" in s) or ("UNSPEK" in s)

    def is_garansi_ticket(r: dict) -> bool:
        if is_sqm_or_unspec(r.get("summary")) or is_sqm_or_unspec(r.get("customer_type")) or is_sqm_or_unspec(r.get("jenis_tiket")):
            return False
        st_g = normalize_upper(r.get("status_garansi"))
        if st_g and ("GARANSI" in st_g or st_g in {"YES", "TRUE", "1", "Y"}):
            return True
        st = normalize_upper(r.get("guarante_status"))
        if not st:
            return False
        if "NOT" in st or "NON" in st or st == "NO":
            return False
        return "GARANSI" in st or "GUARANTEE" in st

    total_saldo = len(rows)

    # Separate rows by Customer Segment
    pl_tsel_rows = [r for r in rows if normalize_upper(r.get("customer_segment")) == "PL-TSEL"]
    rbs_rows = [r for r in rows if normalize_upper(r.get("customer_segment")) == "RBS"]

    rbs_indibiz_count = len(rbs_rows)
    manja_count = sum(1 for r in rows if "CUSTOMER ASSIGN" in normalize_upper(r.get("description_assignment")))
    online_redaman_count = sum(1 for r in rows if normalize_upper(r.get("hasil_ukur")) == "ONLINE" and (13.0 <= abs(parse_redaman_val(r.get("redaman"))) < 25.0 or -25.0 < parse_redaman_val(r.get("redaman")) <= -13.0))

    # PL-TSEL Specific Metrics (excluding SQM & UNSPEC for HVC GOLD, HVC DIAMOND, HVC PLATINUM, REGULER, OSLA)
    hvc_gold_count = sum(1 for r in pl_tsel_rows if "GOLD" in normalize_upper(r.get("customer_type")) and not is_sqm_or_unspec(r.get("summary")))
    hvc_diamond_count = sum(1 for r in pl_tsel_rows if "DIAMOND" in normalize_upper(r.get("customer_type")) and not is_sqm_or_unspec(r.get("summary")))
    hvc_platinum_count = sum(1 for r in pl_tsel_rows if "PLATINUM" in normalize_upper(r.get("customer_type")) and not is_sqm_or_unspec(r.get("summary")))
    reguler_count = sum(1 for r in pl_tsel_rows if ("REGULER" in normalize_upper(r.get("customer_type")) or "REGULAR" in normalize_upper(r.get("customer_type"))) and not is_sqm_or_unspec(r.get("summary")))
    
    garansi_count = sum(1 for r in pl_tsel_rows if is_garansi_ticket(r))
    osla_count = sum(1 for r in pl_tsel_rows if parse_ttr_val(r.get("ttr")) > 12.0 and not is_sqm_or_unspec(r.get("summary")))
    sqm_count = sum(1 for r in pl_tsel_rows if "SQM" in normalize_upper(r.get("summary")))
    unspec_count = sum(1 for r in pl_tsel_rows if "UNSPEC" in normalize_upper(r.get("summary")) or "UNSPEK" in normalize_upper(r.get("summary")))
    gamas_count = sum(1 for r in pl_tsel_rows if is_gamas_ticket(r))
    
    belum_count = sum(1 for r in pl_tsel_rows if normalize_upper(r.get("status_kawan")) in {"", "BELUM DIKERJAKAN"})
    undispatch_count = sum(1 for r in pl_tsel_rows if not is_truthy_text(r.get("tim")) or r.get("tim") == "-")


    # Pivot per Workzone x Status Pengerjaan (Status Kawan)
    wz_pivot = {}
    for r in rows:
        wz = normalize_text(r.get("workzone") or "KOSONG")
        sk = normalize_upper(r.get("status_kawan"))
        if wz not in wz_pivot:
            wz_pivot[wz] = Counter()
        
        if sk == "BELUM DIKERJAKAN":
            wz_pivot[wz]["belum"] += 1
        elif sk in {"BERANGKAT", "TIBA", "SEDANG DIKERJAKAN"}:
            wz_pivot[wz]["proses"] += 1
        elif sk == "PENDING":
            wz_pivot[wz]["pending"] += 1
        else:
            wz_pivot[wz]["unassigned"] += 1

    formatted_wz_pivot = []
    tot_belum = tot_proses = tot_pending = tot_unassigned = tot_grand = 0
    for wz in sorted(wz_pivot.keys()):
        cnt = wz_pivot[wz]
        b = cnt["belum"]
        pr = cnt["proses"]
        pd = cnt["pending"]
        u = cnt["unassigned"]
        t = b + pr + pd + u

        tot_belum += b
        tot_proses += pr
        tot_pending += pd
        tot_unassigned += u
        tot_grand += t

        formatted_wz_pivot.append({
            "workzone": wz,
            "belum": b,
            "proses": pr,
            "pending": pd,
            "unassigned": u,
            "total": t
        })

    # Hasil Ukur Distribution
    hu_counter = Counter()
    for r in rows:
        hu = normalize_upper(r.get("hasil_ukur")) or "BELUM DIUKUR"
        hu_counter[hu] += 1

    # Pivot Workzone & Wilsus x Jenis Tiket (Matching Provisioning Sisa Order Pivot)
    wz_wilsus_pivot_raw = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        wz = normalize_text(r.get("workzone") or "KOSONG")
        wilsus = normalize_text(r.get("wilsus") or "-")
        jenis = r.get("jenis_tiket") or "REGULER"
        wz_wilsus_pivot_raw[wz][wilsus][jenis] += 1

    formatted_wz_wilsus_pivot = []
    grand_jenis_totals = Counter()

    for wz in sorted(wz_wilsus_pivot_raw.keys()):
        wz_subrows = []
        wz_totals = Counter()
        for wilsus in sorted(wz_wilsus_pivot_raw[wz].keys()):
            counts = wz_wilsus_pivot_raw[wz][wilsus]
            wz_totals.update(counts)
            grand_jenis_totals.update(counts)
            wz_subrows.append({
                "wilsus": wilsus,
                "counts": dict(counts),
                "total": sum(counts.values())
            })
        
        formatted_wz_wilsus_pivot.append({
            "workzone": wz,
            "subrows": wz_subrows,
            "wz_totals": dict(wz_totals),
            "wz_grand_total": sum(wz_totals.values())
        })

    # Sorted Assurance Matrix tickets (Workzone, Tim, Wilsus, Incident)
    matrix_tickets = list(rows)
    matrix_tickets.sort(key=lambda x: (
        (x.get("workzone") or "KOSONG").lower(),
        (x.get("tim") or "TANPA TIM").lower(),
        (x.get("wilsus") or "-").lower(),
        (x.get("incident") or "").lower()
    ))

    # Calculate breakdown for Belum Dikerjakan and Undispatch cards
    belum_rows = [r for r in rows if normalize_upper(r.get("status_kawan")) in {"", "BELUM DIKERJAKAN"}]
    c_belum = Counter(r["jenis_tiket"] for r in belum_rows)
    belum_breakdown = [{"jenis": k, "count": v} for k, v in c_belum.most_common()]

    undispatch_rows = [r for r in rows if not r.get("tim") or r.get("tim") == "-"]
    c_undispatch = Counter(r["jenis_tiket"] for r in undispatch_rows)
    undispatch_breakdown = [{"jenis": k, "count": v} for k, v in c_undispatch.most_common()]

    return {
        "total_saldo": total_saldo,
        "rbs_indibiz_count": rbs_indibiz_count,
        "manja_count": manja_count,
        "online_redaman_count": online_redaman_count,
        "hvc_gold_count": hvc_gold_count,
        "hvc_diamond_count": hvc_diamond_count,
        "hvc_platinum_count": hvc_platinum_count,
        "reguler_count": reguler_count,
        "garansi_count": garansi_count,
        "osla_count": osla_count,
        "sqm_count": sqm_count,
        "unspec_count": unspec_count,
        "gamas_count": gamas_count,
        "belum_count": belum_count,
        "undispatch_count": undispatch_count,
        "belum_breakdown": belum_breakdown,
        "undispatch_breakdown": undispatch_breakdown,
        "wz_pivot": formatted_wz_pivot,
        "wz_pivot_totals": {
            "belum": tot_belum,
            "proses": tot_proses,
            "pending": tot_pending,
            "unassigned": tot_unassigned,
            "grand_total": tot_grand
        },
        "wz_wilsus_pivot": formatted_wz_wilsus_pivot,
        "grand_jenis_totals": dict(grand_jenis_totals),
        "hasil_ukur_dist": dict(hu_counter),
        "tickets": rows,
        "assurance_matrix": matrix_tickets,
        "all_wilsus": all_wilsus
    }






def load_dashboard_data(start_date: str, end_date: str, sektor: str = "", jenis_order: str = "") -> dict:
    query = Order.query
    if start_date:
        query = query.filter(Order.status_date_parsed >= start_date)
    if end_date:
        query = query.filter(Order.status_date_parsed <= end_date)
    if jenis_order:
        query = query.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())

    filtered_db_rows = query.all()
    filtered_rows = [o.to_dict() for o in filtered_db_rows]

    # Special fetch for matrix (DISPATCH): All rows that might be needed
    # (either DISPATCH == today OR status_morning is active/pending)
    all_db_rows = Order.query.all()
    matrix_source_rows = [o.to_dict() for o in all_db_rows]
    if jenis_order:
        matrix_source_rows = [r for r in matrix_source_rows if normalize_upper(r.get("jenis_order")) == jenis_order.upper()]

    # Determine "Today" context for metrics
    # Default to current WITA (GMT+8) time
    now_utc = datetime.now(timezone.utc)
    now_wita = now_utc + timedelta(hours=8)
    default_today_wita = now_wita.strftime("%Y-%m-%d")

    # If end_date filter is present, use it; otherwise default to current WITA date
    if end_date:
        today = end_date
    else:
        today = default_today_wita

    today_month = today[:7]
    
    today_db_rows = Order.query.filter(Order.status_date_parsed == today).all()
    today_rows = [o.to_dict() for o in today_db_rows]

    allowed_wz = None
    if sektor:
        sektor_map = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }
        allowed_wz = sektor_map.get(sektor.lower())
        if allowed_wz:
            filtered_rows = [r for r in filtered_rows if normalize_upper(r.get("workzone")) in allowed_wz]
            today_rows = [r for r in today_rows if normalize_upper(r.get("workzone")) in allowed_wz]
            matrix_source_rows = [r for r in matrix_source_rows if normalize_upper(r.get("workzone")) in allowed_wz]

    # ── Matrix + Ranking ──────────────────────────────────────────────────────
    matrix_rows_flat = []
    tim_today_counter: Counter = Counter()
    tim_mtd_counter: Counter = Counter()

    # We group by (Workzone + TIM) to determine if that group has any OGP status
    team_status_map = {} # (workzone, tim) -> is_ogp
    
    for row in matrix_source_rows:
        tim = normalize_text(row.get("TIM"))
        wz = normalize_text(row.get("workzone"))
        status_morning_up = normalize_upper(row.get("status morning"))
        
        if not is_truthy_text(tim) or tim == "-":
            continue
            
        key = (wz.lower(), tim.lower())
        if key not in team_status_map:
            team_status_map[key] = False
            
        if status_morning_up in {"SEDANG DIKERJAKAN", "PROSES SETTING"}:
            team_status_map[key] = True

    for row in matrix_source_rows:
        status_up = normalize_upper(row.get("Status"))
        tim = normalize_text(row.get("TIM"))
        wz = normalize_text(row.get("workzone"))
        status_morning_up = normalize_upper(row.get("status morning"))
        dispatch_date = row.get("dispatch_date")

        is_today = (dispatch_date == today)
        potensi_keywords = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP"}
        is_potensi_st = any(v in status_up for v in potensi_keywords)
        is_potensi_sm = any(v in status_morning_up for v in potensi_keywords)
        is_potensi = is_potensi_st or is_potensi_sm

        # 1. Skip WAPPR only if it's NOT a Potensi row (Potensi are usually WAPPR initially)
        if status_up == "WAPPR" and not is_potensi:
            continue
            
        if not is_truthy_text(tim) or tim == "-":
            continue
            
        is_persistent = (status_morning_up in {
            "SEDANG DIKERJAKAN", "BELUM DIKERJAKAN", "", 
            "MATERIAL/NTE", "MATERIAL / NTE", "PENDING", "PROSES SETTING"
        } or is_potensi)
        
        if not is_today and not is_persistent:
            continue
            
        # Keep current COMPWORK today logic
        if status_up == "COMPWORK" and row.get("tgl_ps_parsed") != today:
            continue

        is_ps_today = (status_up == "COMPWORK" and row.get("tgl_ps_parsed") == today)
        status_morning_up = normalize_upper(row.get("status morning"))

        if status_up == "COMPWORK":
            color_class = "success"
        elif "SETTING" in status_morning_up:
            color_class = "primary"
        elif "SEDANG DIKERJAKAN" in status_morning_up:
            color_class = "warning"
        elif status_morning_up == "OKE TARIK":
            color_class = "info"
        elif status_morning_up in {"BELUM DIKERJAKAN", ""}:
            color_class = "secondary"
        else:
            color_class = "danger"

        # Determine team flag (OGP/IDLE) for grouping indicators
        key = (wz.lower(), tim.lower())
        is_p_ogp = team_status_map.get(key, False)
        team_flag = "OGP" if is_p_ogp else "IDLE"

        # Determine special badges (Robust matching for data variations)
        status_m_up = normalize_upper(row.get("status morning"))
        is_ogp_status = ("SEDANG" in status_m_up or "SETTING" in status_m_up)
        is_hr = ("HR" in status_m_up)
        is_issue = any(kw in status_m_up for kw in {"KENDALA", "RUSAK", "IZIN", "ALAMAT", "FAILWA", "KENDALA"})
        is_no_update = (status_m_up in {"", "-", "KOSONG"} or "BELUM" in status_m_up)

        matrix_rows_flat.append({
            "tim": tim,
            "workzone": wz,
            "track_order": normalize_text(row.get("track_order")),
            "odc": normalize_text(row.get("ODC")),
            "kordinat": normalize_text(row.get("kordinat") or row.get("KORDINAT")),
            "status": status_up,
            "status_morning": normalize_text(row.get("status morning")),
            "catatan": normalize_text(row.get("Catatan")),
            "product_name": row.get("product_name") or row.get("Product Name") or "-",
            "color_class": color_class,
            "is_ps_today": is_ps_today,
            "is_ogp_status": is_ogp_status,
            "is_hr": is_hr,
            "is_issue": is_issue,
            "is_no_update": is_no_update,
            "team_flag": team_flag
        })

    query_compwork = Order.query.filter(db.func.upper(Order.status) == "COMPWORK")
    if sektor:
        sektor_map = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }
        allowed_wz = sektor_map.get(sektor.lower())
        if allowed_wz:
            query_compwork = query_compwork.filter(Order.workzone.in_(allowed_wz))

    all_compwork_rows = [o.to_dict() for o in query_compwork.all()]

    for row in all_compwork_rows:
        tim = normalize_text(row.get("TIM") or row.get("tim"))
        if not is_truthy_text(tim) or tim == "-":
            continue
        # Priority: tgl_ps_parsed -> date_modified_parsed -> status_date_parsed
        ps_date = (
            row.get("tgl_ps_parsed") or
            row.get("date_modified_parsed") or
            row.get("status_date_parsed") or
            ""
        )
        if ps_date == today:
            tim_today_counter[tim] += 1
        if ps_date.startswith(today_month):
            tim_mtd_counter[tim] += 1

    top_tim_today = [{"tim": k, "count": v} for k, v in tim_today_counter.most_common(5)]
    top_tim_mtd = [{"tim": k, "count": v} for k, v in tim_mtd_counter.most_common(5)]
    
    # Sort matrix flat list per workzone, then tim, then odc
    matrix_rows_flat.sort(key=lambda x: (
        (x["workzone"] or "").lower(),
        (x["tim"] or "").lower(),
        (x["odc"] or "").lower()
    ))
    matrix_rows = matrix_rows_flat

    # ── Kendala Tables ────────────────────────────────────────────────────────
    kendala_pelanggan_table = []
    kendala_teknik_table = []
    kendala_fu_table = []
    cek_pending_table = []

    pelanggan_keywords = {
        "BATAL", "DOUBLE INPUT", "KENDALA IZIN", "GANTI PAKET", 
        "INDIKASI CABUT PASANG", "RUMAH KOSONG"
    }

    teknik_keywords = {
        "ODP FULL", "ODP JAUH", "KENDALA JALUR/RUTE TARIKAN", "KENDALA JALUR", "RUTE TARIKAN",
        "NO ODP", "LIMITASI ONU", "ODP BELUM GOLIVE", "ODP RUSAK", "INSERT TIANG"
    }

    for row in filtered_rows:
        status_up = normalize_upper(row.get("Status"))
        status_morning_up = normalize_upper(row.get("status morning"))

        if status_up in {"WORKFAIL", "STARTWORK"}:
            if status_morning_up in {"INSERT TIANG", "ODP RUSAK"}:
                kendala_fu_table.append({
                    "tim": row.get("TIM") or "-",
                    "track_order": row.get("track_order", "-"),
                    "status_morning": row.get("status morning", "-"),
                    "catatan": row.get("Catatan", "-")
                })
            if status_morning_up in {"PENDING", "OKE TARIK", "MATERIAL/NTE", "MATERIAL / NTE"}:
                cek_pending_table.append({
                    "tim": row.get("TIM") or "-",
                    "track_order": row.get("track_order", "-"),
                    "status_morning": row.get("status morning", "-"),
                    "catatan": row.get("Catatan", "-")
                })
            if any(kw in status_morning_up for kw in pelanggan_keywords):
                kendala_pelanggan_table.append({
                    "workorder": row.get("Workorder", "-"),
                    "track_order": row.get("track_order", "-"),
                    "status_morning": row.get("status morning", "-"),
                    "catatan": row.get("Catatan", "-"),
                    "validasi": row.get("validasi") or row.get("VALIDASI") or "-",
                    "status": row.get("Status", "-")
                })
            if any(kw in status_morning_up for kw in teknik_keywords):
                kendala_teknik_table.append({
                    "workorder": row.get("Workorder", "-"),
                    "track_order": row.get("track_order", "-"),
                    "status_morning": row.get("status morning", "-"),
                    "catatan": row.get("Catatan", "-"),
                    "validasi": row.get("validasi") or row.get("VALIDASI") or "-",
                    "status": row.get("Status", "-")
                })

    def is_valid_failwa_status(sm_str: str) -> bool:
        if not sm_str: return False
        s = sm_str.strip().upper()
        if not s or s in {"-", "NONE", "EMPTY", "BELUM DIKERJAKAN", "SEDANG DIKERJAKAN", "OK TARIK", "OKE TARIK"}:
            return False
        return True

    failwa_count = sum(
        1 for o in all_db_rows
        if normalize_upper(o.status) == "STARTWORK"
        and is_valid_failwa_status(o.status_morning)
    )





    # Undispatch (untuk floating widget)
    undispatch_count = sum(
        1 for r in filtered_rows
        if normalize_upper(r.get("Status")) in {"WORKFAIL", "STARTWORK"}
        and (not is_truthy_text(r.get("TIM", "")) or r.get("TIM") == "-")
        and is_empty_status_m(r.get("status morning"))
    )

    # Build ps_today_rows:
    # PS hari ini = COMPWORK dengan tgl_ps_parsed = today
    # Fallback: Date Modified = today, lalu Status Date = today
    ps_today_rows = []
    for r in matrix_source_rows:
        # Priority: tgl_ps_parsed -> date_modified_parsed -> status_date_parsed
        ps_date = (
            r.get("tgl_ps_parsed") or
            r.get("date_modified_parsed") or
            r.get("status_date_parsed") or
            ""
        )
        if start_date and ps_date < start_date: continue
        if end_date and ps_date > end_date: continue
        if not start_date and not end_date and ps_date != today: continue
        if allowed_wz and normalize_upper(r.get("workzone")) not in allowed_wz: continue
        ps_today_rows.append(r)

    # Jam PS Chart -> COMPWORK with tgl_ps / date_modified = today
    jam_ps_source = [r for r in ps_today_rows if normalize_upper(r.get("Status")) == "COMPWORK"]
        
    # Jam RE Chart -> Date Created
    query_re = Order.query
    if start_date:
        query_re = query_re.filter(Order.date_created_parsed >= start_date)
    if end_date:
        query_re = query_re.filter(Order.date_created_parsed <= end_date)
    if not start_date and not end_date:
        query_re = query_re.filter(Order.date_created_parsed == today)
    
    re_db_rows = query_re.all()
    re_rows = [o.to_dict() for o in re_db_rows]
    if sektor:
        allowed_wz = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }.get(sektor.lower())
        if allowed_wz:
            re_rows = [r for r in re_rows if normalize_upper(r.get("workzone")) in allowed_wz]

    # Exclude CNCLWORK and WAPPR from Jam RE
    re_rows = [r for r in re_rows if normalize_upper(r.get("Status")) not in {"CNCLWORK", "WAPPR"}]

    # Sort per Tim
    kendala_fu_table.sort(key=lambda x: (x.get("tim") or "").lower())
    cek_pending_table.sort(key=lambda x: (x.get("tim") or "").lower())

    # Count IDLE teams only from those currently in the Matrix (Today's teams)
    unique_teams_in_matrix = {} # tim -> team_flag
    for r in matrix_rows:
        tname = r.get("tim")
        if tname and tname != "-":
            unique_teams_in_matrix[tname] = r.get("team_flag")
            
    idle_teams_count = sum(1 for flag in unique_teams_in_matrix.values() if flag == "IDLE")

    # For the summary cards at the top, we use the global snapshot (matrix_source_rows)
    # so that metrics like "TOTAL POTENSI" show everything, not just today's updates.
    summary_data = build_summary(matrix_source_rows, ps_today_rows)
    summary_data["idle_teams_count"] = idle_teams_count

    sisa_pivot_data = build_sisa_pivot(matrix_source_rows)

    detail_potensi_table = []
    potensi_keywords = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP"}

    for row in matrix_source_rows:
        status_up = normalize_upper(row.get("Status"))
        status_morning_up = normalize_upper(row.get("status morning"))

        is_potensi_st = any(v in status_up for v in potensi_keywords)
        is_potensi_sm = any(v in status_morning_up for v in potensi_keywords)

        if is_potensi_st or is_potensi_sm:
            detail_potensi_table.append({
                "workorder": row.get("Workorder", "-"),
                "track_order": row.get("track_order", "-"),
                "product_name": get_product_name_normalized(row),
                "odc": row.get("ODC", "-"),
                "tim": row.get("TIM") or row.get("tim") or "-",
                "status_morning": row.get("status morning", "-"),
                "catatan": row.get("Catatan", "-"),
                "eskal_daman": row.get("eskal_daman") or row.get("Eskal Daman") or row.get("ESKAL DAMAN") or "-",
                "status": row.get("Status", "-")
            })

    return {
        "source": "sqlite_database",
        "summary": summary_data,
        "jam_ps_chart": build_hour_chart(jam_ps_source, "Jam PS"),
        "jam_re_chart": build_hour_chart(re_rows, "Jam re"),
        "matrix_rows": matrix_rows,
        "row_count": len(filtered_rows),
        "today_date": today,
        "kendala_fu": kendala_fu_table,
        "cek_pending": cek_pending_table,
        "kendala_pelanggan": kendala_pelanggan_table,
        "kendala_teknik": kendala_teknik_table,
        "detail_potensi": detail_potensi_table,
        "failwa_count": failwa_count,
        "undispatch_count": undispatch_count,
        "top_tim_today": top_tim_today,
        "top_tim_mtd": top_tim_mtd,
        "sisa_pivot": sisa_pivot_data
    }


@app.route("/")
def index():
    filters = {
        "start_date": request.args.get("start_date", ""),
        "end_date": request.args.get("end_date", ""),
        "sektor": request.args.get("sektor", ""),
        "wilsus": request.args.get("wilsus", ""),
        "jenis_tiket": request.args.get("jenis_tiket", ""),
        "jenis_order": request.args.get("jenis_order", "").upper(),
        "active_tab": request.args.get("active_tab", "pane-summary")
    }
    dashboard_data = load_dashboard_data(filters["start_date"], filters["end_date"], filters["sektor"], filters["jenis_order"])
    assurance_data = load_assurance_data(filters["sektor"], filters["wilsus"], filters["jenis_tiket"])


    return render_template(
        "dashboard_order.html",
        filters=filters,
        data_source=dashboard_data["source"],
        summary=dashboard_data["summary"],
        jam_ps_chart=dashboard_data["jam_ps_chart"],
        jam_re_chart=dashboard_data["jam_re_chart"],
        matrix_rows=dashboard_data["matrix_rows"],
        row_count=dashboard_data["row_count"],
        today_date=dashboard_data["today_date"],
        kendala_fu=dashboard_data["kendala_fu"],
        cek_pending=dashboard_data["cek_pending"],
        kendala_pelanggan=dashboard_data["kendala_pelanggan"],
        kendala_teknik=dashboard_data["kendala_teknik"],
        detail_potensi=dashboard_data["detail_potensi"],
        failwa_count=dashboard_data["failwa_count"],
        undispatch_count=dashboard_data["undispatch_count"],
        top_tim_today=dashboard_data["top_tim_today"],
        top_tim_mtd=dashboard_data["top_tim_mtd"],
        sisa_pivot=dashboard_data["sisa_pivot"],
        assurance=assurance_data
    )


last_sync_time = datetime.now()


# ─── TELEGRAM BOT AI AGENT (OPENROUTER) ───────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            # Fallback without parse_mode if Markdown parsing failed
            payload_plain = {
                "chat_id": chat_id,
                "text": text
            }
            requests.post(url, json=payload_plain, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def call_openrouter_api(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise Exception("API Key OpenRouter tidak ditemukan. Harap isi OPENROUTER_API_KEY di Railway.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://monitoring.internetbisnis.biz.id",
        "X-Title": "SA Batulicin Bot"
    }

    # Top free models priority list
    models_to_try = [
        "openrouter/free",
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    try:
        m_res = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
        if m_res.status_code == 200:
            live_models = [m['id'] for m in m_res.json().get('data', []) if m['id'].endswith(':free')]
            for lm in live_models:
                if lm not in models_to_try:
                    models_to_try.append(lm)
    except Exception:
        pass

    last_error = ""
    for model_name in models_to_try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            data = res.json()
            if res.status_code == 200 and "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                if content:
                    return content
            else:
                last_error = data.get("error", {}).get("message", res.text)
        except Exception as e:
            last_error = str(e)

    raise Exception(f"OpenRouter Error: {last_error}")


def get_order_category_summary(r: dict) -> str:
    jo = normalize_upper(r.get("jenis_order") or get_product_name_normalized(r) or "")
    pname = normalize_upper(r.get("product_name") or "")
    tr = normalize_upper(r.get("track_order") or "")
    
    if "INDIBIZ" in jo or "INDIBIZ" in pname:
        return "INDIBIZ"
    elif jo in ["TIF", "VULA", "TIF/VULA"] or tr.startswith("TIF") or tr.startswith("VULA") or "VULA" in jo or "VULA" in pname:
        return "TIF / VULA"
    else:
        return "INDIHOME"


def generate_manual_summary():
    now_utc = datetime.now(timezone.utc)
    now_wita = now_utc + timedelta(hours=8)
    today_wita = now_wita.strftime("%Y-%m-%d")

    all_orders = Order.query.all()
    all_rows = [o.to_dict() for o in all_orders]

    persistent_statuses = {"SEDANG DIKERJAKAN", "PENDING", "MATERIAL/NTE", "PROSES SETTING", "BELUM DIKERJAKAN"}
    active_rows = []
    for r in all_rows:
        is_today = (r.get("dispatch_date") == today_wita or 
                    r.get("status_date_parsed") == today_wita or 
                    r.get("date_created_parsed") == today_wita)
        is_persistent = normalize_upper(r.get("status morning")) in persistent_statuses
        if is_today or is_persistent:
            active_rows.append(r)

    target_rows = active_rows if active_rows else all_rows

    def is_ps_order(r):
        st_up = normalize_upper(r.get("Status"))
        sm_up = normalize_upper(r.get("status morning"))
        dt_st = r.get("status_date_parsed")
        tgl_ps = r.get("tgl_ps_parsed")
        if (dt_st == today_wita or tgl_ps == today_wita):
            if any(k in st_up for k in ["COMPWORK", "PS", "COMPLETED"]) or any(k in sm_up for k in ["COMPWORK", "PS", "COMPLETED"]):
                return True
        return False

    potensi_kw = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP", "SETTING", "VALDAT", "QC", "VALIDASI", "POTENSI"}

    cats = defaultdict(list)
    for r in target_rows:
        cats[get_order_category_summary(r)].append(r)

    # 1. INDIHOME
    indihome_rows = cats["INDIHOME"]
    re_indihome = sum(1 for r in indihome_rows if r.get("date_created_parsed") == today_wita)
    ps_indihome = sum(1 for r in indihome_rows if is_ps_order(r))
    ratio_indihome = (ps_indihome / re_indihome * 100) if re_indihome > 0 else 0.0

    pot_indihome = sum(1 for r in indihome_rows if any(k in normalize_upper(r.get("Status")) for k in potensi_kw) or any(k in normalize_upper(r.get("status morning")) for k in potensi_kw))
    ogp_indihome = sum(1 for r in indihome_rows if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN")
    oke_tarik_indihome = sum(1 for r in indihome_rows if "OKE TARIK" in normalize_upper(r.get("status morning")) or "OKE TARIK" in normalize_upper(r.get("Status")))

    # Tim Idle (Active today but not in OGP)
    all_teams = set()
    ogp_teams = set()
    for r in target_rows:
        t = (r.get("TIM") or r.get("tim") or "").strip()
        if t and t != "-":
            all_teams.add(t)
            if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN":
                ogp_teams.add(t)
    idle_teams = sorted(list(all_teams - ogp_teams))

    # 2. INDIBIZ
    indibiz_rows = cats["INDIBIZ"]
    ps_indibiz = sum(1 for r in indibiz_rows if is_ps_order(r))
    pot_indibiz = sum(1 for r in indibiz_rows if any(k in normalize_upper(r.get("Status")) for k in potensi_kw) or any(k in normalize_upper(r.get("status morning")) for k in potensi_kw))
    ogp_indibiz = sum(1 for r in indibiz_rows if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN")
    oke_tarik_indibiz = sum(1 for r in indibiz_rows if "OKE TARIK" in normalize_upper(r.get("status morning")) or "OKE TARIK" in normalize_upper(r.get("Status")))

    # 3. TIF / VULA
    tif_rows = cats["TIF / VULA"]
    ps_tif = sum(1 for r in tif_rows if is_ps_order(r))
    pot_tif = sum(1 for r in tif_rows if any(k in normalize_upper(r.get("Status")) for k in potensi_kw) or any(k in normalize_upper(r.get("status morning")) for k in potensi_kw))
    ogp_tif = sum(1 for r in tif_rows if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN")
    oke_tarik_tif = sum(1 for r in tif_rows if "OKE TARIK" in normalize_upper(r.get("status morning")) or "OKE TARIK" in normalize_upper(r.get("Status")))

    # 4. Sisa Order Breakdown
    dash = load_dashboard_data("", "", "")
    sisa_map = {"BLC": 0, "SER": 0, "STI": 0, "KPL": 0, "PGT": 0, "KIP": 0}
    if "sisa_pivot" in dash and "workzones" in dash["sisa_pivot"]:
        for wz in dash["sisa_pivot"]["workzones"]:
            wz_name = wz.get("workzone", "").upper()
            sisa_map[wz_name] = wz.get("wz_grand_total", 0)
    total_sisa = sum(sisa_map.values())

    lines = [f"📊 *LAPORAN MONITORING PROVISIONING ({today_wita})*\n"]

    lines.append("🏠 *INDIHOME*")
    lines.append(f"• 📋 RE Hari ini : `{re_indihome}`")
    lines.append(f"• ✅ PS Hari ini : `{ps_indihome}`")
    lines.append(f"• 📈 Ratio PS/RE : `{ratio_indihome:.1f}%`\n")
    lines.append(f"• 🟦 Potensi : `{pot_indihome}`")
    lines.append(f"• 🟧 Sedang OGP : `{ogp_indihome}`")
    lines.append(f"• 🟩 OKE Tarik : `{oke_tarik_indihome}`\n")

    lines.append(f"👥 *Tim Idle ({len(idle_teams)} Tim):*")
    if idle_teams:
        for tm in idle_teams:
            lines.append(f"• `{tm}`")
    else:
        lines.append("• Tidak ada tim idle saat ini.")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")

    lines.append("🏢 *INDIBIZ*")
    lines.append(f"• ✅ PS Hari ini : `{ps_indibiz}`")
    lines.append(f"• 🟦 Potensi : `{pot_indibiz}`")
    lines.append(f"• 🟧 Sedang OGP : `{ogp_indibiz}`")
    lines.append(f"• 🟩 OKE Tarik : `{oke_tarik_indibiz}`")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")

    lines.append("⚡ *TIF / VULA*")
    lines.append(f"• ✅ PS Hari ini : `{ps_tif}`")
    lines.append(f"• 🟦 Potensi : `{pot_tif}`")
    lines.append(f"• 🟧 Sedang OGP : `{ogp_tif}`")
    lines.append(f"• 🟩 OKE Tarik : `{oke_tarik_tif}`")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")

    lines.append(f"📦 *Sisa Order (Total: {total_sisa} Order)*")
    for wz_code in ["BLC", "SER", "STI", "KPL", "PGT", "KIP"]:
        lines.append(f"• {wz_code} : `{sisa_map.get(wz_code, 0)}`")

    return "\n".join(lines).strip()


def clean_odp_code(odc_str: str) -> str:
    if not odc_str or odc_str.strip() in {"-", "", "None"}:
        return "-"
    s = odc_str.split('/')[0].strip()
    return s


def is_redaman_good(r: dict) -> bool:
    hu = normalize_upper(r.get("hasil_ukur"))
    r_val = abs(parse_redaman_val(r.get("redaman")))
    if hu == "ONLINE" and (13.0 <= r_val <= 24.0 or (0 < r_val <= 24.0)):
        return True
    return False


def generate_unspec_summary():
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]
    
    unspec_rows = [
        r for r in rows
        if "UNSPEC" in normalize_upper(r.get("summary"))
        or "UNSPEK" in normalize_upper(r.get("summary"))
        or "UNSPEC" in normalize_upper(r.get("customer_type"))
    ]
    
    if not unspec_rows:
        return "Tidak ada tiket UNSPEC saat ini."

    grouped = defaultdict(list)
    for r in unspec_rows:
        wz = normalize_text(r.get("workzone") or "KOSONG").upper()
        grouped[wz].append(r)

    lines = [f"📋 *MONITORING TIKET UNSPEC ({len(unspec_rows)} Tiket)*\n"]
    for wz in sorted(grouped.keys()):
        lines.append(f"🏢 *WORKZONE {wz}*")
        for r in grouped[wz]:
            inc = r.get("incident") or "-"
            raw_odc = r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-"
            odc = clean_odp_code(raw_odc)
            srv = r.get("service_no") or "-"
            status_icon = "🟢" if is_redaman_good(r) else "🔴"
            lines.append(f"{status_icon} `{inc}` • `{odc}` • `{srv}`")
        lines.append("")

    lines.append("Keterangan:\n🟢 Redaman Online (max -24 dB) | 🔴 Redaman > -24 dB / Need Action")
    return "\n".join(lines).strip()


def is_sqm_or_unspec(summary_str: str) -> bool:
    s = (summary_str or "").upper()
    return ("SQM" in s) or ("UNSPEC" in s) or ("UNSPEK" in s)


def generate_ttr_mepet_summary():
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]
    
    ttr_rows = []
    for r in rows:
        seg = normalize_upper(r.get("customer_segment"))
        ctype = normalize_upper(r.get("customer_type"))
        ttr_val = parse_ttr_val(r.get("ttr"))
        
        if seg == "PL-TSEL" and "GOLD" in ctype:
            if 9.0 <= ttr_val <= 12.0:
                if not is_sqm_or_unspec(r.get("summary")) and not is_gamas_ticket(r):
                    ttr_rows.append((r, ttr_val))

    if not ttr_rows:
        return "Tidak ada tiket HVC Gold dengan TTR mepet (9-12 jam) saat ini."

    grouped = defaultdict(list)
    for r, ttr_val in ttr_rows:
        wz = normalize_text(r.get("workzone") or "KOSONG").upper()
        grouped[wz].append((r, ttr_val))

    lines = [f"⚠️ *MONITORING TTR MEPET 9-12 JAM ({len(ttr_rows)} Tiket)*\n"]
    for wz in sorted(grouped.keys()):
        lines.append(f"🏢 *WORKZONE {wz}*")
        for r, ttr_val in grouped[wz]:
            inc = r.get("incident") or "-"
            raw_odc = r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-"
            odc = clean_odp_code(raw_odc)
            tim = r.get("tim") or r.get("tim_kawan") or r.get("tim_insera") or "-"
            ttr_str = f"{ttr_val:.2f}".replace('.', ',')
            lines.append(f"`{inc}` • `{odc}` • `{tim}` • `{ttr_str} jam`")
        lines.append("")

    return "\n".join(lines).strip()


def generate_online_redaman_summary():
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]
    
    online_rows = []
    for r in rows:
        hu = normalize_upper(r.get("hasil_ukur"))
        r_val = parse_redaman_val(r.get("redaman"))
        r_abs = abs(r_val)
        if hu == "ONLINE" and (13.0 <= r_abs <= 24.0 or (0 < r_abs <= 24.0)):
            online_rows.append((r, r_val))

    if not online_rows:
        return "Tidak ada tiket dengan Redaman Online (max -24 dB) saat ini."

    grouped = defaultdict(list)
    for r, r_val in online_rows:
        wz = normalize_text(r.get("workzone") or "KOSONG").upper()
        grouped[wz].append((r, r_val))

    lines = [f"🟢 *MONITORING TIKET REDAMAN ONLINE ({len(online_rows)} Tiket)*\n"]
    for wz in sorted(grouped.keys()):
        lines.append(f"🏢 *WORKZONE {wz}*")
        for r, r_val in grouped[wz]:
            inc = r.get("incident") or "-"
            raw_odc = r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-"
            odc = clean_odp_code(raw_odc)
            hu = (r.get("hasil_ukur") or "ONLINE").upper()
            jt = r.get("jenis_tiket") or get_jenis_tiket(r)
            r_str = f"-{abs(r_val):.2f}" if r_val != 0 else "-"
            lines.append(f"`{jt}` • `{inc}` • `{odc}` • *{hu}* `{r_str}`")
        lines.append("")

    return "\n".join(lines).strip()


def generate_gamas_summary():
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]
    
    gamas_rows = [r for r in rows if is_gamas_ticket(r)]
    if not gamas_rows:
        return "Tidak ada tiket GAMAS saat ini."

    odp_counts = defaultdict(int)
    grouped_wz = defaultdict(list)

    for r in gamas_rows:
        wz = normalize_text(r.get("workzone") or "KOSONG").upper()
        raw_odc = r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-"
        odc = clean_odp_code(raw_odc)
        odp_counts[odc] += 1
        grouped_wz[wz].append(r)

    lines = [f"🚨 *MONITORING TIKET GAMAS ({len(gamas_rows)} Tiket)*\n"]
    lines.append("📊 *RINGKASAN SEBARAN PER ODP:*")
    
    sorted_odp = sorted(odp_counts.items(), key=lambda x: (-x[1], x[0]))
    for odp, count in sorted_odp:
        lines.append(f"• `{odp}` : *{count} Tiket*")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")

    for wz in sorted(grouped_wz.keys()):
        lines.append(f"🏢 *WORKZONE {wz}*")
        sorted_rows = sorted(
            grouped_wz[wz],
            key=lambda r: clean_odp_code(r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-")
        )
        for r in sorted_rows:
            inc = r.get("incident") or "-"
            raw_odc = r.get("odc_clean") or r.get("odc_real") or r.get("odc") or "-"
            odc = clean_odp_code(raw_odc)
            hu = normalize_upper(r.get("hasil_ukur")) or "EMPTY"
            r_val = parse_redaman_val(r.get("redaman"))
            if r_val != 0:
                r_str = f"-{abs(r_val):.2f}"
            else:
                r_str = "-"
            lines.append(f"`{inc}` • `{odc}` • *{hu}* `{r_str}`")
        lines.append("")

    return "\n".join(lines).strip()


def generate_psb_sore_summary() -> str:
    now_utc = datetime.now(timezone.utc)
    now_wita = now_utc + timedelta(hours=8)
    today_wita = now_wita.strftime("%Y-%m-%d")

    all_orders = Order.query.all()
    all_rows = [o.to_dict() for o in all_orders]

    persistent_statuses = {"SEDANG DIKERJAKAN", "PENDING", "MATERIAL/NTE", "PROSES SETTING", "BELUM DIKERJAKAN"}
    active_rows = []
    for r in all_rows:
        is_today = r.get("dispatch_date") == today_wita or r.get("status_date_parsed") == today_wita
        is_persistent = normalize_upper(r.get("status morning")) in persistent_statuses
        if is_today or is_persistent:
            active_rows.append(r)

    target_rows = active_rows if active_rows else all_rows

    # 1. OGP
    ogp_rows = [r for r in target_rows if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN"]

    # 2. POTENSI
    potensi_keywords = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP", "SETTING", "VALDAT", "QC", "VALIDASI", "POTENSI"}
    potensi_rows = []
    for r in target_rows:
        st_up = normalize_upper(r.get("Status"))
        sm_up = normalize_upper(r.get("status morning"))
        if any(v in st_up for v in potensi_keywords) or any(v in sm_up for v in potensi_keywords):
            potensi_rows.append(r)

    lines = [f"📋 *LAPORAN MONITORING PSB SORE ({today_wita})*\n"]

    lines.append(f"🟧 *ORDER SEDANG OGP ({len(ogp_rows)} Order)*")
    if ogp_rows:
        sorted_ogp = sorted(ogp_rows, key=lambda x: (normalize_upper(x.get("workzone")), x.get("track_order") or ""))
        for r in sorted_ogp:
            tr = r.get("track_order") or r.get("SC Order No/Track ID/CSRM No") or "-"
            tim = r.get("TIM") or r.get("tim") or "-"
            catatan = (r.get("Catatan") or r.get("catatan") or "").strip()
            if not catatan or catatan in {".", "-"}:
                sm = (r.get("status morning") or r.get("status_morning") or "").strip()
                if "TARIK" in sm.upper():
                    catatan = sm

            if catatan and catatan not in {".", "-"}:
                lines.append(f"• `{tr}` • `{tim}` • \n{catatan}")
            else:
                lines.append(f"• `{tr}` • `{tim}`")
    else:
        lines.append("Tidak ada order Sedang OGP saat ini.")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n")

    lines.append(f"🟦 *ORDER POTENSI ({len(potensi_rows)} Order)*\n")
    if potensi_rows:
        grouped_qc = defaultdict(list)
        for r in potensi_rows:
            qc = (r.get("validasi") or r.get("cek qc") or r.get("status morning") or "Belum dorong").strip()
            if not qc or qc == "-":
                qc = "Belum dorong"
            grouped_qc[qc].append(r)

        for qc in sorted(grouped_qc.keys()):
            lines.append(f"*{qc}*")
            sorted_potensi = sorted(grouped_qc[qc], key=lambda x: (normalize_upper(x.get("workzone")), x.get("Workorder") or x.get("track_order") or ""))
            for r in sorted_potensi:
                jo = r.get("jenis_order") or get_product_name_normalized(r) or "INDIHOME"
                tim = r.get("TIM") or r.get("tim") or "-"
                wo = r.get("Workorder") or r.get("workorder") or r.get("track_order") or "-"
                eskal = r.get("eskal_daman") or r.get("Eskal daman") or "Belum eskal daman"
                lines.append(f"• `{jo}` • `{tim}` • `{wo}` • `{eskal}`")
            lines.append("")
    else:
        lines.append("Tidak ada order Potensi saat ini.")

    return "\n".join(lines).strip()


def generate_asr_summary() -> str:
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]

    def parse_ttr(val_str):
        if not val_str: return 0.0
        try:
            return float(str(val_str).replace(',', '.').strip())
        except:
            return 0.0

    def is_sqm_or_unspec(summary_str):
        s = (summary_str or "").upper()
        return ("SQM" in s) or ("UNSPEC" in s) or ("UNSPEK" in s)

    def is_garansi(r):
        if is_sqm_or_unspec(r.get("summary")) or is_sqm_or_unspec(r.get("customer_type")):
            return False
        st_g = (r.get("status_garansi") or "").upper()
        if st_g and ("GARANSI" in st_g or st_g in {"YES", "TRUE", "1", "Y"}):
            return True
        st = (r.get("guarante_status") or "").upper()
        if not st:
            return False
        if "NOT" in st or "NON" in st or st == "NO":
            return False
        return "GARANSI" in st or "GUARANTEE" in st

    def classify_ticket(r):
        summary = (r.get("summary") or "").upper()
        cust_type = (r.get("customer_type") or "").upper()
        cust_seg = (r.get("customer_segment") or "").upper()
        
        if cust_seg == "RBS" or "RBS" in summary or "RBS" in cust_type:
            return "RBS"
        if "SQM" in summary:
            return "SQM"
        if "UNSPEC" in summary or "UNSPEK" in summary:
            return "Unspec"
        if "GOLD" in cust_type:
            return "HVC Gold"
        if "PLATINUM" in cust_type:
            return "HVC Platinum"
        if "DIAMOND" in cust_type:
            return "HVC Diamond"
        return "Reguler"

    # 1. Total Saldo
    total_saldo = len(rows)
    counts = {
        "HVC Gold": 0,
        "HVC Platinum": 0,
        "HVC Diamond": 0,
        "Reguler": 0,
        "SQM": 0,
        "RBS": 0,
        "Unspec": 0
    }
    for r in rows:
        cat = classify_ticket(r)
        counts[cat] = counts.get(cat, 0) + 1

    lines = []
    lines.append(f"📊 *LAPORAN SUMMARY ASSURANCE (TIKET GANGGUAN)*\n")
    lines.append(f"🎫 *Total Saldo Tiket : {total_saldo}*")
    lines.append(f"• 🥇 HVC Gold : {counts['HVC Gold']}")
    lines.append(f"• 💎 HVC Platinum : {counts['HVC Platinum']}")
    lines.append(f"• 💠 HVC Diamond : {counts['HVC Diamond']}")
    lines.append(f"• 👤 Reguler : {counts['Reguler']}")
    lines.append(f"• ⚡ SQM : {counts['SQM']}")
    lines.append(f"• 🏢 RBS : {counts['RBS']}")
    lines.append(f"• ❓ Unspec : {counts['Unspec']}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━\n")

    # 2. Tiket Manja
    manja_rows = []
    for r in rows:
        desc = (r.get("description_assignment") or "").upper()
        if "CUSTOMER ASSIGN" in desc or (r.get("jam_manja") or "").strip():
            manja_rows.append(r)

    sorted_manja = sorted(manja_rows, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
    manja_list = []
    for r in sorted_manja:
        jm = (r.get("jam_manja") or r.get("booking_date") or "").strip()
        if jm and " " in jm and len(jm) > 10:
            time_part = jm.split()[1][:5]
            jm_str = f" {time_part}"
        elif jm:
            jm_str = f" {jm}"
        else:
            jm_str = ""

        inc = r.get("incident") or "-"
        odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
        gamas_flag = " (GAMAS)" if is_gamas_ticket(r) else ""
        manja_list.append(f"• `{inc}` `{odp}`{jm_str}{gamas_flag}")

    lines.append(f"⏳ *Tiket manja : {len(manja_list)}*")
    if manja_list:
        lines.extend(manja_list)
    else:
        lines.append("• Tidak ada tiket manja saat ini.")
    lines.append("")

    # 3. OSLA
    osla_rows = []
    for r in rows:
        ttr_val = parse_ttr(r.get("ttr"))
        if ttr_val > 12.0 and not is_sqm_or_unspec(r.get("summary")):
            osla_rows.append(r)

    sorted_osla = sorted(osla_rows, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
    osla_list = []
    for r in sorted_osla:
        inc = r.get("incident") or "-"
        odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
        ttr_val = parse_ttr(r.get("ttr"))
        ttr_str = f"{ttr_val:.2f}".replace('.', ',')
        gamas_flag = " (GAMAS)" if is_gamas_ticket(r) else ""
        osla_list.append(f"• `{inc}` `{odp}` `{ttr_str}`{gamas_flag}")

    lines.append("⏰ *OSLA :*")
    if osla_list:
        lines.extend(osla_list)
    else:
        lines.append("• Tidak ada tiket OSLA saat ini.")
    lines.append("")

    # 4. GARANSI
    garansi_rows = [r for r in rows if is_garansi(r)]
    sorted_garansi = sorted(garansi_rows, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
    garansi_list = []
    for r in sorted_garansi:
        inc = r.get("incident") or "-"
        odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
        ttr_val = parse_ttr(r.get("ttr"))
        ttr_str = f"{ttr_val:.2f}".replace('.', ',')
        gamas_flag = " (GAMAS)" if is_gamas_ticket(r) else ""
        garansi_list.append(f"• `{inc}` `{odp}` `{ttr_str}`{gamas_flag}")

    lines.append("🛡️ *GARANSI :*")
    if garansi_list:
        lines.extend(garansi_list)
    else:
        lines.append("• Tidak ada tiket Garansi saat ini.")
    lines.append("")

    # 5. HVC Gold Detail
    gold_rows = []
    for r in rows:
        cust_type = (r.get("customer_type") or "").upper()
        if "GOLD" in cust_type and not is_sqm_or_unspec(r.get("summary")) and not is_sqm_or_unspec(cust_type):
            gold_rows.append(r)

    sorted_gold = sorted(gold_rows, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
    gold_detail_list = []
    for r in sorted_gold:
        inc = r.get("incident") or "-"
        odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
        ttr_val = parse_ttr(r.get("ttr"))
        ttr_str = f"{ttr_val:.2f}".replace('.', ',')
        gamas_flag = " (GAMAS)" if is_gamas_ticket(r) else ""
        gold_detail_list.append(f"• `{inc}` `{odp}` `{ttr_str}`{gamas_flag}")

    lines.append(f"🥇 *HVC Gold : {len(gold_detail_list)}*")
    if gold_detail_list:
        lines.extend(gold_detail_list)
    else:
        lines.append("• Tidak ada tiket HVC Gold saat ini.")
    lines.append("")

    # 6. HVC Diamond & Platinum Detail
    dia_plat_rows = []
    for r in rows:
        cust_type = (r.get("customer_type") or "").upper()
        if ("DIAMOND" in cust_type or "PLATINUM" in cust_type) and not is_sqm_or_unspec(r.get("summary")):
            dia_plat_rows.append(r)

    sorted_dia_plat = sorted(dia_plat_rows, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
    dia_plat_list = []
    for r in sorted_dia_plat:
        inc = r.get("incident") or "-"
        odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
        ttr_val = parse_ttr(r.get("ttr"))
        ttr_str = f"{ttr_val:.2f}".replace('.', ',')
        gamas_flag = " (GAMAS)" if is_gamas_ticket(r) else ""
        dia_plat_list.append(f"• `{inc}` `{odp}` `{ttr_str}`{gamas_flag}")

    lines.append(f"💎 *HVC Diamond & Platinum : {len(dia_plat_list)}*")
    if dia_plat_list:
        lines.extend(dia_plat_list)
    else:
        lines.append("• Tidak ada tiket HVC Diamond/Platinum saat ini.")
    lines.append("")

    # 6. Undispatch & Belum Dikerjakan
    undispatch_counts = {
        "HVC Gold": 0,
        "HVC Platinum": 0,
        "HVC Diamond": 0,
        "Reguler": 0,
        "SQM": 0,
        "RBS": 0,
        "Unspec": 0
    }
    total_undispatch_belum = 0
    for r in rows:
        tim = (r.get("tim") or "").strip()
        sk = (r.get("status_kawan") or "").strip().upper()
        if not tim or tim == "-" or sk in {"", "BELUM DIKERJAKAN"}:
            cat = classify_ticket(r)
            undispatch_counts[cat] += 1
            total_undispatch_belum += 1

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🚨 *Undispatch & Belum Dikerjakan : {total_undispatch_belum}*")
    lines.append(f"• 🥇 HVC Gold : {undispatch_counts['HVC Gold']}")
    lines.append(f"• 💎 HVC Platinum : {undispatch_counts['HVC Platinum']}")
    lines.append(f"• 💠 HVC Diamond : {undispatch_counts['HVC Diamond']}")
    lines.append(f"• 👤 Reguler : {undispatch_counts['Reguler']}")
    lines.append(f"• ⚡ SQM : {undispatch_counts['SQM']}")
    lines.append(f"• 🏢 RBS : {undispatch_counts['RBS']}")
    lines.append(f"• ❓ Unspec : {undispatch_counts['Unspec']}")

    return "\n".join(lines).strip()


def generate_prov_idle_summary() -> str:
    all_orders = Order.query.all()
    all_rows = [o.to_dict() for o in all_orders]

    cats = defaultdict(list)
    for r in all_rows:
        st_up = (r.get("Status") or r.get("status") or "").strip().upper()
        if st_up not in {"STARTWORK", "WORKFAIL"}:
            continue

        sm = (r.get("status morning") or r.get("status_morning") or "").strip()
        sm_up = sm.upper()

        # Strict filter: status morning MUST be empty, "-", "EMPTY", or "BELUM DIKERJAKAN"
        allowed_sm = {"", "-", "EMPTY", "BELUM DIKERJAKAN"}
        if sm_up not in allowed_sm:
            continue

        cat = get_order_category_summary(r)
        tr = r.get("track_order") or "-"
        if cat == "INDIHOME":
            tr_up = tr.upper()
            if not (tr_up.startswith("AO") or tr_up.startswith("PD")):
                continue

        tim = (r.get("TIM") or r.get("tim") or "").strip()
        odc_val = (r.get("ODC") or r.get("odc") or "-").strip()
        odc = odc_val.split()[0] if odc_val else "-"
        tim_str = tim if tim and tim != "-" else "EMPTY"
        sm_str = sm if sm and sm != "-" else "EMPTY"

        cats[cat].append(f"`{tr}` `{odc}` `{tim_str}` `{sm_str}`")

    lines = ["📦 *LAPORAN PROVISIONING UNDISPATCH & BELUM DIKERJAKAN*\n"]
    for unit_name in ["INDIHOME", "INDIBIZ", "TIF / VULA"]:
        items = cats[unit_name]
        lines.append(f"🏠 *{unit_name}*" if unit_name == "INDIHOME" else (f"🏢 *{unit_name}*" if unit_name == "INDIBIZ" else f"⚡ *{unit_name}*"))
        if items:
            for item in items:
                lines.append(item)
        else:
            lines.append("• Tidak ada order undispatch/belum dikerjakan.")
        lines.append("")

    return "\n".join(lines).strip()


def generate_asr_idle_summary() -> str:
    all_tickets = AssuranceTicket.query.all()
    rows = [t.to_dict() for t in all_tickets]

    def parse_ttr(val_str):
        if not val_str: return 0.0
        try:
            return float(str(val_str).replace(',', '.').strip())
        except:
            return 0.0

    def classify_ticket(r):
        summary = (r.get("summary") or "").upper()
        cust_type = (r.get("customer_type") or "").upper()
        cust_seg = (r.get("customer_segment") or "").upper()

        if cust_seg == "RBS" or "RBS" in summary or "RBS" in cust_type:
            return "RBS"
        if "SQM" in summary:
            return "SQM"
        if "UNSPEC" in summary or "UNSPEK" in summary:
            return "UNSPEC"
        if "GOLD" in cust_type:
            return "HVC GOLD"
        if "DIAMOND" in cust_type:
            return "HVC DIAMOND"
        if "PLATINUM" in cust_type:
            return "HVC PLATINUM"
        return "REGULER"

    cats = defaultdict(list)
    for r in rows:
        tim = (r.get("tim") or "").strip()
        sk = (r.get("status_kawan") or "").strip().upper()

        is_undispatch = not tim or tim == "-" or tim.upper() == "EMPTY"
        is_belum = sk in {"BELUM DIKERJAKAN", "EMPTY", "-", ""}

        if is_undispatch or is_belum:
            c_name = classify_ticket(r)
            cats[c_name].append(r)

    lines = ["🚨 *LAPORAN ASSURANCE UNDISPATCH & BELUM DIKERJAKAN*\n"]
    icon_map = {
        "HVC GOLD": "🥇",
        "HVC DIAMOND": "💠",
        "HVC PLATINUM": "💎",
        "REGULER": "👤",
        "SQM": "⚡",
        "UNSPEC": "❓",
        "RBS": "🏢"
    }
    for unit_name in ["HVC GOLD", "HVC DIAMOND", "HVC PLATINUM", "REGULER", "SQM", "UNSPEC", "RBS"]:
        row_list = cats[unit_name]
        icon = icon_map.get(unit_name, "📌")
        lines.append(f"{icon} *{unit_name}*")
        if row_list:
            sorted_rows = sorted(row_list, key=lambda x: clean_odc_real(x.get("device_name"), x.get("odc_real")))
            for r in sorted_rows:
                inc = r.get("incident") or "-"
                odp = clean_odc_real(r.get("device_name"), r.get("odc_real"))
                ttr_val = parse_ttr(r.get("ttr"))
                ttr_str = f"{ttr_val:.2f}".replace('.', ',')
                lines.append(f"`{inc}` `{odp}` `{ttr_str}`")
        else:
            lines.append("• Tidak ada tiket undispatch/belum dikerjakan.")
        lines.append("")

    return "\n".join(lines).strip()


def generate_pending_summary() -> str:
    now_utc = datetime.now(timezone.utc)
    now_wita = now_utc + timedelta(hours=8)
    today_wita = now_wita.strftime("%Y-%m-%d")

    all_orders = Order.query.all()
    all_rows = [o.to_dict() for o in all_orders]

    persistent_statuses = {"SEDANG DIKERJAKAN", "PENDING", "MATERIAL/NTE", "PROSES SETTING", "BELUM DIKERJAKAN"}
    active_rows = []
    for r in all_rows:
        is_today = r.get("dispatch_date") == today_wita or r.get("status_date_parsed") == today_wita
        is_persistent = normalize_upper(r.get("status morning")) in persistent_statuses
        if is_today or is_persistent:
            active_rows.append(r)

    target_rows = active_rows if active_rows else all_rows

    pending_rows = [r for r in target_rows if "PENDING" in normalize_upper(r.get("status morning"))]
    if not pending_rows:
        return "Tidak ada order PENDING saat ini."

    grouped = defaultdict(list)
    for r in pending_rows:
        wz = normalize_text(r.get("workzone") or "KOSONG").upper()
        grouped[wz].append(r)

    lines = [f"🟡 *MONITORING ORDER PENDING ({len(pending_rows)} Order)*\n"]
    for wz in sorted(grouped.keys()):
        lines.append(f"🏢 *WORKZONE {wz}*")
        sorted_rows = sorted(grouped[wz], key=lambda x: x.get("track_order") or "")
        for r in sorted_rows:
            tr = r.get("track_order") or r.get("SC Order No/Track ID/CSRM No") or "-"
            tim = r.get("TIM") or r.get("tim") or "-"
            cat = (r.get("Catatan") or r.get("catatan") or r.get("status morning") or "-").strip()
            lines.append(f"• `{tr}` • `{tim}` • `{cat}`")
        lines.append("")

    return "\n".join(lines).strip()


def generate_sync_summary() -> str:
    global last_sync_time
    c1 = sync_orders()
    c2 = sync_assurance_tickets()
    last_sync_time = datetime.now()
    
    now_utc = datetime.now(timezone.utc)
    now_wita = (now_utc + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S WITA")
    
    return f"""🔄 *SINKRONISASI DATA BERHASIL!*

✅ *Data Provisioning:* Synced `{c1}` order
✅ *Data Assurance:* Synced `{c2}` tiket
🕒 *Waktu Sync:* `{now_wita}`

💡 _Data database telah diperbarui ke versi terbaru. Silakan jalankan command monitoring Anda (misal: /psbsore, /gamas, /pending, /online, /ttr, /unspec, /asr, /providle, /asridle)._"""


def generate_rekon_summary(tim_query: str) -> str:
    rows = fetch_sheet_rows()
    deduped = dedupe_rows(rows)
    
    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    
    filtered_rows = []
    for r in deduped:
        status_up = normalize_upper(r.get("Status"))
        tim_val = normalize_upper(r.get("tim") or r.get("TIM"))
        date_mod = normalize_text(r.get("Date Modified"))
        
        is_mtd = False
        parsed_mod = parse_sheet_date(date_mod)
        if parsed_mod and parsed_mod.startswith(current_month_str):
            is_mtd = True
            
        if status_up == "COMPWORK" and tim_query.upper() in tim_val and is_mtd:
            filtered_rows.append(r)
            
    if not filtered_rows:
        return f"❌ Tidak ada data COMPWORK MTD untuk tim: {tim_query.upper()}"
        
    out = [f"*{tim_query.upper()}*"]
    
    for r in filtered_rows:
        wo = normalize_text(r.get("Workorder")) or normalize_text(r.get("track_order")) or "-"
        lensa_val = normalize_upper(r.get("LENSA"))
        wecare_val = normalize_upper(r.get("WECARE"))
        valins_val = normalize_upper(r.get("VALINS"))
        
        if "AREA 4" in lensa_val:
            qc_stat = "QC NOK"
        elif "COMPLY" in lensa_val:
            qc_stat = "QC OK"
        else:
            qc_stat = "QC OK"
        
        if "AREA 4" in wecare_val or "NOK" in wecare_val:
            wecare_stat = "WECARE NOK"
        else:
            wecare_stat = "WECARE OK"
            
        if "PSB" in valins_val or "NOK" in valins_val:
            valins_stat = "VALINS NOK"
        else:
            valins_stat = "VALINS OK"
            
        out.append(f"{wo} | {qc_stat} | {wecare_stat} | {valins_stat}")
        
    return "\n".join(out)


def generate_help_guide():
    return """🤖 *PANDUAN FITUR & DAFTAR COMMAND BOT MONITORING*

🔄 *COMMAND SINKRONISASI DATA*
🔄 `/sync` : Update & tarik data realtime terbaru dari Google Sheet

📌 *COMMAND ASSURANCE (TIKET GANGGUAN)*
📊 `/asr` : Laporan Summary & Status Tiket Gangguan (Assurance)
🚨 `/asridle` : Laporan Tiket Assurance Undispatch & Belum Dikerjakan
🚨 `/gamas` : Cek tiket GAMAS per Workzone (lengkap sebaran ODP)
🟢 `/online` : Cek tiket Redaman Online (max -24 dB) per Workzone
⚠️ `/ttr` : Cek tiket HVC Gold TTR mepet (9 - 12 jam) per Workzone
📋 `/unspec` : Cek tiket UNSPEC (PL-TSEL Unspecified) per Workzone

📌 *COMMAND PROVISIONING (PASANG BARU)*
📊 `/prov` atau `/pso` atau `/summary` : Summary Laporan Provisioning & Sisa Order
📦 `/providle` : Laporan Order Provisioning Undispatch & Belum Dikerjakan
🌅 `/psbsore` : Cek Order Sedang OGP dan Total Potensi
🟡 `/pending` : Cek Order PENDING beserta catatan kendala per Workzone

💬 *BOT INTERAKTIF*
Anda juga bisa bertanya langsung menggunakan bahasa alami:
• _"Berapa total PS hari ini?"_
• _"Berapa tiket manja yang aktif?"_
• _"Berapa order pending hari ini?"_"""


@app.route("/api/telegram/webhook", methods=["POST"])
def telegram_webhook():
    api_key = os.getenv("OPENROUTER_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    if not TELEGRAM_BOT_TOKEN:
        return jsonify({"status": "disabled"}), 200

    update = request.get_json()
    if not update:
        return "OK", 200

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"]
        user_name = update["message"]["from"].get("first_name", "Pengguna")

        cmd = user_text.strip().lower()
        if cmd in {"/start", "/help", "help", "menu", "petunjuk", "command", "fitur", "info"} or cmd.startswith("/help") or cmd.startswith("/start"):
            help_msg = generate_help_guide()
            send_telegram_message(chat_id, help_msg)
            return "OK", 200

        if cmd.startswith("/sync") or cmd.startswith("/update") or cmd.startswith("/refresh"):
            send_telegram_message(chat_id, "⏳ *Proses sinkronisasi data sedang berjalan...*\n_Mohon tunggu sebentar, data sedang ditarik dari Google Sheets._")
            
            def do_bg_sync(target_chat_id):
                with app.app_context():
                    try:
                        sync_msg = generate_sync_summary()
                        send_telegram_message(target_chat_id, sync_msg)
                    except Exception as ex:
                        print(f"Error in async /sync: {ex}")
                        send_telegram_message(
                            target_chat_id, 
                            f"⚠️ *Sinkronisasi Gagal:* {str(ex)}\n\n"
                            "💡 _Server Google Sheets sedang mengalami perlambatan/gangguan koneksi. Silakan coba jalankan /sync kembali beberapa saat lagi._"
                        )

            threading.Thread(target=do_bg_sync, args=(chat_id,)).start()
            return "OK", 200

        if cmd.startswith("/providle") or cmd.startswith("/psoidle"):
            try:
                msg = generate_prov_idle_summary()
                if len(msg) > 4000:
                    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, msg)
            except Exception as ex:
                print(f"Error in /providle command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /providle: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/asridle") or cmd.startswith("/assuranceidle"):
            try:
                msg = generate_asr_idle_summary()
                if len(msg) > 4000:
                    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, msg)
            except Exception as ex:
                print(f"Error in /asridle command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /asridle: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/asr") or cmd.startswith("/assurance"):
            try:
                asr_msg = generate_asr_summary()
                if len(asr_msg) > 4000:
                    chunks = [asr_msg[i:i+4000] for i in range(0, len(asr_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, asr_msg)
            except Exception as ex:
                print(f"Error in /asr command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /asr: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/pending"):
            try:
                pending_msg = generate_pending_summary()
                if len(pending_msg) > 4000:
                    chunks = [pending_msg[i:i+4000] for i in range(0, len(pending_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, pending_msg)
            except Exception as ex:
                print(f"Error in /pending command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /pending: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/psbsore") or cmd.startswith("/psb_sore"):
            try:
                psb_msg = generate_psb_sore_summary()
                if len(psb_msg) > 4000:
                    chunks = [psb_msg[i:i+4000] for i in range(0, len(psb_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, psb_msg)
            except Exception as ex:
                print(f"Error in /psbsore command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /psbsore: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/gamas"):
            try:
                gamas_msg = generate_gamas_summary()
                if len(gamas_msg) > 4000:
                    chunks = [gamas_msg[i:i+4000] for i in range(0, len(gamas_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, gamas_msg)
            except Exception as ex:
                print(f"Error in /gamas command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /gamas: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/online") or cmd.startswith("/redaman"):
            try:
                online_msg = generate_online_redaman_summary()
                if len(online_msg) > 4000:
                    chunks = [online_msg[i:i+4000] for i in range(0, len(online_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, online_msg)
            except Exception as ex:
                print(f"Error in /online command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /online: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/ttr"):
            try:
                ttr_msg = generate_ttr_mepet_summary()
                if len(ttr_msg) > 4000:
                    chunks = [ttr_msg[i:i+4000] for i in range(0, len(ttr_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, ttr_msg)
            except Exception as ex:
                print(f"Error in /ttr command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /ttr: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/unspec") or cmd.startswith("/unspek"):
            try:
                unspec_msg = generate_unspec_summary()
                if len(unspec_msg) > 4000:
                    chunks = [unspec_msg[i:i+4000] for i in range(0, len(unspec_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, unspec_msg)
            except Exception as ex:
                print(f"Error in /unspec command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /unspec: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/rekon"):
            try:
                parts = user_text.split(maxsplit=1)
                if len(parts) < 2:
                    send_telegram_message(chat_id, "⚠️ Format salah. Gunakan: `/rekon <nama_tim>`\nContoh: `/rekon BLC|ARIF-006`")
                    return "OK", 200
                tim_query = parts[1].strip()
                rekon_msg = generate_rekon_summary(tim_query)
                if len(rekon_msg) > 4000:
                    chunks = [rekon_msg[i:i+4000] for i in range(0, len(rekon_msg), 4000)]
                    for c in chunks:
                        send_telegram_message(chat_id, c)
                else:
                    send_telegram_message(chat_id, rekon_msg)
            except Exception as ex:
                print(f"Error in /rekon command: {ex}")
                send_telegram_message(chat_id, f"⚠️ Gagal memproses /rekon: {str(ex)}")
            return "OK", 200

        if cmd.startswith("/prov") or cmd.startswith("/pso") or cmd.startswith("/summary") or cmd == "provisioning":
            manual_msg = generate_manual_summary()
            send_telegram_message(chat_id, manual_msg)
            return "OK", 200

        # Fetch current data for AI
        try:
            dashboard_data = load_dashboard_data("", "", "")
            assurance_data = load_assurance_data("", "", "")

            ai_context = {
                "provisioning": dashboard_data["summary"],
                "idle_teams": dashboard_data["summary"].get("idle_teams_count", 0),
                "potensi_hari_ini": len(dashboard_data.get("detail_potensi", [])),
                "undispatch_count": dashboard_data["undispatch_count"],
                "assurance": {
                    "total_saldo": assurance_data["total_saldo"],
                    "hvc_count": (assurance_data.get("hvc_gold_count",0) + assurance_data.get("hvc_diamond_count",0) + assurance_data.get("hvc_platinum_count",0)),
                    "platinum_count": assurance_data["hvc_platinum_count"],
                    "gold_count": assurance_data["hvc_gold_count"],
                    "garansi_count": assurance_data["garansi_count"],
                    "pl_tsel_count": assurance_data["total_saldo"],
                    "undispatch_assurance": assurance_data["undispatch_count"]
                }
            }
            
            top_teams = ", ".join([f"{t['tim']} ({t['count']})" for t in dashboard_data.get("top_tim_today", [])])
            ai_context["top_tim_hari_ini"] = top_teams

            context_json = json.dumps(ai_context, indent=2)

            prompt = f"""
Kamu adalah "Antigravity Bot", asisten AI profesional untuk tim teknisi SA Batulicin. 
Tugasmu adalah menjawab pertanyaan pengguna tentang kondisi pekerjaan dan tiket berdasarkan data realtime dari database.
Jawab dengan ramah, informatif, dan profesional dalam bahasa Indonesia. Gunakan format Markdown yang rapi (seperti **bold**, atau list jika perlu).
Jika pengguna menyapa (halo/p/test), atau pesan kurang jelas, sertakan daftar command berikut di akhir jawabanmu:
🟢 /online : Cek daftar tiket Redaman Online (max -24 dB)
⚠️ /ttr : Cek tiket HVC Gold dengan TTR mepet range 9 - 12 Jam
📋 /unspec : Cek daftar tiket UNSPEC (PL-TSEL Unspecified)
📊 /prov atau /pso atau /summary : Laporan Provisioning & Sisa Order

Berikut adalah RINGKASAN DATA SAAT INI (Format JSON):
{context_json}

Keterangan:
- "provisioning" berisi ringkasan Order Pasang Baru (PS, Kendala, Valdat, dsb).
- "assurance" berisi ringkasan Tiket Gangguan (Manja) (Total saldo, HVC, Garansi, dll).

Pertanyaan pengguna ({user_name}):
"{user_text}"
"""
            ai_reply = call_openrouter_api(prompt)
            send_telegram_message(chat_id, ai_reply)

        except Exception as e:
            print("AI Error, falling back to help guide:", e)
            help_msg = generate_help_guide()
            send_telegram_message(chat_id, help_msg)

    return "OK", 200


REKON_BOT_TOKEN = "8497218740:AAF9bUVlQdHUKlKB8VMSLTs_b8Dbm_k33m4"

def send_telegram_message_rekon(chat_id, text):
    if not REKON_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{REKON_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            payload_plain = {"chat_id": chat_id, "text": text}
            requests.post(url, json=payload_plain, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message rekon: {e}")

@app.route("/api/telegram/webhook_rekon", methods=["POST"])
def telegram_webhook_rekon():
    update = request.get_json()
    if not update:
        return "OK", 200

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"]
        cmd = user_text.strip().lower()

        if cmd.startswith("/rekon"):
            try:
                parts = user_text.split(maxsplit=1)
                if len(parts) < 2:
                    send_telegram_message_rekon(chat_id, "⚠️ Format salah. Gunakan: `/rekon <nama_tim>`\nContoh: `/rekon BLC|ARIF-006`")
                    return "OK", 200
                tim_query = parts[1].strip()
                send_telegram_message_rekon(chat_id, "⏳ *Sedang menarik data dari Google Sheets...*")
                
                rekon_msg = generate_rekon_summary(tim_query)
                if len(rekon_msg) > 4000:
                    chunks = [rekon_msg[i:i+4000] for i in range(0, len(rekon_msg), 4000)]
                    for c in chunks:
                        send_telegram_message_rekon(chat_id, c)
                else:
                    send_telegram_message_rekon(chat_id, rekon_msg)
            except Exception as ex:
                print(f"Error in /rekon command: {ex}")
                send_telegram_message_rekon(chat_id, f"⚠️ Gagal memproses /rekon: {str(ex)}")
            return "OK", 200
        
        elif cmd in {"/start", "/help"}:
            send_telegram_message_rekon(chat_id, "Halo! Ini adalah Bot khusus Rekon.\nKetik `/rekon <nama_tim>` untuk mengecek data.\nContoh: `/rekon BLC|ARIF-006`")
            return "OK", 200

    return "OK", 200


@app.route("/api/dashboard/order")
def api_dashboard_order():
    global last_sync_time
    # Automatic Sync Check (if last sync > 15 minutes)
    if (datetime.now() - last_sync_time) > timedelta(minutes=15):
        try:
            sync_orders()
            sync_assurance_tickets()
            last_sync_time = datetime.now()
            print("Auto-sync completed successfully.")
        except Exception as e:
            print(f"Auto-sync failed: {str(e)}")

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    sektor = request.args.get("sektor", "")
    return jsonify(load_dashboard_data(start_date, end_date, sektor))


@app.route("/api/dashboard/detail")
def api_dashboard_detail():
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    category = request.args.get("category", "")
    sektor = request.args.get("sektor", "")
    jenis_order = request.args.get("jenis_order", "")

    query = Order.query
    if start_date:
        query = query.filter(Order.status_date_parsed >= start_date)
    if end_date:
        query = query.filter(Order.status_date_parsed <= end_date)
    if jenis_order:
        query = query.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())

    filtered_db_rows = query.all()
    filtered_rows = [o.to_dict() for o in filtered_db_rows]

    today = datetime.now().strftime("%Y-%m-%d")
    today_db_rows = Order.query.filter(Order.status_date_parsed == today).all()
    today_rows = [o.to_dict() for o in today_db_rows]

    allowed_wz = None
    if sektor:
        sektor_map = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }
        allowed_wz = sektor_map.get(sektor.lower())
        if allowed_wz:
            filtered_rows = [r for r in filtered_rows if normalize_upper(r.get("workzone")) in allowed_wz]
            today_rows = [r for r in today_rows if normalize_upper(r.get("workzone")) in allowed_wz]

    result = []
    if category == "total_ps":
        # PS hari ini: COMPWORK dengan tgl_ps_parsed = today (fallback: date_modified, status_date)
        query_all = Order.query
        if jenis_order:
            query_all = query_all.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())
        all_db_rows = query_all.all()
        all_rows = [o.to_dict() for o in all_db_rows]
        if allowed_wz:
            all_rows = [r for r in all_rows if normalize_upper(r.get("workzone")) in allowed_wz]
        
        ps_today_rows = []
        for r in all_rows:
            ps_date = (
                r.get("tgl_ps_parsed") or
                r.get("date_modified_parsed") or
                r.get("status_date_parsed") or
                ""
            )
            if start_date and ps_date < start_date: continue
            if end_date and ps_date > end_date: continue
            if not start_date and not end_date and ps_date != today: continue
            ps_today_rows.append(r)
            
        result = [r for r in ps_today_rows if normalize_upper(r.get("Status")) == "COMPWORK"]
    elif category == "total_potensi":
        result = []
        potensi_keywords = {"VALSTART", "VAL START", "ACTCOMP", "ACT COMP", "ACTCOPM", "VALCOMP", "VAL COMP"}
        query_pot = Order.query
        if jenis_order:
            query_pot = query_pot.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())
        pot_rows = [o.to_dict() for o in query_pot.all()]
        if allowed_wz:
            pot_rows = [r for r in pot_rows if normalize_upper(r.get("workzone")) in allowed_wz]
        for r in pot_rows:
            st_up = normalize_upper(r.get("Status"))
            sm_up = normalize_upper(r.get("status morning"))
            if any(v in st_up for v in potensi_keywords) or any(v in sm_up for v in potensi_keywords):
                result.append(r)
    elif category == "sedang_ogp":
        result = [r for r in filtered_rows if normalize_upper(r.get("status morning")) == "SEDANG DIKERJAKAN"]
    elif category == "oke_tarik":
        result = [r for r in filtered_rows if normalize_upper(r.get("Status")) in {"WORKFAIL", "STARTWORK"} and normalize_upper(r.get("status morning")) == "OKE TARIK"]
    elif category == "belum_dikerjakan":
        result = [
            r for r in filtered_rows
            if normalize_upper(r.get("Status")) in {"WORKFAIL", "STARTWORK"}
            and normalize_upper(r.get("status morning")) in {"BELUM DIKERJAKAN", ""}
            and is_truthy_text(r.get("TIM"))
            and str(r.get("TIM")).strip() != "-"
        ]
    elif category == "undispatch":
        result = [
            r for r in filtered_rows
            if normalize_upper(r.get("Status")) in {"WORKFAIL", "STARTWORK"}
            and (not is_truthy_text(r.get("TIM", "")) or r.get("TIM") == "-")
            and is_empty_status_m(r.get("status morning"))
        ]
    elif category == "idle_teams":
        # Logic to identify IDLE teams from Matrix source
        now_utc = datetime.now(timezone.utc)
        now_wita = now_utc + timedelta(hours=8)
        today_wita = now_wita.strftime("%Y-%m-%d")
        persistent_statuses = {"SEDANG DIKERJAKAN", "PENDING", "MATERIAL/NTE", "PROSES SETTING", "BELUM DIKERJAKAN"}

        query_idle = Order.query
        if jenis_order:
            query_idle = query_idle.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())
        all_rows_list = [o.to_dict() for o in query_idle.all()]
        
        if sektor:
            sektor_map = {"batulicin": {"BLC", "SER"}, "satui": {"STI", "PGT", "KIP"}, "kotabaru": {"KPL"}}
            allowed_wz = sektor_map.get(sektor.lower(), set())
            all_rows_list = [r for r in all_rows_list if normalize_upper(r.get("workzone")) in allowed_wz]

        matrix_rows_source = []
        for r in all_rows_list:
            is_today = r.get("dispatch_date") == today_wita
            is_persistent = normalize_upper(r.get("status morning")) in persistent_statuses
            if is_today or is_persistent:
                matrix_rows_source.append(r)

        team_status_map = {}
        for r in matrix_rows_source:
            tim = normalize_text(r.get("TIM"))
            if not is_truthy_text(tim) or tim == "-": continue
            status_m_up = normalize_upper(r.get("status morning"))
            if tim.lower() not in team_status_map: team_status_map[tim.lower()] = False
            if status_m_up in {"SEDANG DIKERJAKAN", "PROSES SETTING"}:
                team_status_map[tim.lower()] = True
        
        idle_teams = sorted(list({t for t, is_ogp in team_status_map.items() if not is_ogp}))
        return jsonify({"success": True, "data": [{"tim": t.upper()} for t in idle_teams]})
    elif category == "perlu_failwa":
        if start_date or end_date:
            source_rows = filtered_rows
        else:
            query_fw = Order.query
            if jenis_order:
                query_fw = query_fw.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())
            source_rows = [o.to_dict() for o in query_fw.all()]

        if sektor:
            sektor_map = {"batulicin": {"BLC", "SER"}, "satui": {"STI", "PGT", "KIP"}, "kotabaru": {"KPL"}}
            allowed_wz = sektor_map.get(sektor.lower(), set())
            source_rows = [r for r in source_rows if normalize_upper(r.get("workzone")) in allowed_wz]

        def is_valid_failwa_sm(sm_str: str) -> bool:
            if not sm_str: return False
            s = sm_str.strip().upper()
            if not s or s in {"-", "NONE", "EMPTY", "BELUM DIKERJAKAN", "SEDANG DIKERJAKAN", "OK TARIK", "OKE TARIK"}:
                return False
            return True

        result = [
            r for r in source_rows
            if normalize_upper(r.get("Status")) == "STARTWORK"
            and is_valid_failwa_sm(r.get("status morning"))
        ]


    elif category == "pivot_cell":
        wz_req = request.args.get("workzone", "")
        wil_req = request.args.get("wilsus", "")
        jen_req = request.args.get("jenis", "")

        query_pivot = Order.query
        if jenis_order:
            query_pivot = query_pivot.filter(db.func.upper(Order.jenis_order) == jenis_order.upper())
        source_rows = [o.to_dict() for o in query_pivot.all()]
        
        if sektor:
            sektor_map = {"batulicin": {"BLC", "SER"}, "satui": {"STI", "PGT", "KIP"}, "kotabaru": {"KPL"}}
            allowed_wz = sektor_map.get(sektor.lower(), set())
            source_rows = [r for r in source_rows if normalize_upper(r.get("workzone")) in allowed_wz]

        result = []
        for r in source_rows:
            st_up = normalize_upper(r.get("Status"))
            sm_up = normalize_upper(r.get("status morning"))
            if st_up in {"STARTWORK", "WORKFAIL"}:
                is_sedang = ("SEDANG" in sm_up and "BELUM" not in sm_up)
                is_belum_or_empty = sm_up in {"", "BELUM DIKERJAKAN"}
                if not (is_sedang or is_belum_or_empty):
                    continue
            else:
                continue

            if wz_req and wz_req.strip() not in {"-", "", "ALL", "GRAND TOTAL"} and normalize_upper(r.get("workzone")) != normalize_upper(wz_req):
                continue
            if wil_req and wil_req.strip() not in {"-", "", "ALL"} and normalize_upper(r.get("wilsus")) != normalize_upper(wil_req):
                continue
            if jen_req and jen_req.strip() not in {"TOTAL", "GRAND TOTAL", ""}:
                pname = get_product_name_normalized(r)
                if normalize_upper(pname) != normalize_upper(jen_req):
                    continue
            result.append(r)

    else:
        result = []


    detail_rows = []
    for r in result:
        # Fallback if product_name is "-" or empty
        pname = r.get("product_name")
        if not pname or pname == "-":
            pname = get_product_name_normalized(r)
            
        detail_rows.append({
            "status": r.get("Status", "-"),
            "track_order": r.get("track_order", "-"),
            "workorder": r.get("Workorder", "-"),
            "product_name": pname,
            "odc": r.get("ODC", "-"),
            "tim": r.get("TIM", "-"),
            "status_morning": r.get("status morning") or "EMPTY",
            "catatan": r.get("Catatan", "-"),
            "eskal_daman": r.get("eskal_daman") or r.get("Eskal daman") or "-"
        })

    return jsonify({"success": True, "data": detail_rows})




@app.route("/api/assurance/detail")
def api_assurance_detail():
    category = request.args.get("category", "")
    sektor = request.args.get("sektor", "")
    wilsus = request.args.get("wilsus", "")
    jenis_tiket = request.args.get("jenis_tiket", "")

    query = AssuranceTicket.query
    all_tickets = query.all()
    rows = [t.to_dict() for t in all_tickets]

    for r in rows:
        r["jenis_tiket"] = get_jenis_tiket(r)
        r["is_manja"] = get_is_manja(r)

    if sektor:

        sektor_map = {
            "batulicin": {"BLC", "SER"},
            "satui": {"STI", "PGT", "KIP"},
            "kotabaru": {"KPL"}
        }
        allowed_wz = sektor_map.get(sektor.lower())
        if allowed_wz:
            rows = [r for r in rows if normalize_upper(r.get("workzone")) in allowed_wz]

    if wilsus and wilsus.strip() not in {"-", "", "ALL"}:
        rows = [r for r in rows if normalize_upper(r.get("wilsus")) == normalize_upper(wilsus)]

    if jenis_tiket:
        jt_up = normalize_upper(jenis_tiket)
        if jt_up == "REGULER":
            rows = [r for r in rows if r["jenis_tiket"] not in {"SQM", "UNSPEC", "UNSPEK"}]
        elif jt_up == "SQM":
            rows = [r for r in rows if r["jenis_tiket"] == "SQM" or "SQM" in normalize_upper(r.get("summary"))]
        elif jt_up == "UNSPEC":
            rows = [r for r in rows if r["jenis_tiket"] in {"UNSPEC", "UNSPEK"} or "UNSPEC" in normalize_upper(r.get("summary")) or "UNSPEK" in normalize_upper(r.get("summary"))]
        else:
            rows = [r for r in rows if normalize_upper(r["jenis_tiket"]) == jt_up]



    def parse_ttr_val(val_str: str) -> float:
        if not val_str: return 0.0
        try:
            return float(val_str.replace(',', '.').strip())
        except:
            return 0.0

    def parse_redaman_val(val_str: str) -> float:
        if not val_str or val_str.strip() in {"-", ""}: return 0.0
        try:
            return float(val_str.replace(',', '.').strip())
        except:
            return 0.0

    def is_sqm_or_unspec(summary_str: str) -> bool:
        s = (summary_str or "").upper()
        return ("SQM" in s) or ("UNSPEC" in s) or ("UNSPEK" in s)

    def is_garansi_ticket(r: dict) -> bool:
        if is_sqm_or_unspec(r.get("summary")) or is_sqm_or_unspec(r.get("customer_type")) or is_sqm_or_unspec(r.get("jenis_tiket")):
            return False
        st_g = normalize_upper(r.get("status_garansi"))
        if st_g and ("GARANSI" in st_g or st_g in {"YES", "TRUE", "1", "Y"}):
            return True
        st = normalize_upper(r.get("guarante_status"))
        if not st:
            return False
        if "NOT" in st or "NON" in st or st == "NO":
            return False
        return "GARANSI" in st or "GUARANTEE" in st

    result = []
    for r in rows:
        cust_type = normalize_upper(r.get("customer_type"))
        cust_seg = normalize_upper(r.get("customer_segment"))
        summary = normalize_upper(r.get("summary"))
        garansi_st = normalize_upper(r.get("guarante_status"))
        sk = normalize_upper(r.get("status_kawan"))
        tim = normalize_text(r.get("tim"))
        desc_assign = normalize_upper(r.get("description_assignment"))
        hasil_uk = normalize_upper(r.get("hasil_ukur"))
        redaman_val = parse_redaman_val(r.get("redaman"))
        ttr_val = parse_ttr_val(r.get("ttr"))

        is_pl_tsel = (cust_seg == "PL-TSEL")

        if category == "assurance_saldo":
            result.append(r)
        elif category == "rbs_indibiz":
            if cust_seg == "RBS": result.append(r)
        elif category == "tik_manja":
            if "CUSTOMER ASSIGN" in desc_assign: result.append(r)
        elif category == "online_redaman":
            if hasil_uk == "ONLINE" and (13.0 <= abs(redaman_val) < 25.0 or -25.0 < redaman_val <= -13.0): result.append(r)
        elif category == "hvc_gold":
            if is_pl_tsel and "GOLD" in cust_type and not is_sqm_or_unspec(summary): result.append(r)
        elif category == "hvc_diamond":
            if is_pl_tsel and "DIAMOND" in cust_type and not is_sqm_or_unspec(summary): result.append(r)
        elif category == "hvc_platinum":
            if is_pl_tsel and "PLATINUM" in cust_type and not is_sqm_or_unspec(summary): result.append(r)
        elif category == "reguler":
            if is_pl_tsel and ("REGULER" in cust_type or "REGULAR" in cust_type) and not is_sqm_or_unspec(summary): result.append(r)
        elif category == "garansi":
            if is_pl_tsel and is_garansi_ticket(r): result.append(r)
        elif category == "osla":
            if is_pl_tsel and ttr_val > 12.0 and not is_sqm_or_unspec(summary): result.append(r)
        elif category == "sqm":
            if is_pl_tsel and "SQM" in summary: result.append(r)
        elif category == "unspec":
            if is_pl_tsel and ("UNSPEC" in summary or "UNSPEK" in summary): result.append(r)
        elif category == "gamas":
            if is_pl_tsel and is_gamas_ticket(r): result.append(r)
        elif category == "assurance_belum_dikerjakan":
            if is_pl_tsel and sk in {"", "BELUM DIKERJAKAN"}: result.append(r)
        elif category == "assurance_undispatch":
            if is_pl_tsel and (not tim or tim == "-"): result.append(r)
        elif category == "pivot_cell":
            wz_req = request.args.get("workzone", "")
            wil_req = request.args.get("wilsus", "")
            jen_req = request.args.get("jenis", "")

            matched = True
            if wz_req and wz_req.strip() not in {"-", "", "ALL", "GRAND TOTAL"} and normalize_upper(r.get("workzone")) != normalize_upper(wz_req):
                matched = False
            if wil_req and wil_req.strip() not in {"-", "", "ALL"} and normalize_upper(r.get("wilsus")) != normalize_upper(wil_req):
                matched = False
            if jen_req and jen_req.strip() not in {"TOTAL", "GRAND TOTAL", ""}:
                jt = normalize_upper(r.get("jenis_tiket"))
                jr = normalize_upper(jen_req)
                if "HVC DIAMOND" in jr or "PLATINUM" in jr:
                    if jt not in {"HVC DIAMOND", "HVC PLATINUM"}:
                        matched = False
                elif jt != jr:
                    matched = False
            if matched:
                result.append(r)



    detail_rows = []
    for r in result:
        detail_rows.append({
            "incident": r.get("incident", "-"),
            "odc_real": r.get("odc_clean") or r.get("odc_real") or "-",
            "service_no": r.get("service_no", "-"),
            "customer_segment": r.get("customer_segment", "-"),
            "reported_date": r.get("reported_date", "-"),
            "customer_type": r.get("customer_type", "-"),
            "hasil_ukur": r.get("hasil_ukur", "-"),
            "redaman": r.get("redaman", "-"),
            "ttr": r.get("ttr", "-"),
            "flag": r.get("flag", "-"),
            "tim": r.get("tim") or "-",
            "wilsus": r.get("wilsus", "-"),
            "status_kawan": r.get("status_kawan") or "EMPTY",
            "catatan": r.get("catatan") or "-",
            "jam_manja": r.get("jam_manja") or "-",
            "summary": r.get("summary") or "-"
        })

    return jsonify({"success": True, "data": detail_rows})


@app.route("/api/sync", methods=["POST"])
def api_sync():
    global last_sync_time
    try:
        c1 = sync_orders()
        c2 = sync_assurance_tickets()
        last_sync_time = datetime.now()
        return jsonify({"success": True, "message": f"Berhasil sinkronisasi {c1} data Provisioning & {c2} data Assurance"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/status")
def api_status():
    global last_sync_time
    return jsonify({"last_sync_time": last_sync_time.timestamp()})







@app.errorhandler(500)
def internal_server_error(e):
    import traceback
    err_tb = traceback.format_exc()
    print("500 Internal Server Error Traceback:\n", err_tb)
    return f"<h3>Internal Server Error</h3><pre>{err_tb}</pre>", 500


def init_db_migration():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("db.create_all note:", e)

        try:
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(assurance_ticket)")
            cols = [info[1] for info in cursor.fetchall()]
            if "status_garansi" not in cols:
                try:
                    cursor.execute("ALTER TABLE assurance_ticket ADD COLUMN status_garansi VARCHAR(100)")
                    conn.commit()
                    print("Migrated assurance_ticket table with status_garansi column")
                except Exception as ex:
                    print("Note adding status_garansi:", ex)

            cursor.execute('PRAGMA table_info("order")')
            order_cols = [info[1] for info in cursor.fetchall()]
            if "service_no" not in order_cols:
                try:
                    cursor.execute('ALTER TABLE "order" ADD COLUMN service_no VARCHAR(100)')
                    conn.commit()
                    print("Migrated order table with service_no column")
                except Exception as ex:
                    print("Note adding service_no:", ex)
        except Exception as e:
            print("DB Migration Note:", e)

try:
    init_db_migration()
except Exception as ex:
    print("init_db_migration error:", ex)


if __name__ == "__main__":
    with app.app_context():
        if Order.query.first() is None:
            print("Database Provisioning kosong, melakukan sinkronisasi awal...")
            sync_orders()
        if AssuranceTicket.query.first() is None:
            print("Database Assurance kosong, melakukan sinkronisasi awal...")
            sync_assurance_tickets()
        print("Sinkronisasi database selesai.")
    app.run(debug=True, host="0.0.0.0", port=5000)

