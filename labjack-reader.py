import time
import threading
from labjack import ljm
from audioop import cross
from flask_cors import cross_origin
from flask import Flask, render_template, jsonify,request,redirect, send_file
import time as tm
from sqlalchemy import create_engine,update,and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from jinja2 import Environment, FileSystemLoader
from database_schema import Inputs, Config, Ports, Points
from create_database import recreate_db
from labjack import ljm
from datetime import datetime

recreate_db() #CREATES DB TABLES IF THEY DONT EXSIST

engine = create_engine('sqlite:///labjack.db?check_same_thread=False', echo = False)
Base = declarative_base()
conn = engine.connect()
file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
Session = sessionmaker(bind=engine)
session = Session()


#IF CONFIG IS EMPTY, ADD DEFAULT VALUES TO MAKE LABJACK OBJECT AND START THREADS 
if len(session.query(Config).all())==0:
    p = Config(
        title = "labjackdata",
        labjackmodel = "T4",
        scanspersecond = 2

        )
    session.add(p)
    session.commit()


class Labjack:
    def __init__(self):  
        self.model = session.query(Config.labjackmodel).first()[0]
        
        allports = []
        self.datavalues = {}
        self.timevalues = {}
        ports = session.query(Inputs).all()
        for port in ports:
            self.datavalues[f'{port.id}'] = []
            self.timevalues[f'{port.id}'] = []
            newport = {
                'name': port.name,
                'id': port.id,
                'units':port.units,
                'port':port.port,
                'm':port.calibrationm,
                'b':port.calibrationb    }
            allports.append(newport)
        self.ports = allports
        self.scansper = float(session.query(Config.scanspersecond).first()[0])
        self.getdata = False
        

        self.port_configuration = {}
    
    def reconfig(self,model,scansper,ports):
        self.model = model
        self.scansper = scansper
        self.ports = ports
        self.handle = ljm.openS(f"{self.model}", "ANY", "ANY")
    
    def collectdata(self):
        while True:
            if self.getdata:
                for port in self.ports:
                    name = port['port']
                    try:
                        result = ljm.eReadName(self.handle, name)
                        calibrated = float(port['m'])*result + float(port['b'])
                        p = Points(
                            time_stamp = time.time(),
                            input_id = port['id'],
                            value = (calibrated)
                        )
                        session.add(p)
                        session.commit()
                    except Exception as e:
                        # collection failed, do I need to re-connect?
                        self.handle = ljm.openS(f"{self.model}", "ANY", "ANY")  
            time.sleep(1/int(self.scansper))
       

    def endcollection(self):
        self.getdata = False
        return("success")
    def startcollection(self):
        self.getdata = True
        return("success")
    def viewcurrentconfig(self):
        ports = []
        for port in self.ports:
            portinfo = {
                'name': port['name'],
                'port':port['port'],
                'units':port['units'],
                'm':port['m'],
                'b':port['b']
            }
            ports.append(portinfo)
        configsettings = {
            'model': self.model,
            'scanspersecond':self.scansper,
            'ports':ports
        }
        
        return jsonify(configsettings)
        

    def portbyid(self,portid):
        pastports = session.query(Ports).all()
        for port in pastports:
            if port.id==portid:
                portinfo = {
                'id': port.id,
                'name': port.name,
                'port':port.port,
                'units':port.units,
                'm':port.m,
                'b':port.b
                }
        return (portinfo)


app = Flask(__name__)
def startWebServer():
    app.run()

global lj 
lj = Labjack()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

#RENDERS HTML TEMPLATES
@app.route('/', methods=['GET'])
@cross_origin()
def homepage():
    return redirect("/graph")

@app.route('/graph', methods=['GET'])
@cross_origin()
def graph():
    return render_template("graph.html")

@app.route('/config', methods=['GET'])
@cross_origin()
def config():
    return render_template("config.html")

@app.route('/viewconfig',methods=['GET'])
@cross_origin()
def viewconfig():
    return render_template("viewconfig.html")

@app.route('/exportdata',methods=['GET'])
@cross_origin()
def exportdatapage():
    return render_template("export.html")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/getdata', methods=['GET']) #GETS DATA FROM DATABASES (ALL DATA AND DATA ONLY AFTER START DATA COLLECTION), RETURNS JSON
def getdata():
    returnjson = {}
    startseconds = float(request.args.get('currenttime'))
    allinputs = session.query(Inputs.name).all()
    timesdict = {}
    inputsdict = {}
    inputsunits = {}
    returnjson = {}
    allinputs = session.query(Inputs.name).all()
    allinputsunits = session.query(Inputs.units).all()
    for input,unit in zip(allinputs,allinputsunits):
        inputsunits[f"{input[0]}"] = unit[0]
    for input in allinputs: 
        inputname = input[0]
        inputid = session.query(Inputs.id).filter(Inputs.name==f"{inputname}")[0][0]
        points = session.query(Points.time_stamp,Points.value).filter(and_(Points.time_stamp>startseconds,Points.input_id==inputid)).all()
        times = []
        values = []
        for p in points:
            times.append(p[0])
            values.append(p[1])
        timesdict[f'{inputname}'] = times
        inputsdict[f'{inputname}'] = values
    returnjson['times'] = timesdict
    returnjson['inputs'] = inputsdict
    # ALL TIMES AND VALUES
    timesdict = {}
    inputsdict = {}
    for input in allinputs:
        inputname = input[0]
        inputids = conn.execute(f'SELECT id FROM inputs WHERE (inputs.name = "{inputname}");')
        for i in inputids:
            inputid = (i[0])
        query = f'SELECT time_stamp, value FROM points WHERE input_id={inputid};'
        points = session.execute(query)
        times = []
        values = []
        for p in points:
            times.append(p[0])
            values.append(p[1])
        timesdict[f'{inputname}'] = times
        inputsdict[f'{inputname}'] = values
        units = session.query(Inputs.units).filter(Inputs.name==inputname)
        for unit in units:
            inputsunits[f'{inputname}'] = unit[0]
    returnjson['units'] = inputsunits
    returnjson['fulltimes'] = timesdict
    returnjson['inputsfull'] = inputsdict
    return jsonify(returnjson)


@app.route('/startcollection', methods=['GET']) # STARTS DATA COLLECTION
@cross_origin()
def startcollection():
    lj.startcollection()
    return ("success",200)
    

@app.route('/section',methods=['GET']) #GETS ALL POINTS OF INPUTS FROM GIVEN TIME SECTION (ALL IF NO TIME CONSTRAINTS)
@cross_origin()
def getsection():
    timestart = float(request.args.get('timestart'))
    if not(request.args.get('timeend') == "NaN"):
        timeend = float(request.args.get('timeend'))
    else:
        timeend = float(tm.time())
    returnjson = {}
    allinputs = session.query(Inputs.name).all()
    timesdict = {}
    inputsdict = {}
    inputsunits = {}
    for input in allinputs:
        inputname = input[0]
        inputids = conn.execute(f'SELECT id FROM inputs WHERE (inputs.name = "{inputname}");')
        for i in inputids:
            inputid = (i[0])
        query = f'SELECT time_stamp, value FROM points WHERE time_stamp<{timeend} AND time_stamp > {timestart} AND input_id={inputid};'
        points = session.execute(query)
        times = []
        values = []
        for p in points:

            times.append(p[0])
            values.append(p[1])
        timesdict[f'{inputname}'] = times
        inputsdict[f'{inputname}'] = values
        units = session.query(Inputs.units).filter(Inputs.name==inputname)
        for unit in units:
            inputsunits[f'{inputname}'] = unit[0]
    returnjson['units'] = inputsunits
    returnjson['times'] = timesdict
    returnjson['inputs'] = inputsdict
    if (len(times) == 0):
        return("Error", 416)
    else:
        return jsonify(returnjson)



@app.route('/endcollection',methods=['GET']) #STOPS DATA COLLECTION
@cross_origin()
def endcollection():
    lj.endcollection()
    return("Success")


@app.route('/configsettings',methods=['POST']) #CHANGES CONFIG SETTINGS OF LABJACK OBJECT AND DATABASE, EDITS IF ALREADY EXISTS
@cross_origin()
def configsettings():
    data = request.get_json()
    # Creates ports list, adds inputs to db, adds columns to points table 
    for portname in data['ports']:
        try:
            handle = ljm.openS(f"{data['labjack-model']}","ANY","ANY")
            ljm.eReadName(handle, f'{portname["port"]}')
            ljm.close(handle)
        except:
            errordict = {'port': portname["port"]}
            return(jsonify(errordict), 404)
    model = data['labjack-model']
    persec = data['scans-per-second']
    session.query(Config).delete()
    configinfo = Config(
        title = "Labjack Inputs",
        labjackmodel = model,
        scanspersecond = persec
    )
    session.add(configinfo)
    session.commit()
    session.query(Inputs).delete()
    allportsinfo = []
    for p in data['ports']:
        portname = p['name']
        portport = p['port']
        portunits = p['units']
        portm = p['m']
        portb = p['b']
        newport = Ports(
            name = portname,
            port = portport,
            units = portunits,
            m = portm,
            b = portb
        )
        if (session.query(Ports.name).filter_by(name=portname).first() ==None): #IF PORT DOESN'T EXIST, ADD
            session.add(newport)
            session.commit()
    
        if(session.query(Ports.name).filter_by(name=f"{p['name']}").first() !=None): #UPDATES PORT INFO IF NAMES ARE THE SAME
            session.execute(update(Ports).where(Ports.name ==portname).values(units = portunits,port =
            portport,m = portm,b = portb))
            session.commit()
        
        allinputids = session.execute(f"SELECT id FROM ports WHERE name='{portname}'") 
        for i in allinputids:
            inputid = i[0]
        newinput = Inputs(
            id = inputid,
            name = p['name'],
            units = p['units'],
            port = p['port'],
            calibrationm = p['m'],
            calibrationb = p['b']
        )
        session.add(newinput)
        session.commit()
        newportinfo = {
                'name': newinput.name,
                'id': newinput.id,
                'units':newinput.units,
                'port':newinput.port,
                'm':newinput.calibrationm,
                'b':newinput.calibrationb    }
        allportsinfo.append(newportinfo)
    lj.reconfig(data['labjack-model'],data['scans-per-second'],allportsinfo)
    return ("success",200)

@app.route('/getconfigsettings',methods=['GET']) #GETS ALL CONFIG DATA FROM LABJACK CLASS TO DISPLAY IN VIEW CONFIGURATIONS 
@cross_origin()
def getconfigsettings():
    return(lj.viewcurrentconfig())


@app.route('/pastports',methods=['GET']) #GETS ALL PAST PORT INFO TO SEE PAST PORT IDS AND DATA (FOR VIEW CONFIGS AND EXPORT DATA)
@cross_origin()
def pastports():
    pastportsjson = {}
    portslist = []
    ports = session.query(Ports).all()
    for p in ports:
        portsinfo = {
            'id': p.id,
            'name':p.name,
            'port':p.port,
            'units':p.units,
            'm':p.m,
            'b':p.b
        }
        portslist.append(portsinfo)
    pastportsjson["ports"] = portslist
    return jsonify(pastportsjson)


@app.route('/portbyid',methods=['GET']) #GETS PORT INFO BY ID TO AUTOFILL WHEN ADDING A PORT BY ID 
@cross_origin()
def portbyid():
    portid = int(request.args.get('portid'))
    return lj.portbyid(portid)
   
@app.route('/defaultvalues',methods = ['GET']) #GETS MODEL AND SCANS PER SECOND TO AUTOFILL IN CHANGE CONFIGURATIONS
@cross_origin()
def defaultvalues():
    values = session.query(Config.labjackmodel,Config.scanspersecond).all()
    for value in values:
        returnjson = {
            'model': value[0],
            'scanspersec': value[1]
        } 
    return jsonify(returnjson)
    
@app.route('/exportdataid',methods=['GET']) #CREATES CSV AND SENDS IT AS ATTATCHMENT
@cross_origin()
def exportdata():
    portid = int(request.args.get('portid'))
    filename = (request.args.get('filename'))
    starttime = (request.args.get('starttime'))
    endtime = (request.args.get('endtime'))
    if starttime=="NaN":
        starttime=0
    else:
        starttime = float(request.args.get('starttime'))
    if endtime =="NaN":
        endtime = 0
    else:
        endtime = float(request.args.get('endtime'))
    try: 
        portname = session.query(Ports.name).filter(Ports.id==portid)[0][0]
    except:
        return("error",400)
    
    if endtime==0:
        data = session.query(Points.time_stamp,Points.value).filter(and_(Points.input_id==portid,Points.time_stamp>starttime)).all()
    else:
        data = session.query(Points.time_stamp,Points.value).filter(and_(Points.input_id==portid,Points.time_stamp>starttime,Points.time_stamp<endtime)).all()
    f = open(f"{filename}.csv","w")
    f.write(f"timestamp(epoch),time(datetime),{portname} value\n")

    for points in data:
        normaltime =  datetime.fromtimestamp(points[0])

        f.write(f"{points[0]},{normaltime},{points[1]}\n")
    f.close()
    path = f"{filename}.csv"
    return send_file(path, as_attachment= True)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

#STARTS THREADS 
thread_1 = threading.Thread(target=lj.collectdata)
thread_2 = threading.Thread(target=startWebServer)

thread_1.start()
thread_2.start()


# - Exporting data adds .csv extention to given file name (no need to include .csv in the given file name)
# - Entering no start/end time results in all data (both export data and graph section)
# - different ports may have different configurations (ports like FIO5 may not work, to edit, changes lines 79 and 292)
# - the labjack changes the number of scans per second based on the inputed configuration, but the graph only updates every .5 seconds
#   - to change the update time of the graph, go to graph.html line 55 and change 1000 (1000 is one every second, increasing increases time between updates)
