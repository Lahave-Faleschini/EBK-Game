import pandas as pd
from database import engine, SessionLocal
from models import Base, Team, TeamAlias, Player, roster, Jersey_Number

Base.metadata.create_all(engine)
db = SessionLocal()

print("Reading College Basketball Excel file...")
df = pd.read_excel("College_Basketball_Rosters.xlsx")
print(f"Found {len(df):,} rows — importing...")

# Columns expected: School, Season, Player, Jersey Number, Position, Height, Weight

# ── STEP 1: Insert teams (schools) ────────────────────────
team_cache = {}

for school_name in df["School"].dropna().unique():
    existing = db.query(Team).filter(Team.name == school_name).first()
    if existing:
        team_cache[school_name] = existing
    else:
        new_team = Team(name=school_name, league="NCAAB")
        db.add(new_team)
        db.flush()
        team_cache[school_name] = new_team

db.commit()
print(f"✓ {len(team_cache)} college teams inserted/found")

# ── STEP 2: Insert players ────────────────────────────────
# college_id = the school the player first appears under (for basketball,
# the roster team IS the college, unlike NFL where college was separate)
player_cache = {}

for player_name in df["Player"].dropna().unique():
    existing = db.query(Player).filter(Player.name == player_name).first()
    if existing:
        player_cache[player_name] = existing
    else:
        player_rows = df[df["Player"] == player_name]
        school_name = player_rows["School"].iloc[0]
        school_team = team_cache.get(school_name)

        new_player = Player(
            name=player_name,
            college_id=school_team.id if school_team else None
        )
        db.add(new_player)
        db.flush()
        player_cache[player_name] = new_player

db.commit()
print(f"✓ {len(player_cache)} college players inserted")

# ── STEP 3: Insert rosters and jersey numbers ─────────────
roster_count = 0
jersey_count = 0
roster_seen = set()
jersey_seen = set()

for _, row in df.iterrows():
    player_name = row["Player"]
    school_name = row["School"]
    season = row["Season"]
    jersey = row["Jersey Number"]

    if pd.isna(player_name) or pd.isna(school_name) or pd.isna(season):
        continue

    player = player_cache.get(player_name)
    team = team_cache.get(school_name)

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
        except (ValueError, TypeError):
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
    