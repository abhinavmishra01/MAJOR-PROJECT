'''
This file contains the database models and the database connection code.
'''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import relationship, backref
from sqlalchemy import func
from datetime import datetime

DB_NAME = 'database.sqlite'
DB_URL = f'sqlite:///{DB_NAME}'

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    email = Column(String(64), nullable=False, unique=True)
    password = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def verify_password(self, password):
        return self.password == password
    
    def __repr__(self):
        return f'<User {self.name}>'
    
    def __str__(self):
        return self.name

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    city = Column(String(64), default='Lucknow')
    gender = Column(String(2), default='M')
    avatar = Column(String(255), nullable=False)
    # todo add more fields
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __repr__(self):
        return f'<Profile {self.user.name}>'
    
    def __str__(self):
        return self.user.name
    
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    path = Column(String(255))
    added_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime,default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"{self.id}|{self.path}|{self.added_by}"
 
    
def opendb():
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()

if __name__ == '__main__':
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)
    