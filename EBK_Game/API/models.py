from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key = True)
    name = Column(String)
    league = Column(String)
    
class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key= True)
    name = Column(String)
    college_id = Column(Integer, ForeignKey("teams.id"))

class roster(Base):
    __tablename__ = "rosters"
    id = Column(Integer, primary_key= True)
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    year = Column(Integer)

class Jersey_Number(Base):
    __tablename__ = "Jersey_Numbers"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    number = Column(Integer)
    
class TeamAlias(Base):
    __tablename__ = "team_aliases"
    id      = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    alias   = Column(String)