from database import SessionLocal
from models import Team, roster
from sqlalchemy import func
 
db = SessionLocal()
 
team = db.query(Team).filter(Team.name == "Minnesota Timberwolves").first()
if not team:
    print("No 'Minnesota Timberwolves' Team row exists at all!")
else:
    print(f"Team found: id={team.id}, league={team.league}")
    count = db.query(roster).filter(roster.team_id == team.id).count()
    print(f"Total roster rows pointing to this team: {count}")
 
    if count > 0:
        years = db.query(roster.year, func.count(roster.id)).filter(
            roster.team_id == team.id
        ).group_by(roster.year).order_by(roster.year).all()
        print("\nRoster rows by year:")
        for year, cnt in years:
            print(f"  {year}: {cnt} players")
 
# Also do a broader NBA-wide sanity check: total NBA roster rows vs total unique
# (team, year) combos, to see if certain years/teams are systematically empty
nba_team_ids = [t.id for t in db.query(Team).filter(Team.league == "NBA").all()]
total_nba_roster = db.query(roster).filter(roster.team_id.in_(nba_team_ids)).count()
print(f"\nTotal NBA roster rows (all teams): {total_nba_roster:,}")
 
db.close()






