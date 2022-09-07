# DB SQLALCHEMY, CREATES A CLASS FOR EACH TABLE
from numpy import unpackbits
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, PrimaryKeyConstraint, String, Text, column, create_engine, Table, and_, join,MetaData,Float
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship, sessionmaker, Session, foreign, mapper,relationship, aliased
from sqlalchemy.sql import func


Base = declarative_base()
engine = create_engine('sqlite:///labjack.db',echo = False)
Session = sessionmaker(bind=engine)
session = Session()


class Inputs(Base):
    __tablename__ = "inputs"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique = True)
    units = Column(String(255))
    port = Column(String(255),unique = True)
    calibrationm = Column(Float)
    calibrationb = Column(Float)

class Config(Base):
    __tablename__ = "config"
    title = Column(String, primary_key = True)
    labjackmodel = Column(String)
    scanspersecond = Column(Float)

class Ports(Base):
    __tablename__ = "ports"
    id = Column(Integer,primary_key=True,autoincrement= "auto")
    name = Column(String, primary_key = True)
    port = Column(String)
    units = Column(String)
    m = Column(Float)
    b = Column(Float)
    
class Points(Base):
    __tablename__ = "points"
    id = Column(Integer, primary_key=True,autoincrement= "auto")
    time_stamp= Column(Float)
    input_id = Column(Integer, ForeignKey("inputs.id"))
    input = relationship("Inputs")
    value = Column(Float)

    
class Allports(Base):
    __tablename__ = "allports"
    id = Column(Integer)
    name = Column(String, primary_key = True)
    port = Column(String)
    units = Column(String)
    m = Column(Float)
    b = Column(Float)




# inputs = session.query(Points).filter(Points.input.name=="LengthMeasurer").all()