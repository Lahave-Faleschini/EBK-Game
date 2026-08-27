import pandas as pd
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
fpath = BASE_DIR / "College_Football_Rosters.xlsx"

if not fpath.exists():
    print(f"File not found at {fpath} — check the exact filename in your API folder")
    raise SystemExit(1)

df = pd.read_excel(fpath)
print(f"Total rows in College_Football_Rosters.xlsx: {len(df):,}")
print(f"Distinct schools: {df['School'].nunique()}")
print(f"Distinct seasons: {sorted(df['Season'].unique())}\n")

# Check for players appearing on 2+ different schools in the SAME season —
# same contamination signal we used for basketball. A player can transfer
# between seasons, but not exist on two rosters within one season.
by_player_year = defaultdict(set)
for _, row in df.iterrows():
    player = row["Player"]
    season = row["Season"]
    school = row["School"]
    if pd.isna(player) or pd.isna(season) or pd.isna(school):
        continue
    by_player_year[(player, season)].add(school)

contaminated = {k: v for k, v in by_player_year.items() if len(v) > 1}

print(f"Total (player, season) pairs: {len(by_player_year):,}")
print(f"Contaminated (player, season) pairs found: {len(contaminated):,}")

if contaminated:
    print("\nSample of contaminated entries (first 20):")
    for (player, season), schools in list(contaminated.items())[:20]:
        print(f"  {season} — {player} — {sorted(schools)}")
else:
    print("\n✓ No same-season multi-team contamination found — the in-scrape validation appears to have worked.")

# Also check for missing/empty critical fields as a basic sanity check
missing_player = df["Player"].isna().sum()
missing_school = df["School"].isna().sum()
print(f"\nRows with missing Player: {missing_player}")
print(f"Rows with missing School: {missing_school}")