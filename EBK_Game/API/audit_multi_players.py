from database import SessionLocal
from models import Player, Team, roster
from sqlalchemy import func

db = SessionLocal()

print("Auditing players with roster history spanning multiple teams...")

# Find players with more than one distinct team in their roster history
multi_team = (
    db.query(roster.player_id, func.count(func.distinct(roster.team_id)).label("team_count"))
    .group_by(roster.player_id)
    .having(func.count(func.distinct(roster.team_id)) > 1)
    .all()
)

print(f"\nPlayers with 2+ distinct teams in roster table: {len(multi_team)}")

# Sample a handful and show their full history
print("\nSample of 15 multi-team players:")
for player_id, team_count in multi_team[:15]:
    p = db.query(Player).filter(Player.id == player_id).first()
    rows = db.query(roster).filter(roster.player_id == player_id).order_by(roster.year).all()
    print(f"\n{p.name} (id={p.id}) — {team_count} distinct teams, {len(rows)} roster rows:")
    for r in rows:
        team = db.query(Team).filter(Team.id == r.team_id).first()
        print(f"  {r.year} — {team.name} ({team.league})")

# Also check: total roster rows vs total distinct (player, team, year) combos
# to see if any wholesale deletion happened
total_rows = db.query(roster).count()
print(f"\nTotal roster rows in DB: {total_rows:,}")

db.close()