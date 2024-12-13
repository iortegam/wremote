#!/usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        remoteData.py
#
# Purpose:
#       This is the data server for the remote FTIR instrument
#
#
#
# Notes:
#       1) 
#
#
# License:
#    Copyright (c) 2013-2014 NDACC/IRWG
#    This file is part of sfit4.
#
#    sfit4 is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    sfit4 is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with sfit4.  If not, see <http://www.gnu.org/licenses/>
#
#----------------------------------------------------------------------------------------

    #-------------------------#
    # Import Standard modules #
    #-------------------------#


import os
import sys
import socket
import select
import smtplib
import datetime       as     dt
from email.mime.text  import MIMEText
from trackerUtils     import *

 
    
class FTIRdataClient(object):
    
    def __init__(self,TCP_IP="127.0.0.1",TCP_Port=5555,BufferSize=4024):
    
        #-----------------------------------
        # Configuration parameters of server
        #-----------------------------------
        self.TCP_IP          = TCP_IP
        self.TCP_Port        = int(TCP_Port)
        self.RECV_BUFFER     = int(BufferSize) 

    def setParam(self,message):
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(("set "+message).encode())
        
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart.decode()
            
            sock.close()    
        except:
            print ("Unable to connect to data server!!")       
            incommingTotal = False   
            
        return incommingTotal
    
    def getParam(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(("get "+message).encode())
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart.decode()
            
            sock.close()    
        except:
            print ("Unable to connect to data server!!")          
            incommingTotal = False    
            
        return incommingTotal

    def getParamN(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(("getN "+message).encode())
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart.decode()
            
            sock.close()    
        except:
            print ("Unable to connect to data server!!")          
            incommingTotal = False         

        return incommingTotal

    def writeTCP(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(message.encode())
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart.decode()
            
            sock.close()    
        except:
            print ("Unable to connect to data server!!")           
            incommingTotal = False          
            
        return incommingTotal

    def writeSpectra(self,message):

        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(("WRITE_OPUS "+message).encode())
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart.decode()
            
            sock.close()    
        except:
            print ("Unable to connect to data server!!")           
            incommingTotal = False   
            
        return incommingTotal
                

class FTIRdataServer(object):
    
    def __init__(self,ctlFvars,inputFileName):

        #-----------------------------------
        # Configuration parameters of server
        #-----------------------------------        
        self.ctlFvars        = ctlFvars
        self.TCP_IP          = ctlFvars["FTS_DataServ_IP"]
        self.TCP_Port        = int(ctlFvars["FTS_DataServ_PORT"])
        self.RECV_BUFFER     = int(ctlFvars["FTS_DATASERV_BSIZE"])
        self.connection_list = []
        self.EWSaddress      = ctlFvars["Bruker_IP"]
        self.dataParams      = {}
        self.dataParamTS     = {}
        self.baseDataDir     = ctlFvars["Dir_baseData"]
        self.inputFname      = inputFileName
        #self.pollLst         = obsList["pollLst"].strip().split(",")
        #self.hdrLst          = obsList["hdrLst"].strip().split(",")
        
        
        
    def getTS(self,crntTime):
        
        return "{0:%Y%m%d.%H%M%S}".format(crntTime)
                   
    def runServer(self):
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.TCP_IP,self.TCP_Port))
        #self.server_socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
	
        self.server_socket.listen(10)         
        self.connection_list.append(self.server_socket)

        #-------------------------------------------------------------
        # Set initial parameters upon start up of database
        # TRACKERSTAT -> Initializing -- This says that the tracker is
        #    initializing and not ready for taking a measurement.
        #-------------------------------------------------------------
        crntTime = dt.datetime.now(dt.timezone.utc)
	       
        self.dataParams["TRACKER_STATUS"]       = self.ctlFvars["Tracker_status"].upper()
        self.dataParamTS["TRACKER_STATUS"]      = self.getTS(crntTime)
        self.dataParams["TRACKER_POWER"]       = self.ctlFvars["Tracker_power"].upper()
        self.dataParamTS["TRACKER_POWER"]      = self.getTS(crntTime)
        self.dataParams["OPUS_CMND"]            = self.ctlFvars["Opus_cmnd"].upper()
        self.dataParamTS["OPUS_CMND"]           = self.getTS(crntTime) 
        self.dataParams["OPUS_LASTSCAN"]        = self.ctlFvars["Opus_lastscan"]
        self.dataParamTS["OPUS_LASTSCAN"]       = self.getTS(crntTime)         
        self.dataParams["TRACKER_CMND"]         = self.ctlFvars["Tracker_cmnd"].upper()
        self.dataParamTS["TRACKER_CMND"]        = self.getTS(crntTime)
        self.dataParams["TRACKER_SUNPIX"]       = self.ctlFvars["Tracker_sunpix"]
        self.dataParamTS["TRACKER_SUNPIX"]      = self.getTS(crntTime)
        self.dataParams["TRACKER_AZIMUTH"]      = self.ctlFvars["Tracker_azimuth"]
        self.dataParamTS["TRACKER_AZIMUTH"]     = self.getTS(crntTime)
        self.dataParams["TRACKER_ELEVATION"]    = self.ctlFvars["Tracker_elevation"]
        self.dataParamTS["TRACKER_ELEVATION"]   = self.getTS(crntTime)        
        self.dataParams["TRACKER_SUNRAD"]       = self.ctlFvars["Tracker_sunrad"]
        self.dataParamTS["TRACKER_SUNRAD"]      = self.getTS(crntTime)
        self.dataParams["FILE_DEFAULTS"]        = [self.inputFname]          
        self.dataParamTS["FILE_DEFAULTS"]       = self.getTS(crntTime)
        
        #-------------------------------------
        # Start loop to listen for connections
        #-------------------------------------
        while True:

            #--------------------------
            # Get current date and time
            #--------------------------
            crntTime = dt.datetime.now(dt.timezone.utc)
            yrstr    = "{0:04d}".format(crntTime.year)
            mnthstr  = "{0:02d}".format(crntTime.month)
            daystr   = "{0:02d}".format(crntTime.day)  
            datestr  = yrstr + mnthstr + daystr                
            
            self.crntDataDir = self.baseDataDir + datestr + "\\"       
                            
            #--------------------
            # Get list of sockets
            #--------------------
            read_sockets,write_sockets,error_sockets = select.select(self.connection_list,[],[], 2)

            print ('\nReading socket on {} UT:'.format(dt.datetime.now(dt.timezone.utc)))
            
            for sock in read_sockets:
        
                #-----------------------
                # Handle new connections
                #-----------------------
                if sock == self.server_socket:
                    
                    #----------------------------------------------
                    # New connection recieved through server_socket
                    #----------------------------------------------
                    sockfd, addr = self.server_socket.accept()
                    
                    self.connection_list.append(sockfd)
                    print ("Client (%s, %s) connected" % addr)
        
                #-------------------------------------
                # Handle incomming request from client
                #-------------------------------------
                else:
                    
                    #------------------------
                    # Handle data from client
                    #------------------------
                    try:
                        data = sock.recv(self.RECV_BUFFER).decode()
                        
                        #------------------------------------------------
                        # Three types of call to server:
                        #  1) set   -- sets the value of a data parameter
                        #  2) get   -- gets the value of a data parameter
                        #  3) write -- write data to a file
                        #------------------------------------------------
                        splitVals = data.strip().split()
                        
                        if splitVals[0].upper() == 'GET':
                            
                            #-------------------------------------------------
                            # Send value of requested parameter back to client
                            #-------------------------------------------------
                            try:
                                msg = " ".join(self.dataParams[splitVals[1].upper()])
                                sock.sendall(msg.encode())
                            except:
                                sock.sendall("-999".encode())
                                
                        elif splitVals[0].upper() == 'GETTS':
                            
                            #-------------------------------------------------
                            # Send value of requested parameter back to client
                            #-------------------------------------------------
                            try:
                                msg = " ".join(self.dataParamTS[splitVals[1].upper()])
                                sock.sendall(msg.encode())
                            except:
                                sock.sendall("-999".encode())       

                        elif splitVals[0].upper() == 'GETET':

                            #-------------------------------------------------
                            # Send value of requested parameter back to client
                            #-------------------------------------------------
                            crntTime = dt.datetime.now(dt.timezone.utc)

                            try:

                                TS = dt.datetime(int(self.dataParamTS[splitVals[1]][0:4]), int(self.dataParamTS[splitVals[1]][4:6]), int(self.dataParamTS[splitVals[1]][6:8]), int(self.dataParamTS[splitVals[1]][9:11]),
                                    int(self.dataParamTS[splitVals[1]][11:13]), int(self.dataParamTS[splitVals[1]][13:15]), tzinfo=dt.timezone.utc)

                                ET = abs(crntTime - TS).seconds
                                ET = float("{:.2f}".format(ET/60.))  # Minutes

                                msg = " ".join(str(ET))
                                sock.sendall(msg)
                            except:
                                sock.sendall("-999")                 
                                
                                
                        elif splitVals[0].upper() == 'GETN':
                            
                            #-------------------------------------------------
                            # Send value of requested parameter back to client
                            #-------------------------------------------------                            
                            valsToGet  = splitVals[1:]
                            valsToSend = []
                            
                            for val in valsToGet:
                                try:                           
                                    strVal = " ".join(self.dataParams[val.upper()])
                                    valsToSend.append(strVal)
                                except:
                                    valsToSend.append("-999")
                                
                            msg = ",".join(valsToSend)
                            sock.sendall(msg.encode())                            
                            
                        elif splitVals[0].upper() == 'SET':
                            
                            #---------------------------------------------------
                            # Set value of parameter sent by client. Send back 1
                            # for success or 0 for failure
                            #---------------------------------------------------
                            self.dataParams[splitVals[1].upper()] = splitVals[2:]
                            
                            crntTime = dt.datetime.now(dt.timezone.utc)
                            self.dataParamTS[splitVals[1].upper()] = self.getTS(crntTime)
                            
                            sock.sendall(splitVals[1:].encode())
                            
                        elif splitVals[0].upper() == 'PING':
                            
                            #------------------------
                            # Return status to client
                            #------------------------                                    
                            sock.sendall("PONG!".encode())                     
                            
                        elif splitVals[0].upper() == 'LISTALL':
                            
                            msgLst = []
                            
                            #----------------------------
                            # Create a string of all keys 
                            # and values to send back
                            #----------------------------
                            for k in self.dataParams:
                                msgLst.append("{0:}={1:}".format(k," ".join(self.dataParams[k])))
                            
                            msg = ";".join(msgLst)
                            
                            sock.sendall(msg.encode())
                            
                        elif splitVals[0].upper() == 'LISTALLTS':   # List all time stamps
                            
                            msgLst = []
                            
                            #----------------------------
                            # Create a string of all keys 
                            # and values to send back
                            #----------------------------

                            for k in self.dataParamTS:
                                msgLst.append("{0:}={1:}".format(k,self.dataParamTS[k]))
                            
                            msg = ";".join(msgLst)
                            
                            sock.sendall(msg.encode())      

                        elif splitVals[0].upper() == 'LISTALLET':   # Elapsed time

                            print('LISTALLET')

                            msgLst = []

                            #----------------------------
                            # Create a string of all keys
                            # and values to send back
                            #----------------------------
                            crntTime = dt.datetime.now(dt.timezone.utc)

                            for k in self.dataParamTS:
                                TS = dt.datetime(int(self.dataParamTS[k][0:4]), int(self.dataParamTS[k][4:6]), int(self.dataParamTS[k][6:8]), int(self.dataParamTS[k][9:11]), int(self.dataParamTS[k][11:13]), int(self.dataParamTS[k][13:15]),  tzinfo=dt.timezone.utc)
                                ET = abs(crntTime - TS).seconds

                                ET = float("{:.2f}".format(ET/60.))  # Minutes

                                msgLst.append("{0:}={1:}".format(k,str(ET)))

                            msg = ";".join(msgLst)

                            #sock.sendall(msg)   
                            sock.sendall(msg.encode())               
                        
                        elif splitVals[0].upper() == 'WRITE_OPUS':
                            
                            #-----------------------------------------
                            # Check if Measurement summary file exists
                            #-----------------------------------------
                            fname = self.crntDataDir+"Measurement.log"

                            if not ckFile(fname):
                                with open(fname,'w') as fopen:
                                    fopen.write("{0:16s} {1:12s} {2:12s} {3:12s} {4:12s} {5:12s}\n".format("Measurement_Time","Filename","SNR_RMS","Peak_Amplitude","Pre_Amp_Gain","Signal_Gain"))
                                    fopen.write("{0:16s} {1:12s} {2:.3f} {3:12s} {4:12s} {5:12s}\n".format(splitVals[1],splitVals[2],float(splitVals[3]),splitVals[4],splitVals[5],splitVals[6]))
                            else:
                                with open(fname,'a') as fopen:
                                    fopen.write("{0:16s} {1:12s} {2:.3f} {3:12s} {4:12s} {5:12s}\n".format(splitVals[1],splitVals[2],float(splitVals[3]),splitVals[4],splitVals[5],splitVals[6]))
                            
                            #---------------------------------------------
                            # Temprorary Store last instance in dictionary
                            #---------------------------------------------
                            crntTime                          = dt.datetime.now(dt.timezone.utc)
                            self.dataParams["OPUS_LASTSCAN"]  = "{0:} {1:} {2:} {3:} {4:} {5:}".format(splitVals[1],splitVals[2],splitVals[3],splitVals[4],splitVals[5],splitVals[6])
                            self.dataParamTS["OPUS_LASTSCAN"] = self.getTS(crntTime)
                            #----------------------
                            # All entries are lists
                            #----------------------
                            self.dataParams["OPUS_LASTSCAN"] = self.dataParams["OPUS_LASTSCAN"].split()

                            print (self.dataParams["OPUS_LASTSCAN"])
                            
                            
                            #--------------------
                            # Get Sun information
                            #--------------------
                            #sunPixInfo   = self.dataParams["TRACKER_SUNPIX"]
                            #sunAzimuth   = self.dataParams["TRACKER_AZIMUTH"]
                            #sunElevation = self.dataParams["TRACKER_ELEVATION"]
                            
                            #----------------------------------
                            # Send email with Measurement Stats
                            #----------------------------------
                            toemails = [onemail for onemail in self.ctlFvars["Email_to"].strip().split(",")]

                            print ('Trying to send e-mail to: {}'.format(toemails))
    
                            msg = MIMEText("----------------------------Measurement DATA------------------------\n\n"             + \
                                           "Filename            = {0:>12s}\n".format(splitVals[2])                                + \
                                           "SNR                 = {0:.3f}\n".format(float(splitVals[3]))                          + \
                                           "Measurement time    = {0:>12s}\n".format(splitVals[1])                                + \
                                           "Peak Amplitude      = {0:>12s}\n".format(splitVals[4])                                + \
                                           "Pre-amp Gain        = {0:>12s}\n".format(splitVals[5])                                + \
                                           "Signal Gain         = {0:>12s}\n".format(splitVals[6]))
                                                   
                            msg['Subject']= "Sucessful {0:} at FL0 at {1:}, SNR= {2:.1f}".format(splitVals[2], splitVals[1], float(splitVals[3]))
                            msg['From']   = self.ctlFvars['Email_from']
                            msg['To']     = self.ctlFvars['Email_to']            
                        
                            # s = smtplib.SMTP('localhost')
                            s = smtplib.SMTP(self.ctlFvars['Local_Server'], int(self.ctlFvars['Local_port']))   
                            s.sendmail(self.ctlFvars['Email_from'], toemails, msg.as_string())
                            s.quit()  
                            print ('e-mail sent to: {}'.format(toemails))   

                            #------------------------
                            # Return status to client
                            #------------------------                                    
                            sock.sendall("Write Successfull".encode())                           
                            
                        else:
                            pass
                        
                        #------------------------
                        # Close socket connection
                        #------------------------
                        sock.close()
                        self.connection_list.remove(sock)   
                    
                    #------------------------------------------------------
                    # Remove client from socket list if client discconnects
                    #------------------------------------------------------
                    except:
                        sock.close()
                        self.connection_list.remove(sock)
                        continue
        
        #-------------
        # Close server
        #-------------
        self.closeServer()
                
    def closeConnect(self,sock):
        sock.close()
        self.connection_list.remove(sock)        

    def closeServer(self):
        ''' Close the TCP data server '''
        self.server_socket.close()
        
        
if __name__ == "__main__":

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

    #------------------------
    # Import observation list
    #------------------------
    #obsList = mainInputParse(obsListFile)
    
    #-----------
    # Run Server
    #-----------
    server1 = FTIRdataServer(ctlFvars,ctlFile)
    server1.runServer()
