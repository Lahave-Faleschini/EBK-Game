import pandas as pd
from database import engine, SessionLocal
from models import Base, Team, TeamAlias, Player, roster, Jersey_Number

Base.metadata.create_all(engine)
db = SessionLocal()

ALIASES = {
    "Brooklyn Nets": ["Nets", "New Jersey Nets", "NJ Nets", "BKN", "BRK"],
    "Oklahoma City Thunder": ["Thunder", "OKC", "Seattle SuperSonics", "SuperSonics", "Seattle"],
    "New Orleans Pelicans": ["Pelicans", "New Orleans Hornets", "NO Hornets", "NOP"],
    "Memphis Grizzlies": ["Grizzlies", "Vancouver Grizzlies", "Vancouver", "MEM"],
    "Washington Wizards": ["Wizards", "Washington Bullets", "Bullets", "WAS"],
    "Charlotte Hornets": ["Hornets", "Charlotte Bobcats", "Bobcats", "CHA"],
    "Utah Jazz": ["Jazz", "New Orleans Jazz", "UTA"],
    "Sacramento Kings": ["Kings", "Kansas City Kings", "Cincinnati Royals", "Rochester Royals", "SAC"],
    "Atlanta Hawks": ["Hawks", "St. Louis Hawks", "Milwaukee Hawks", "Tri-Cities Blackhawks", "ATL"],
    "Golden State Warriors": ["Warriors", "San Francisco Warriors", "Philadelphia Warriors", "GSW"],
    "Los Angeles Lakers": ["Lakers", "Minneapolis Lakers", "LAL"],
    "Los Angeles Clippers": ["Clippers", "San Diego Clippers", "Buffalo Braves", "LAC"],
    "Houston Rockets": ["Rockets", "San Diego Rockets", "HOU"],
    "Phoenix Suns": ["Suns", "PHO", "PHX"],
    "Dallas Mavericks": ["Mavericks", "Mavs", "DAL"],
    "Miami Heat": ["Heat", "MIA"],
    "Chicago Bulls": ["Bulls", "CHI"],
    "Boston Celtics": ["Celtics", "BOS"],
    "San Antonio Spurs": ["Spurs", "SAS"],
    "Denver Nuggets": ["Nuggets", "DEN"],
    "Minnesota Timberwolves": ["Timberwolves", "Wolves", "MIN"],
    "Portland Trail Blazers": ["Trail Blazers", "Blazers", "POR"],
    "Toronto Raptors": ["Raptors", "TOR"],
    "Philadelphia 76ers": ["76ers", "Sixers", "PHI", "Syracuse Nationals"],
    "Detroit Pistons": ["Pistons", "Fort Wayne Pistons", "DET"],
    "Indiana Pacers": ["Pacers", "IND"],
    "Milwaukee Bucks": ["Bucks", "MIL"],
    "Cleveland Cavaliers": ["Cavaliers", "Cavs", "CLE"],
    "New York Knicks": ["Knicks", "NYK"],
    "Orlando Magic": ["Magic", "ORL"],
    "New Orleans Pelicans": ["Pelicans", "NOP"],
}

print("Reading excel file... 8==>")
df = pd.read_excel("../NBA_Rosters2026.xlsx")
print(f"Found {len(df):,} rows importing...")

# Adding all new teams that have not been accounted for
team_cache = {}

for team_name in df["Team"].unique():
    existing = db.query(Team).filter(Team.name == team_name).first()
    if existing:
        team_cache[team_name] = existing
    else:
        new_team = Team(name=team_name, league = "NBA")
        db.add(new_team)
        db.flush()
        team_cache[team_name] = new_team

db.commit()
print(f"✓ {len(team_cache)} teams inserted")

# inserting aliases(teams that have rebranded or changed name or abbreviation)

alias_count = 0
for team_name, alias_list in ALIASES.items():
    # Find the team — try cache first, then database
    team = team_cache.get(team_name)
    if not team:
        team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        # Team not in database yet — add it
        team = Team(name=team_name, league="NBA")
        db.add(team)
        db.flush()
        team_cache[team_name] = team

    for alias in alias_list:
        existing = db.query(TeamAlias).filter(
            TeamAlias.team_id == team.id,
            TeamAlias.alias == alias
        ).first()
        if not existing:
            db.add(TeamAlias(team_id=team.id, alias=alias))
            alias_count += 1

db.commit()
print(f"✓ {alias_count} aliases inserted")

# inserting all new players

player_cache = {}
for player_name in df["Player"].unique():
    existing = db.query(Player).filter(Player.name == player_name).first()
    if existing:
        player_cache[player_name] = existing
    else:
        # Get college from first row for this player
        player_rows = df[df["Player"] == player_name]
        college_name = player_rows["College"].iloc[0]

        college_team = None
        if pd.notna(college_name) and str(college_name).strip() != "":
            # Check if college already exists as a team
            college_team = db.query(Team).filter(
                Team.name.ilike(f"%{college_name}%")
            ).first()
            # If not, add it
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
print(f"✓ {len(player_cache)} players added")

#adding rosters and jersey numbers
roster_count  = 0
jersey_count  = 0
roster_seen   = set()  
jersey_seen   = set()



for _, row in df.iterrows():
    player_name = row["Player"]
    team_name   = row["Team"]
    season      = row["Season"]  # "1980-81"
    jersey      = row["Jersey Number"]

    try:
        year = int(str(season).split("-")[0])
    except:
        continue

    player = player_cache.get(player_name)
    team   = team_cache.get(team_name)

    if not player or not team:
        continue

    # Roster entry
    roster_key = (player.id, team.id, year)
    if roster_key not in roster_seen:
        db.add(roster(player_id=player.id, team_id=team.id, year=year))
        roster_seen.add(roster_key)
        roster_count += 1

    # Jersey number
    try:
        jersey_num = int(str(jersey).strip())
        jersey_key = (player.id, team.id, jersey_num)
        if jersey_key not in jersey_seen:
            db.add(Jersey_Number(player_id=player.id, team_id=team.id, number=jersey_num))
            jersey_seen.add(jersey_key)
            jersey_count += 1
    except:
        pass

    # Commit every 1000 rows to keep memory usage low
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
print(f"\nDatabase is ready — run uvicorn main:app --reload to start your API")