from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash
 
engine = create_engine('sqlite:///notes.db', echo=True)
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
 
from flask_login import UserMixin

# User class is for storing user records with user name, email and hashed password
class User(UserMixin, Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True)
    username = Column(String(64), index=True, unique=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))
    notes = relationship('Note', backref='author', lazy='dynamic')
 
    def __init__(self, username, password, email):
        self.username = username
        self.password = self.set_password(password)
        self.email = email

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Notes have associated user_id and categories         
class Note(Base):
    __tablename__ = "notes"
 
    id = Column(Integer, primary_key=True)
    note = Column(String)
    category = Column(String)
    user_id = Column(ForeignKey(User.id))

    def __init__(self, user_id, note, category):
        self.user_id = user_id
        self.note = note
        self.category = category

# create DB tables
Base.metadata.create_all(engine)