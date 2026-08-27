import pandas as pd
from database import engine, SessionLocal
from models import Base, Team, TeamAlias, Player, roster, Jersey_Number

Base.metadata.create_all(engine)
db = SessionLocal()

print("Reading NFL Excel file...")
df = pd.read_excel("../NFL_Rosters_1999_Present.xlsx")
print(f"Found {len(df):,} rows — importing...")

# nflverse uses team abbreviations (e.g. "KC", "BUF") — map them to full names
NFL_TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
    "OAK": "Las Vegas Raiders", "SD": "Los Angeles Chargers", "STL": "Los Angeles Rams",
}

NFL_ALIASES = {
    "Las Vegas Raiders": ["Raiders", "Oakland Raiders", "LV", "OAK"],
    "Los Angeles Chargers": ["Chargers", "San Diego Chargers", "LAC", "SD"],
    "Los Angeles Rams": ["Rams", "St. Louis Rams", "LAR", "STL"],
    "Washington Commanders": ["Commanders", "Washington Redskins", "Washington Football Team", "WAS"],
    "Tennessee Titans": ["Titans", "Houston Oilers", "TEN"],
}

# ── STEP 1: Insert teams ──────────────────────────────────
team_cache = {}

for code in df["team"].dropna().unique():
    full_name = NFL_TEAM_NAMES.get(code, code)
    existing = db.query(Team).filter(Team.name == full_name).first()
    if existing:
        team_cache[code] = existing
    else:
        new_team = Team(name=full_name, league="NFL")
        db.add(new_team)
        db.flush()
        team_cache[code] = new_team

db.commit()
print(f"✓ {len(team_cache)} NFL teams inserted/found")

# ── STEP 2: Insert NFL aliases ─────────────────────────────
alias_count = 0
for team_name, alias_list in NFL_ALIASES.items():
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        continue
    for alias in alias_list:
        existing = db.query(TeamAlias).filter(
            TeamAlias.team_id == team.id,
            TeamAlias.alias == alias
        ).first()
        if not existing:
            db.add(TeamAlias(team_id=team.id, alias=alias))
            alias_count += 1

db.commit()
print(f"✓ {alias_count} NFL aliases inserted")

# ── STEP 3: Insert players ────────────────────────────────
player_cache = {}

for player_name in df["full_name"].dropna().unique():
    existing = db.query(Player).filter(Player.name == player_name).first()
    if existing:
        player_cache[player_name] = existing
    else:
        player_rows = df[df["full_name"] == player_name]
        college_name = player_rows["college"].iloc[0]

        college_team = None
        if pd.notna(college_name) and str(college_name).strip() != "":
            college_team = db.query(Team).filter(
                Team.name.ilike(f"%{college_name}%")
            ).first()
            if not college_team:
                college_team = Team(name=str(college_name), league="NCAA")
                db.add(college_team)
                db.flush()

        new_player = Player(
            name=player_name,
            college_id=college_team.id if college_team else None
        )
        db.add(new_player)
        db.flush()
        player_cache[player_name] = new_player

db.commit()
print(f"✓ {len(player_cache)} NFL players inserted")

# ── STEP 4: Insert rosters and jersey numbers ─────────────
roster_count = 0
jersey_count = 0
roster_seen = set()
jersey_seen = set()

for _, row in df.iterrows():
    player_name = row["full_name"]
    team_code = row["team"]
    season = row["season"]
    jersey = row["jersey_number"]

    if pd.isna(player_name) or pd.isna(team_code) or pd.isna(season):
        continue

    player = player_cache.get(player_name)
    team = team_cache.get(team_code)

    if not player or not team:
        continue

    year = int(season)

    roster_key = (player.id, team.id, year)
    if roster_key not in roster_seen:
        db.add(roster(player_id=player.id, team_id=team.id, year=year))
        roster_seen.add(roster_key)
        roster_count += 1

    if pd.notna(jersey):
        try:
            jersey_num = int(jersey)
            jersey_key = (player.id, team.id, jersey_num)
            if jersey_key not in jersey_seen:
                db.add(Jersey_Number(player_id=player.id, team_id=team.id, number=jersey_num))
                jersey_seen.add(jersey_key)
                jersey_count += 1
        except:
            pass

    if roster_count % 1000 == 0 and roster_count > 0:
        db.commit()
        print(f"  {roster_count:,} roster entries processed...")

db.commit()
db.close()

print(f"\n✓ All done!")
print(f"  Teams:          {len(team_cache):,}")
print(f"  Players:        {len(player_cache):,}")
print(f"  Roster entries: {roster_count:,}")
print(f"  Jersey numbers: {jersey_count:,}")