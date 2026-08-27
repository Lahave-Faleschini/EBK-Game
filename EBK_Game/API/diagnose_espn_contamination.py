import requests
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}

team_id = 103   # Boston College
season = 2006

url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/{season}/teams/{team_id}/athletes"
r = requests.get(url, headers=HEADERS, timeout=10)
print(f"Status: {r.status_code}")
data = r.json()
refs = [item["$ref"] for item in data.get("items", [])]
print(f"Athlete count returned: {len(refs)}\n")

print("Fetching each athlete's name + checking for a team reference in their raw data...\n")
for ref in refs:
    detail_r = requests.get(ref, headers=HEADERS, timeout=10)
    if detail_r.status_code != 200:
        continue
    detail = detail_r.json()
    name = detail.get("fullName", "?")

    # Look for any team reference embedded in the athlete's own record
    team_ref = detail.get("team", {}).get("$ref", "NO TEAM FIELD PRESENT")
    print(f"{name}: team field in athlete detail = {team_ref}")