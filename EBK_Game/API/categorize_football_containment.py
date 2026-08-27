import pandas as pd
from pathlib import Path
from collections import defaultdict
import re

BASE_DIR = Path(__file__).parent
df = pd.read_excel(BASE_DIR / "College_Football_Rosters.xlsx")

by_player_year = defaultdict(set)
for _, row in df.iterrows():
    player = row["Player"]
    season = row["Season"]
    school = row["School"]
    if pd.isna(player) or pd.isna(season) or pd.isna(school):
        continue
    by_player_year[(player, season)].add(school)

contaminated = {k: v for k, v in by_player_year.items() if len(v) > 1}

# A "junk" name: starts with a dash, is very short, or is mostly non-alphabetic
def looks_like_junk(name):
    name = str(name).strip()
    if name.startswith("-"):
        return True
    if len(name) <= 3:
        return True
    letters = sum(c.isalpha() for c in name)
    if letters < len(name) * 0.5:  # less than half the characters are letters
        return True
    return False

junk = {k: v for k, v in contaminated.items() if looks_like_junk(k[0])}
real_names = {k: v for k, v in contaminated.items() if not looks_like_junk(k[0])}

print(f"Total contaminated (player, season) pairs: {len(contaminated)}")
print(f"  Junk/placeholder names: {len(junk)}")
print(f"  Real-looking names: {len(real_names)}")

print(f"\n--- Real-looking name collisions (first 40) ---")
for (player, season), schools in list(real_names.items())[:40]:
    print(f"  {season} — {player} — {sorted(schools)}")

print(f"\nTotal junk rows in the ORIGINAL dataframe (not just contaminated pairs):")
junk_row_count = df["Player"].apply(looks_like_junk).sum()
print(f"  {junk_row_count:,} out of {len(df):,} total rows look like junk/placeholder entries")