from database import SessionLocal
from models import Player, Team, roster
from collections import defaultdict

db = SessionLocal()

TEAM_A = "TCU"
TEAM_B = "Washington"

rows = (
    db.query(roster.player_id, roster.year, Team.name)
    .join(Team, roster.team_id == Team.id)
    .filter(Team.league == "NCAAB")
    .all()
)

by_player_year = defaultdict(set)
for player_id, year, team_name in rows:
    by_player_year[(player_id, year)].add(team_name)

print(f"Player-seasons where both '{TEAM_A}' and '{TEAM_B}' appear:\n")
for (player_id, year), teams in by_player_year.items():
    if TEAM_A in teams and TEAM_B in teams:
        p = db.query(Player).filter(Player.id == player_id).first()
        print(f"  {year} — {p.name} (player_id={player_id})")

db.close()