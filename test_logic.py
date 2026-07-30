from app import build_summary, normalize_upper, normalize_text

def test_potensi_logic():
    # Mock rows
    mock_rows = [
        {"Status": "VALSTART", "status morning": "", "product_name": "INDIHOME", "TIM": "TEAM A"},
        {"Status": "ACTCOMP", "status morning": "", "product_name": "INDIHOME", "TIM": "TEAM A"},
        {"Status": "VALCOMP", "status morning": "", "product_name": "INDIHOME", "TIM": "TEAM A"},
        {"Status": "STARTWORK", "status morning": "PROSES SETTING", "product_name": "INDIHOME", "TIM": "TEAM B"},
        {"Status": "COMPWORK", "status morning": "DONE", "product_name": "INDIHOME", "tgl_ps_parsed": "2026-04-04", "TIM": "TEAM C"}
    ]
    
    # today_rows (only COMPWORK for today)
    today_rows = [mock_rows[4]]
    
    summary = build_summary(mock_rows, today_rows)
    
    print(f"Total Potensi: {summary['total_potensi']}")
    print(f"Potensi Breakdown: {summary['potensi_breakdown']}")
    
    # Expected: 4 (VALSTART, ACTCOMP, VALCOMP, PROSES SETTING)
    if summary['total_potensi'] == 4:
        print("SUCCESS: Potensi logic correctly counts PROSES SETTING and basic statuses.")
    else:
        print(f"FAILURE: Expected 4, got {summary['total_potensi']}")

if __name__ == "__main__":
    test_potensi_logic()
