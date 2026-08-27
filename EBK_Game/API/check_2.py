from database import SessionLocal
from models import Team, Player, roster, Jersey_Number
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("COLLEGE BASKETBALL IMPORT VERIFICATION")
print("=" * 60)

# ── Overall counts ────────────────────────────────────────
ncaab_teams = db.query(Team).filter(Team.league == "NCAAB").count()
print(f"\nTotal NCAAB teams: {ncaab_teams}")

# ── List all teams (so you can confirm coverage) ──────────
print("\nAll NCAAB teams in DB:")
teams = db.query(Team).filter(Team.league == "NCAAB").order_by(Team.name).all()
for t in teams:
    print(f"  - {t.name}")

# ── Roster counts per team ─────────────────────────────────
print("\nRoster entries per team:")
results = (
    db.query(Team.name, func.count(roster.id))
    .join(roster, roster.team_id == Team.id)
    .filter(Team.league == "NCAAB")
    .group_by(Team.name)
    .order_by(func.count(roster.id).desc())
    .all()
)
for name, count in results:
    print(f"  {name:35s} {count:>5,} roster entries")

# ── Any NCAAB team with zero roster entries? ──────────────
teams_with_rosters = {name for name, _ in results}
empty_teams = [t.name for t in teams if t.name not in teams_with_rosters]
if empty_teams:
    print(f"\n⚠ Teams with 0 roster entries: {empty_teams}")
else:
    print("\n✓ Every NCAAB team has at least one roster entry")

# ── Sample: pull one team's full roster for a season ──────
if teams:
    sample_team = teams[0]
    sample_year = (
        db.query(roster.year)
        .filter(roster.team_id == sample_team.id)
        .order_by(roster.year.desc())
        .first()
    )
    if sample_year:
        year = sample_year[0]
        print(f"\nSample roster — {sample_team.name}, {year}:")
        rows = (
            db.query(Player.name, Jersey_Number.number)
            .join(roster, roster.player_id == Player.id)
            .outerjoin(
                Jersey_Number,
                (Jersey_Number.player_id == Player.id) & (Jersey_Number.team_id == sample_team.id)
            )
            .filter(roster.team_id == sample_team.id, roster.year == year)
            .all()
        )
        for name, number in rows:
            jersey_str = f"#{number}" if number is not None else "#--"
            print(f"  {jersey_str:5s} {name}")

# ── Check for duplicate players (same name, might be different people) ──
print("\nChecking for potential duplicate player names...")
dupes = (
    db.query(Player.name, func.count(Player.id))
    .group_by(Player.name)
    .having(func.count(Player.id) > 1)
    .all()
)
if dupes:
    print(f"  ⚠ {len(dupes)} player names appear more than once in Player table:")
    for name, count in dupes[:10]:
        print(f"    - {name} ({count}x)")
    if len(dupes) > 10:
        print(f"    ... and {len(dupes) - 10} more")
else:
    print("  ✓ No duplicate player names found")

db.close()
print("\nDone.")