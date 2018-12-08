import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_db import *
 
engine = create_engine('sqlite:///notes.db', echo=True)
 
Session = sessionmaker(bind=engine)
session = Session()
 
user = User("admin","password","user@example.com")
session.add(user)
session.commit()