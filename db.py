from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from datetime import date

DATABASE_URL = os.environ.get("DATABASE_URL") 
engine = create_engine(DATABASE_URL)

Base = declarative_base()

class PlayerSession(Base):
    __tablename__ = 'player_sessions'
    
    id = Column(Integer, primary_key=True)
    slack_user_id = Column(String, nullable=False)
    play_date = Column(Date, default=date.today)
    guesses = Column(String, default="")
    guess_strings = Column(String, default="")
    done = Column(Boolean, default=False)
    yellows = Column(String, default="")
    greens = Column(String, default="")
    grays = Column(String, default="")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)