#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        readMet.py
#
# Purpose:
#       - Program to read Wether Transmitter data at MLO
#       - Send data to TCP
#
# Notes:
#       Sensor: Young ResponseONE 92000
#       Link:   http://www.youngusa.com/products/16/85.html
#
#       Use of serial port:  https://buildmedia.readthedocs.org/media/pdf/pyserial/latest/pyserial.pdf
#       
#       Factory Default Configuration (RS-232-ASCII): 
#                                                    - Temp            [C]
#                                                    - RH              [%]
#                                                    - Pressure        [hPa]
#                                                    - Wind Speed      [m/s]
#                                                    - Wind Direction  [Degrees azimuth]
#--------------------------------
#       FOR LINUX TRY >> $ dmesg | grep tty
#       ALTERNATIVELY: setserial -g /dev/ttyS[0123]
#        FOR LINUX: /dev/ttyS0
#--------------------------------
# Created:
#       Ivan Ortega April 2019
#----------------------------------------------------------------------------------------

import serial
import time
from remoteData       import FTIRdataClient
import os
import sys
import socket
import select
import smtplib
import datetime       as     dt
from email.mime.text  import MIMEText
from trackerUtils     import *


class MetClass(FTIRdataClient):

    def __init__(self, port='COM1', rate=9600, timeout=0, TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=4024,Dir_baseData=' X:\id\fl0'):

        self.port        = port
        self.rate        = rate
        self.timeout     = timeout   
        self.TCPserverIP = TCP_IP_in
        self.baseDataDir = Dir_baseData
        self.Met         = {}
        
        FTIRdataClient.__init__(self,TCP_IP=TCP_IP_in,TCP_Port=TCP_Port_in,BufferSize=BufferSize_in)

    def getDTstr(self,crntTime):

        #--------------------------
        # Get current date and time
        #--------------------------
        
        yrstr    = "{0:04d}".format(crntTime.year)
        mnthstr  = "{0:02d}".format(crntTime.month)
        daystr   = "{0:02d}".format(crntTime.day)  
        hourstr  =  "{0:02d}".format(crntTime.hour) 
        minstr   =  "{0:02d}".format(crntTime.minute) 
        secstr   =  "{0:02d}".format(crntTime.second) 

        datestr  = yrstr + mnthstr + daystr 
        timestr  = hourstr+':'+ minstr+':'+ secstr  

        return datestr, timestr
    

    def checkSerial(self):

        #------------------------
        # Check Serial port
        #------------------------
        try:
            self.ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
            self.ser.close()
            #print("port opened on " + ser.name)
            return True
        except IOError as e:
            print("%s %s - Work-around attempt" % (self.port, e))
            return False

    #------------------------
    # Attempt to send commands: April 2019 (Not Working in Windows 10)
    #------------------------
    def SendSerial(self):

        inp   = 'RPTV'
        
        #------------------------
        # Check if address exists
        #------------------------
        try:
            ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
            
            print("port opened on " + ser.name)
            
        except IOError as e:
            print("%s %s - Work-around attempt" % (self.port, e))
            return False
        

        if ser.isOpen():

            ser.write(inp + '\r')


            out = ''
            # let's wait one second before reading output (let's give device time to answer)
            time.sleep(2)

            #ser.write('SET77' + '\r\n')
            #time.sleep(1)
            while ser.inWaiting() > 0:
                ser.flush()
                #ser.write(inp + '\r\n')
                #out += ser.readline()
                out += ser.read(1)

            if out != '':
                print(">>" + out)

            ser.close()

    def printLog(self):

        #--------------------------
        # Get current date and time
        #--------------------------
        crntTime = dt.datetime.utcnow()       

        datestr, timestr = self.getDTstr(crntTime)         
        
        self.crntDataDir = self.baseDataDir + datestr + "/" 

        ckDirMk(self.crntDataDir)

        #-----------------------------------------
        # Check if Measurement summary file exists
        #-----------------------------------------
        fname = self.crntDataDir+"houseMet.log"
       
        if not ckFile(fname):
            with open(fname,'w') as fopen:
                fopen.write("{0:<12s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s} {6:>12s}\n".format("Date","Time","Temperature","Rel_Humidity","Pressure","Wind_Speed","Wind_Dir"))
                fopen.write("{0:<12s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s} {6:>12s}\n".format(datestr,timestr, self.Met['ATM2_TEMPERATURE'], self.Met['ATM2_REL_HUMIDITY'], self.Met['ATM2_PRESSURE'], self.Met['ATM2_WIND_SPEED'], self.Met['ATM2_WIND_DIR_E_OF_N']  ) )
        
        else:
            with open(fname,'a') as fopen:
                fopen.write("{0:<12s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s} {6:>12s}\n".format(datestr,timestr, self.Met['ATM2_TEMPERATURE'], self.Met['ATM2_REL_HUMIDITY'], self.Met['ATM2_PRESSURE'], self.Met['ATM2_WIND_SPEED'], self.Met['ATM2_WIND_DIR_E_OF_N']  ) )



    #------------------------
    # Connect serial port and read data
    #------------------------
    def getMet(self, sleepTime= 2):

        if not self.checkSerial(): return False
        #ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
        #print ser.is_open()
        try:
    	    ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
    	    #print("port opened on " + ser.name)
        except IOError as e:
    	    print("%s %s - Work-around attempt" % (self.port, e))
    	    return False

    	#-----------
    	# Sleep time: important
    	#-----------
        time.sleep(int(sleepTime))

        Metreading = ser.readline()#.decode('utf-8')
        print(Metreading)
        
        #-----------
        # Close serial port
        #-----------
        ser.close()
        
        #-----------
        # reading is a string...
        #-----------
        parts = Metreading.strip().split()
        print(parts)

        exit()
        
        if len(parts) >= 7:

            status           =  parts[6].split('*')[0]

            if status  == '00':

                self.Met['ATM2_WIND_SPEED']            = parts[1]
                self.Met['ATM2_WIND_DIR_E_OF_N']       = parts[2]
                self.Met['ATM2_TEMPERATURE']           = parts[3]
                self.Met['ATM2_REL_HUMIDITY']          = parts[4]
                self.Met['ATM2_PRESSURE']              = parts[5]
                self.Met['ATM2_STATUS']                = 'OK'

            else:
                if status == '01':
                    print ('Transducer path A blocked or dirty!')
                elif status == '02':
                    print ('Transducer path B blocked or dirty!')
                elif status == '04':
                    print ('Transducer path C blocked or dirty!')
                elif status == '08':
                    print ('Temperature/RH error!!')
                else:
                    print ('Refer to manual: status {}'.format(status))

                self.Met['ATM2_STATUS']           = 'NOT_OK'

        elif len(parts) < 7:
            self.Met['ATM2_STATUS']           = 'NOT_OK'
            
  
    def sendData(self):
        #--------------------------
        # Write data to data server
        #--------------------------
        if not self.Met:
            print ("No data to send to TCP from Weather Transmitter...\n")
            return False

        print ("Successfully obtained Weather Transmitter data at......{}\n".format(dt.datetime.utcnow()))

        for key in self.Met:
            message = key + " " + self.Met[key]
            self.setParam(message)
            #print key + " = " + self.Met[key]
            print ("{0:<20s} = {1:<12s}".format(key,  self.Met[key]))

        print('\n')


if __name__ == "__main__":


	#--------------------------------
	# Retrieve command line arguments
	#--------------------------------
    try:
        ctlFile  = sys.argv[1]
    except:
	#   ctlFile  = "/home/mloftir/remote/ops/MLO_Defaults.input"
        ctlFile  = "C:/bin/ops/FL0_Defaults.input"


	#----------------------------
	# Check existance of ctl file
	#----------------------------
    ckFile(ctlFile,exitFlg=True)

	#-------------------------
	# Import ctlFile variables
	#-------------------------
    ctlFvars = mainInputParse(ctlFile)

	#-----------------------------
	# Initialize Met Object
	#-----------------------------
    MetData = MetClass(port=ctlFvars["Met_Port"], rate=ctlFvars["Met_Rate"], timeout=0, 
		                 TCP_IP_in=ctlFvars["FTS_DataServ_IP"], TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]), 
		                BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]),Dir_baseData=ctlFvars["Dir_baseData"])

    MetData.getMet(sleepTime=ctlFvars["Met_UpdateInt"])

    #MetData.SendSerial()
    #exit()

    while True: 
        
        try:
            MetData.getMet(sleepTime=ctlFvars["Met_UpdateInt"])
        except:
            print ("Unable to obtained Weather Transmitter Data!\n")

        # try:
        #     MetData.sendData()
        # except:
        #     print "Unable to send data from web parser program to TCP data server!\n"

        # try:
        #     MetData.printLog()
        # except:
        #     print "Unable to save house Met data!\n"
    
