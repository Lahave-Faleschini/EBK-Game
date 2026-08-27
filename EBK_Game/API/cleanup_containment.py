import requests
import time
from collections import defaultdict
from database import SessionLocal
from models import Player, Team, roster, Jersey_Number

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Same mapping as your original scraper — needed to know each school's ESPN team_id
POWER5_SCHOOLS = {
    "Boston College": 103, "Clemson": 228, "Duke": 150, "Florida State": 52,
    "Georgia Tech": 59, "Louisville": 97, "Miami": 2390, "North Carolina": 153,
    "NC State": 152, "Pittsburgh": 221, "Syracuse": 183, "Virginia": 258,
    "Virginia Tech": 259, "Wake Forest": 154,
    "Illinois": 356, "Iowa": 2294, "Indiana": 84, "Maryland": 120,
    "Michigan": 130, "Michigan State": 127, "Minnesota": 135, "Nebraska": 158,
    "Northwestern": 77, "Ohio State": 194, "Penn State": 213, "Purdue": 2509,
    "Rutgers": 164, "Wisconsin": 275,
    "Baylor": 239, "BYU": 252, "Cincinnati": 2132, "Houston": 248,
    "Iowa State": 66, "Kansas": 2305, "Kansas State": 2306, "Oklahoma": 201,
    "Oklahoma State": 197, "TCU": 2628, "Texas": 251, "Texas Tech": 2641,
    "UCF": 2116, "West Virginia": 277,
    "Arizona": 12, "Arizona State": 9, "Cal": 25, "Colorado": 38,
    "Oregon": 2483, "Oregon State": 204, "Stanford": 24, "UCLA": 26,
    "USC": 30, "Utah": 254, "Washington": 264, "Washington State": 265,
    "Alabama": 333, "Arkansas": 8, "Auburn": 2, "Florida": 57,
    "Georgia": 61, "Kentucky": 96, "LSU": 99, "Mississippi State": 344,
    "Missouri": 142, "Ole Miss": 145, "South Carolina": 2579, "Tennessee": 2633,
    "Texas A&M": 245, "Vanderbilt": 238,
}
TEAM_ID_TO_SCHOOL = {v: k for k, v in POWER5_SCHOOLS.items()}


def fetch_true_teams(team_id, season):
    """Returns {athlete_name: true_team_id} using each athlete's own record."""
    result = {}
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/teams/{team_id}/athletes"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return result
    refs = [item["$ref"] for item in r.json().get("items", [])]
    for ref in refs:
        dr = requests.get(ref, headers=HEADERS, timeout=10)
        if dr.status_code != 200:
            continue
        detail = dr.json()
        name = detail.get("fullName", "")
        team_ref = detail.get("team", {}).get("$ref", "")
        true_id = None
        if team_ref:
            try:
                true_id = int(team_ref.split("/teams/")[1].split("?")[0])
            except (IndexError, ValueError):
                pass
        if name and true_id:
            result[name] = true_id
        time.sleep(0.1)
    return result


db = SessionLocal()

print("Finding contaminated player-seasons...")
rows = (
    db.query(roster.player_id, roster.year, Team.name, Team.id)
    .join(Team, roster.team_id == Team.id)
    .filter(Team.league == "NCAAB")
    .all()
)

# IMPORTANT: keep the DB's internal Team.id (db_team_id) separate from ESPN's
# own team_id (looked up via POWER5_SCHOOLS by school name). They are NOT the same number.
by_player_year = defaultdict(list)  # (player_id, year) -> [(team_name, db_team_id), ...]
for player_id, year, team_name, db_team_id in rows:
    by_player_year[(player_id, year)].append((team_name, db_team_id))

contaminated = {k: v for k, v in by_player_year.items() if len({t[0] for t in v}) > 1}
print(f"Found {len(contaminated)} contaminated player-seasons\n")

# Group work by (year, set of ESPN team_ids involved) to minimize ESPN calls
groups = defaultdict(set)  # year -> set of ESPN team_ids to fetch
for (player_id, year), teams in contaminated.items():
    for team_name, db_team_id in teams:
        espn_id = POWER5_SCHOOLS.get(team_name)
        if espn_id:
            groups[year].add(espn_id)
        # if a team_name isn't in POWER5_SCHOOLS at all, we can't verify it via
        # this method — it'll just stay unresolved, which is the safe default

print("Fetching ground-truth team data from ESPN (this will take a while)...")
truth_cache = {}  # (year, espn_team_id) -> {name: true_espn_team_id}
for year, espn_ids in groups.items():
    for espn_id in espn_ids:
        school = TEAM_ID_TO_SCHOOL.get(espn_id, f"unknown({espn_id})")
        print(f"  Fetching {school}, {year}...")
        truth_cache[(year, espn_id)] = fetch_true_teams(espn_id, year)

print("\nApplying fixes...")
fixed = 0
unresolved = []

for (player_id, year), teams in contaminated.items():
    player = db.query(Player).filter(Player.id == player_id).first()

    # Build a combined truth map across all team fetches for this year,
    # using each candidate team's ESPN id (not the DB id) to look up truth_cache
    true_espn_team_id = None
    for team_name, db_team_id in teams:
        espn_id = POWER5_SCHOOLS.get(team_name)
        if espn_id is None:
            continue
        truth_map = truth_cache.get((year, espn_id), {})
        if player.name in truth_map:
            true_espn_team_id = truth_map[player.name]
            break

    if true_espn_team_id is None:
        unresolved.append((player.name, year, [t[0] for t in teams]))
        continue

    true_school = TEAM_ID_TO_SCHOOL.get(true_espn_team_id)
    if true_school is None:
        # Their real team isn't even in our Power 5 list — don't guess, log it
        unresolved.append((player.name, year, [t[0] for t in teams]))
        continue

    # Delete roster/jersey rows for the WRONG team(s), keep the correct one
    # (uses db_team_id here since that's what roster/Jersey_Number tables reference)
    for team_name, db_team_id in teams:
        if team_name != true_school:
            db.query(roster).filter(
                roster.player_id == player_id,
                roster.team_id == db_team_id,
                roster.year == year
            ).delete()
            db.query(Jersey_Number).filter(
                Jersey_Number.player_id == player_id,
                Jersey_Number.team_id == db_team_id
            ).delete()
            fixed += 1

db.commit()

print(f"\n✓ Fixed {fixed} incorrect roster rows")
print(f"⚠ {len(unresolved)} player-seasons could not be auto-resolved (logged below, nothing deleted):")
for name, year, teams in unresolved[:30]:
    print(f"  {year} — {name} — was tagged: {teams}")
if len(unresolved) > 30:
    print(f"  ...and {len(unresolved) - 30} more")

db.close()