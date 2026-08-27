import pandas as pd
from pathlib import Path
import sys

if len(sys.argv) < 2:
    print("Usage: python check_cbb_source.py <player name substring>")
    sys.exit(1)

search = sys.argv[1].lower()
BASE_DIR = Path(__file__).parent
fpath = BASE_DIR / "College_Basketball_Rosters.xlsx"

if not fpath.exists():
    print(f"File not found at {fpath} — check the exact filename in your API folder")
    sys.exit(1)

df = pd.read_excel(fpath)
matches = df[df["Player"].astype(str).str.lower().str.contains(search, na=False)]

print(f"=== College_Basketball_Rosters.xlsx ===")
if matches.empty:
    print(f"No rows matching '{search}'")
else:
    for _, row in matches.iterrows():
        print(f"  {row['Season']} — {row['Player']} — {row['School']} — #{row['Jersey Number']}")