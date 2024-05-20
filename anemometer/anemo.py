#!/usr/bin/python

#-*- encoding:utf-8 -*-
import tornado.web
import tornado.ioloop
from tornado.ioloop import IOLoop, PeriodicCallback
import tornado.process
import tornado.template
import tornado.httpserver
import json
import sys
import serial.tools.list_ports as ls
import os,time
import serial
import textwrap
i=0
def encrypt(string, length):
    a=textwrap.wrap(string,length)
    return a


from configparser import ConfigParser
os.chdir(os.path.dirname(os.path.realpath(__file__)))
configfile_name = "config.ini"
if not os.path.isfile(configfile_name):
    # Create the configuration file as it doesn't exist yet
    cfgfile = open(configfile_name, 'w')
    # Add content to the file
    Config = ConfigParser()
    Config.add_section('api')
    Config.set('api', 'port', '3019')
    Config.add_section('anemo')
    Config.set('anemo', 'sr_port', '/dev/ttyUSB0')
    Config.set('anemo', 'baudrate', '9600')
    Config.set('anemo', 'timeout', '1')
    Config.add_section('data')
    Config.set('data', 'start', '01 03 00 00 00 0f 05 ce') # start

    Config.write(cfgfile)
    cfgfile.close()
configReader = ConfigParser()
configReader.read('config.ini')
sr_port = configReader['anemo']['sr_port']
baudrate = configReader['anemo'].getint('baudrate')
sr_timeout = configReader['anemo']['timeout']
api_port = configReader['api'].getint('port')
s_data = configReader['data']['start']
print(sr_port,baudrate)
class Anemo(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
class SensorData(tornado.web.RequestHandler):
    def get(self):
        os.system('python -m serial.tools.list_ports -v')
        sr=serial.Serial()
        sr.port=str(sr_port)
        sr.baudrate=baudrate
        sr.timeout=1
        sr.stopbits=1
        sr.bytesize=8
        sr.open()
        data = configReader['data']['start']
        print(data)
        if sr.is_open:
            print("port is open")
            data=sr.write(bytes.fromhex(data))
            resp = sr.readline()
            # resp = b'\x01\x03\x1E\x00\x30\x00\xB0\x00\xFA\x02\x8A\x27\xAC\x00\x22\x00\x32\x00\x01\x44\x5B\xFF\xAE\x07\xE4\x01\x5E\x00\x32\x00\x42\x0B\xB8\xBE'
            resp = resp.hex()
            resp = encrypt(resp,2)
            wspeed1 = resp[3]
            wspeed2 = resp[4]
            wdir1 = resp[5]
            wdir2 = resp[6]
            temp1 = resp[7]
            temp2 = resp[8]
            humid1 = resp[9]
            humid2 = resp[10]
            airpres1 =resp[11]
            airpres2=resp[12]
           
            wind_speed = wspeed1+wspeed2
            wind_speed = round((int(wind_speed,16) * 0.01)*18/5,2)
            # print("wind speed ",str(wind_speed)+' km/hr')
            wind_dirc = wdir1+wdir2
            wind_dirc = int(wind_dirc,16)
            temp = temp1+temp2
            temp = round(int(temp,16)*0.1,2)
            humid = humid1+humid2
            humid = round(int(humid,16)*0.1,2)
            airpressure = airpres1+airpres2
            airpressure = round(int(airpressure,16)*0.1,2)
           
            sr.close()
            data = {'WindSpeed':str(wind_speed)+' km/h','WindDirection': str(wind_dirc),'Temperature': str(temp)+'°C','Humidity': str(humid)+' %','Pressure': str(airpressure)+' hbar'}
            self.write(json.dumps(data))
            # self.write({'WindSpeed': str(wind_speed)+' km/h','WindDirection ': str(wind_dirc)+' degree','Temperature ': str(temp)+' deg C'})
        else:
            print("port is not open")
            return 0
        
def make_app():
    return tornado.web.Application([("/", Anemo),("/sdata", SensorData)],template_path=os.path.join(os.path.dirname(__file__), "templates"))

if __name__ == '__main__':
    app = make_app()
    app.listen(api_port)
    print("Lrf is listening for commands on port: "+str(api_port))
    IOLoop.instance().start()
