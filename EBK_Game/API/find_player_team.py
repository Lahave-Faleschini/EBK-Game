import sys
from database import SessionLocal
from models import Player, Team, roster

if len(sys.argv) < 2:
    print("Usage: python find_player_team.py <player name>")
    sys.exit(1)

name = sys.argv[1]
db = SessionLocal()

players = db.query(Player).filter(Player.name.ilike(f"%{name}%")).all()

if not players:
    print(f"No player found matching '{name}'")
else:
    for p in players:
        print(f"\nPlayer: {p.name} (id={p.id})")
        rosters = db.query(roster).filter(roster.player_id == p.id).all()
        for r in rosters:
            team = db.query(Team).filter(Team.id == r.team_id).first()
            print(f"  {r.year} — {team.name} ({team.league})")

db.close()