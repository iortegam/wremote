##! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        SerialParser.py
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

    def __init__(self, port='/dev/ttyS0', rate=9600, timeout=0, TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=4024,Dir_baseData=' /home/tabftir/daily/',sleepTime=5, aveTime=30):

        self.port        = port
        self.rate        = rate
        self.timeout     = timeout
        self.TCPserverIP = TCP_IP_in
        self.baseDataDir = Dir_baseData
        if not ( Dir_baseData.endswith('\\') ): self.baseDataDir = Dir_baseData + '\\'
        
        self.sleepTime   = sleepTime
        self.aveTime     = aveTime
        self.Met         = {}

        self.ntimes      = int(np.divide(float(self.aveTime), float(self.sleepTime)) )

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

        import serial.tools.list_ports

        ports = serial.tools.list_ports.comports()

        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))

            #if str(port) == str(self.port):


        print('\n')
        print('Using port: {}\n'.format(self.port))

        #------------------------
        # Check Serial port
        #------------------------
        try:
            self.ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
            self.ser.close()
            #print("ck port opened on " + self.ser.name)
            return True
        except IOError as e:
            print(e)
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

            print("Sen port opened on " + ser.name)

        except IOError as e:
            print("%s %s - Work-around attempt" % (self.port, e))
            return False


        if ser.isOpen():

            ser.write(inp + '\r')


            out = ''
            # let's wait second before reading output (let's give device time to answer)
            time.sleep(2)

            #ser.write('SET77' + '\r\n')
            #time.sleep(1)
            while ser.inWaiting() > 0:
                ser.flush()
                #ser.write(inp + '\r\n')
                #out += ser.readline()
                out += ser.read(1)

            if out != '':
                print (">>" + out)

            ser.close()

    def printLog(self):

        #--------------------------
        # Get current date and time
        #--------------------------
        crntTime = dt.datetime.now(dt.timezone.utc)

        datestr, timestr = self.getDTstr(crntTime)

        self.crntDataDir = self.baseDataDir + datestr + "/"

        ckDirMk(self.crntDataDir)

        #-----------------------------------------
        # Check if Measurement summary file exists
        #-----------------------------------------
        fname = self.crntDataDir+"houseMet.log"

        try:
            if not ckFile(fname):
                with open(fname,'w') as fopen:
                    fopen.write("{0:<10s} {1:>10s} {2:>14s} {3:>14s} {4:>14s} {5:>14s} {6:>14s} {7:>14s}\n".format("Date","Time","Atm_Temperature","Atm_Rel_Humidity","Atm_Pressure","Atm_Wind_Speed",  "Atm_Wind_Gust", "Atm_Wind_Dir"))
                    fopen.write("{0:<10s} {1:>10s} {2:>14s} {3:>14s} {4:>14s} {5:>14s} {6:>14s} {7:>14s}\n".format(datestr,timestr, str(round(np.mean(np.asarray(self.Met['ATM_TEMPERATURE'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_REL_HUMIDITY'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_PRESSURE'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_WIND_SPEED'])),3 )), str(round(np.max(np.asarray(self.Met['ATM_WIND_SPEED'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_WIND_DIR_E_OF_N'])),3 ))   ) )

            else:
                with open(fname,'a') as fopen:
                    fopen.write("{0:<10s} {1:>10s} {2:>14s} {3:>14s} {4:>14s} {5:>14s} {6:>14s} {7:>14s}\n".format(datestr,timestr, str(round(np.mean(np.asarray(self.Met['ATM_TEMPERATURE'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_REL_HUMIDITY'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_PRESSURE'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_WIND_SPEED'])),3 )), str(round(np.max(np.asarray(self.Met['ATM_WIND_SPEED'])),3 )), str(round(np.mean(np.asarray(self.Met['ATM_WIND_DIR_E_OF_N'])),3 ))   ) )
        except: pass

    def sendData(self):
        #------------------sendData--------
        # Write data to data server
        #--------------------------
        #print self.met
        if not self.Met:
            print ("No data to send to TCP from Weather Transmitter...\n")
            return False

        print ("Obtained Weather Transmitter data at......{}\n".format(dt.datetime.now(dt.timezone.utc)))

        for key in self.Met:
            
            try:
                val     = str(round(  np.mean(np.asarray(self.Met[key])), 3))
                message = key + " " + val
                self.setParam(message)
                #print ("{0:<20s} = {1:<14s}".format(key,  self.Met[key]))
                print ("{0:<20s} = {1:<14s}".format(key,  val))
            except:
                message = key + " " + self.Met[key]
                self.setParam(message)
                print ("{0:<20s} = {1:<14s}".format(key,  self.Met[key]))

        try:
            val     = str(round( np.max(np.asarray(self.Met['ATM_WIND_SPEED'])), 3))
            message = "ATM_WIND_GUST" + " " + val
            self.setParam(message)
            print ("{0:<20s} = {1:<14s}".format("ATM_WIND_GUST",  val))
        except:
            pass

        print ('\n')


    #------------------------
    # Connect serial port and read data
    #------------------------
    def getMet(self):

        print ('Reading Serial Port -> Creating Array & wait for {} seconds'.format(self.sleepTime))

        if not self.checkSerial(): 
            
            self.Met['ATM_STATUS'] = 'NOT_OK'
            
        #ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
        #print ser.is_open()
        try:
    	    ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
            #ser = serial.Serial(self.port, 9600, timeout=5, xonxoff=True, rtscts=True)
    	    print("get port opened on " + ser.name)
        except IOError as e:
            print("%s %s - Work-around attempt" % (self.port, e))
            exit()
            return False


        print(ser)
        time.sleep(int(self.sleepTime))
        #time.sleep(10)

        # print(ser.read())
        # print(ser.readline().decode('utf-8') )
        # print(ser.readline() )
        # exit()

        self.Met   = {}
        print('ntimes: ', self.ntimes)

        for i in range(self.ntimes):
            #-----------
            # Sleep time: important
            #-----------
            readingSer = ser.readline().decode('utf-8')
            #print(' readingSer string: ', readingSer)
            #print(' readingSer string: ', readingSer.strip())
            #print(' readingSer string: ', readingSer.strip().split())
            #print('readingSer: {}'.format(readingSer))

            #exit()
            #-----------
            # reading is a string...
            #-----------
            parts = readingSer.strip().split()
            print('parts: ', len(parts))

            if len(parts) >= 7:

                status           =  parts[6].split('*')[0]

                #print(parts)
                
                if status  == '00':

                    ws = float(parts[1])
                    wd = float(parts[2])
                    te = float(parts[3])
                    rh = float(parts[4])
                    pr = float(parts[5])

                    self.Met.setdefault('ATM_WIND_SPEED', []).append(ws)
                    self.Met.setdefault('ATM_WIND_DIR_E_OF_N', []).append(wd)
                    self.Met.setdefault('ATM_TEMPERATURE', []).append(te)
                    self.Met.setdefault('ATM_REL_HUMIDITY', []).append(rh)
                    self.Met.setdefault('ATM_PRESSURE', []).append(pr)


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

                    self.Met['ATM_STATUS']           = 'NOT_OK'

            elif len(parts) < 7:
                self.Met['ATM_STATUS']           = 'NOT_OK'

            time.sleep(int(self.sleepTime))

        if 'ATM_WIND_SPEED' in self.Met:
            self.Met['ATM_STATUS']           = 'OK'

        self.sendData()
        if self.Met['ATM_STATUS'] == 'OK': self.printLog()

        #-----------
        # Close serial port
        #-----------
        ser.close()

    #------------------------
    # Connect serial port and read data
    #------------------------
    def updMet(self):

        #print 'Reading Serial Port'
        if not self.checkSerial(): return False
        #ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
        #print ser.is_open()
        try:
    	    ser = serial.Serial(self.port, self.rate, timeout=self.timeout)
    	    #print("upd port opened on " + ser.name)
        except IOError as e:
            print("%s %s - Work-around attempt" % (self.port, e))
            return False

        time.sleep(int(self.sleepTime))

        if 'ATM_WIND_SPEED' in self.Met:

            for i, x in enumerate(self.Met['ATM_WIND_SPEED']):
            #for i in range(self.ntimes):
                #print( 'upD, i, x : ', i, x )

                #-----------
                # Sleep time: important
                #-----------
                readingSer = ser.readline().decode('utf-8')

                #-----------
                # reading is a string...
                #-----------
                parts = readingSer.strip().split()
                #print('len: ' , len(parts))
                #print(parts)

                if len(parts) >= 7:

                    status           =  parts[6].split('*')[0]

                    if status  == '00':

                        ws = float(parts[1])
                        wd = float(parts[2])
                        te = float(parts[3])
                        rh = float(parts[4])
                        pr = float(parts[5])

                        self.Met['ATM_WIND_SPEED'][i]        = ws
                        self.Met['ATM_WIND_DIR_E_OF_N'][i]   = wd
                        self.Met['ATM_TEMPERATURE'][i]       = te
                        self.Met['ATM_REL_HUMIDITY'][i]      = rh
                        self.Met['ATM_PRESSURE'][i]          = pr

                        #self.sendData()
                        #self.printLog()

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

                        self.Met['ATM_STATUS']           = 'NOT_OK'

                elif len(parts) < 7:
                    self.Met['ATM_STATUS']           = 'NOT_OK'

                time.sleep(int(self.sleepTime))
        else:
            self.Met['ATM_STATUS']           = 'NOT_OK'
            #self.sendData()

        self.sendData()
        if self.Met['ATM_STATUS'] == 'OK': self.printLog()

        #-----------
        # Close serial port
        #-----------
        ser.close()




if __name__ == "__main__":


	#--------------------------------
	# Retrieve command line arguments
	#--------------------------------
    #try:
    #    ctlFile  = sys.argv[1]
    #except:
    #    ctlFile  = "C:/bin/ops/FL0_Defaults.input"

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    # Edit here only
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    # #----------------------------
    # # Check existance of ctl file
    # #----------------------------
    ckFile(ctlFile,exitFlg=True)

    # #-------------------------
    # # Import ctlFile variables
    # #-------------------------
    ctlFvars = mainInputParse(ctlFile)

    print("\nLocal input parameters:")
    for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']


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
    MetData = MetClass(port=ctlFvars["Atm_Port"], rate=ctlFvars["Atm_Rate"], timeout=0,
                     TCP_IP_in=ctlFvars["FTS_DataServ_IP"], TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),
                    BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]),Dir_baseData=ctlFvars["Dir_WinData"],
                    sleepTime=ctlFvars["Atm_UpdateInt"], aveTime=ctlFvars["Atm_updateave"])

    MetData.getMet()

    #exit()

    #-----------------------------
    # Try to send commands for configuration (to be tested)
    #-----------------------------
    #MetData.SendSerial()
    #exit()

    while True:

        if MetData.Met['ATM_STATUS'] == 'OK':
            MetData.updMet()
        else:
            MetData.getMet()


        #try:
        #    MetData.updMet()
        #except:
        #    print "Unable to obtained Weather Transmitter Data!\n"
        #    MetData.getMet()

        #try:
        #MetData.sendData()
        #except:
        #    print("Unable to send data from web parser program to TCP data server!\n")

        #try:
        #    MetData.printLog()
        #except:
        #    print "Unable to save house Met data!\n"

