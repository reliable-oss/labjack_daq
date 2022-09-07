#CREATES DB TABLES IF THEY DONT EXSIST
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String, Text, create_engine, Float, Table
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

def recreate_db():
    Base = declarative_base()
    meta = MetaData()

    engine = create_engine('sqlite:///labjack.db',echo = True)

    conn = engine.connect()


    if (sqlalchemy.inspect(engine).has_table('inputs') == False):   
        conn.execute("CREATE TABLE inputs(id INTEGER PRIMARY KEY, name STRING, units STRING, port STRING, calibrationm FLOAT, calibrationb FLOAT);")
    if (sqlalchemy.inspect(engine).has_table('points') == False):       
        conn.execute("CREATE TABLE points(id INTEGER PRIMARY KEY AUTOINCREMENT,  time_stamp FLOAT, input_id FLOAT, value FLOAT, FOREIGN KEY (input_id) REFERENCES inputs(id));")
       
    if (sqlalchemy.inspect(engine).has_table('config') == False):  
        conn.execute("CREATE TABLE config(title STRING PRIMARY KEY, labjackmodel STRING, scanspersecond FLOAT);")
    if (sqlalchemy.inspect(engine).has_table('ports') == False):  
        conn.execute("CREATE TABLE ports(id INTEGER PRIMARY KEY AUTOINCREMENT, name STRING, port STRING, units STRING, m FLOAT, b FLOAT);")
    

if __name__ == '__main__':
    recreate_db()