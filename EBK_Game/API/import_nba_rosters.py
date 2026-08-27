import pandas as pd
from pathlib import Path
from database import engine, SessionLocal
from models import Base, Team, TeamAlias, Player, roster, Jersey_Number

Base.metadata.create_all(engine)
db = SessionLocal()

print("Reading NBA Excel files...")

# Folder containing this script
BASE_DIR = Path(__file__).parent

files = [
    "NBA_Rosters_1947-1979.xlsx",
    "NBA_Rosters_1980_Present.xlsx",
    "NBA_Rosters2026.xlsx",      # Remove this line if you don't actually have this file
]

frames = []

for filename in files:
    filepath = BASE_DIR / filename

    if filepath.exists():
        print(f"  ✓ Loaded {filename}")
        frames.append(pd.read_excel(filepath))
    else:
        print(f"  ⚠ Skipped {filename} (not found)")

# Stop if nothing was loaded
if len(frames) == 0:
    raise FileNotFoundError(
        f"""
No Excel files were found.

Current folder:
{BASE_DIR}

Files in this folder:
{[f.name for f in BASE_DIR.glob('*')]}

Make sure your Excel files are located in the same folder as import_nba_rosters.py.
"""
    )

df = pd.concat(frames, ignore_index=True)

before = len(df)

df = df.drop_duplicates(
    subset=["Season", "Team", "Player", "Jersey Number"],
    keep="first"
)

print(f"Combined: {before:,} rows → {len(df):,} after removing overlap duplicates")