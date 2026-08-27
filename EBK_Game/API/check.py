import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Test a couple of schools using their BASKETBALL team_ids from POWER5_SCHOOLS,
# to see if football uses the same id or a different one.
test_schools = {
    "Ohio State": 194,   # basketball id
    "Boston College": 103,  # basketball id
    "Alabama": 333,       # basketball id
}

season = 2023  # a normal, well-covered season to sanity check against

for school_name, bball_id in test_schools.items():
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/{season}/teams/{bball_id}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f"\n=== {school_name} (using basketball id {bball_id}) ===")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Team name returned by football API: {data.get('displayName', '?')}")
    else:
        print("This id does not resolve to a valid football team at this endpoint.")