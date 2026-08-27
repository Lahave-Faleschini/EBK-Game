from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Team, TeamAlias, Player, roster, Jersey_Number

app = FastAPI()

# find a team by name or alias 
def find_team(name: str, db: Session):
    n = name.strip()

    # Try direct name match first
    team = db.query(Team).filter(
        Team.name.ilike(f"%{n}%")
    ).first()
    if team:
        return team

    # Try alias match
    alias = db.query(TeamAlias).filter(
        TeamAlias.alias.ilike(f"%{n}%")
    ).first()
    if alias:
        return db.query(Team).filter(Team.id == alias.team_id).first()

    return None


# Validate a team 
@app.get("/validate/team")
def validate_team(name: str, db: Session = Depends(get_db)):
    team = find_team(name, db)
    if team:
        return {"valid": True, "team": team.name, "league": team.league}
    return {"valid": False, "reason": f"'{name}' is not a recognized team"}


# Validate a player 
@app.get("/validate/player")
def validate_player(name: str, team: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.name.ilike(f"%{name}%")).first()
    if not player:
        return {"valid": False, "reason": f"Player '{name}' not found"}

    team_obj = find_team(team, db)
    if not team_obj:
        return {"valid": False, "reason": f"Team '{team}' not found"}

    # Did this player actually play for this team? (pro roster OR college roster OR college_id match)
    played_here = db.query(roster).filter(
        roster.player_id == player.id,
        roster.team_id == team_obj.id
    ).first()
    college_match = (player.college_id == team_obj.id)

    if not played_here and not college_match:
        return {"valid": False, "reason": f"{player.name} never played for {team_obj.name}"}

    # If the team is a college (NCAA football or NCAAB basketball), we ALSO need to confirm they went pro
    if team_obj.league in ("NCAA", "NCAAB"):
        pro_roster_entry = db.query(roster).join(Team, roster.team_id == Team.id).filter(
            roster.player_id == player.id,
            Team.league.in_(["NBA", "NFL"])
        ).first()

        if not pro_roster_entry:
            return {"valid": False, "reason": f"{player.name} played for {team_obj.name} but never went pro"}

    return {"valid": True, "player": player.name, "team": team_obj.name}


# Validate a jersey number 
@app.get("/validate/jersey")
def validate_jersey(player: str, number: int, db: Session = Depends(get_db)):
    player_obj = db.query(Player).filter(
        Player.name.ilike(f"%{player}%")
    ).first()
    if not player_obj:
        return {"valid": False, "reason": f"Player '{player}' not found"}

    jersey = db.query(Jersey_Number).filter(
        Jersey_Number.player_id == player_obj.id,
        Jersey_Number.number == number
    ).first()

    if jersey:
        return {"valid": True, "player": player_obj.name, "number": number}
    return {"valid": False, "reason": f"{player_obj.name} never wore #{number}"}


# Validate teammates 
@app.get("/validate/teammate")
def validate_teammate(player1: str, player2: str, db: Session = Depends(get_db)):
    p1 = db.query(Player).filter(Player.name.ilike(f"%{player1}%")).first()
    p2 = db.query(Player).filter(Player.name.ilike(f"%{player2}%")).first()

    if not p1:
        return {"valid": False, "reason": f"Player '{player1}' not found"}
    if not p2:
        return {"valid": False, "reason": f"Player '{player2}' not found"}

    # Get all roster entries for p1
    p1_rosters = db.query(roster).filter(roster.player_id == p1.id).all()

    for entry in p1_rosters:
        overlap = db.query(roster).filter(
            roster.player_id == p2.id,
            roster.team_id == entry.team_id,
            roster.year == entry.year
        ).first()

        if overlap:
            team = db.query(Team).filter(Team.id == entry.team_id).first()
            return {
                "valid": True,
                "team": team.name,
                "year": entry.year
            }

    return {"valid": False, "reason": f"{p1.name} and {p2.name} were never teammates"}


#  Validate number player
@app.get("/validate/number_player")
def validate_number_player(player: str, number: int, db: Session = Depends(get_db)):
    player_obj = db.query(Player).filter(
        Player.name.ilike(f"%{player}%")
    ).first()
    if not player_obj:
        return {"valid": False, "reason": f"Player '{player}' not found"}

    jersey = db.query(Jersey_Number).filter(
        Jersey_Number.player_id == player_obj.id,
        Jersey_Number.number == number
    ).first()

    if jersey:
        return {"valid": True, "player": player_obj.name, "number": number}
    return {"valid": False, "reason": f"{player_obj.name} never wore #{number}"}