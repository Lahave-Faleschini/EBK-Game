import pandas as pd
from pathlib import Path
import sys

if len(sys.argv) < 2:
    print("Usage: python check_source_data.py <player name substring>")
    sys.exit(1)

search = sys.argv[1].lower()

BASE_DIR = Path(__file__).parent
files = [
    "NBA_Rosters_1947-1979.xlsx",
    "NBA_Rosters_1980_Present.xlsx",
    "NBA_Rosters2026.xlsx",
]

for fname in files:
    fpath = BASE_DIR / fname
    if not fpath.exists():
        print(f"\n=== {fname} === (not found, skipping)")
        continue

    df = pd.read_excel(fpath)
    matches = df[df["Player"].astype(str).str.lower().str.contains(search, na=False)]

    print(f"\n=== {fname} ===")
    if matches.empty:
        print(f"  No rows matching '{search}'")
    else:
        for _, row in matches.iterrows():
            print(f"  {row['Season']} — {row['Player']} — {row['Team']} — #{row['Jersey Number']}")