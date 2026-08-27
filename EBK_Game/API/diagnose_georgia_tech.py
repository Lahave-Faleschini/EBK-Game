import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
season = 2015  # Marcus Allen / Zach Allen both show up this year

teams_to_check = {
    "Georgia Tech": 59,
    "Penn State": 213,
}

for school_name, team_id in teams_to_check.items():
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{season}/teams/{team_id}/athletes"
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f"\n=== {school_name} (team_id={team_id}), season {season} — status {r.status_code} ===")
    if r.status_code != 200:
        continue
    data = r.json()
    refs = [item["$ref"] for item in data.get("items", [])]
    print(f"Athlete count: {len(refs)}")

    for ref in refs:
        detail_r = requests.get(ref, headers=HEADERS, timeout=10)
        if detail_r.status_code != 200:
            continue
        detail = detail_r.json()
        name = detail.get("fullName", "?")
        team_ref = detail.get("team", {}).get("$ref", "NO TEAM FIELD")
        print(f"  {name}: team field = {team_ref}")