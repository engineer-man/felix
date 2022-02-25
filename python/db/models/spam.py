from sqlalchemy import Column, Integer, String
from db.config import Base


class Spam(Base):
    __tablename__ = 'spam'
    id = Column(Integer, primary_key=True)
    member = Column(String, nullable=False)
    regex = Column(String, nullable=False)

class Spammer(Base):
    __tablename__ = 'spammer'
    id = Column(Integer, primary_key=True)
    member = Column(String, nullable=False)
    regex = Column(String, nullable=False)
