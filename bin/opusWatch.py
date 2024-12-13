#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        opusWatch.py
#
# Purpose:
#       Program to watch and see if OPUS hangs
#
#
#
# Notes:
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


#---------------
# Import modules
#---------------
import os 		
import sys 			
import psutil
import subprocess 
import datetime    as     dt
from   time        import sleep
#from   remoteDataWindowsClient  import FTIRdataClient
from   remoteData  import FTIRdataClient
from ModUtils     import *
                        #-------------------------#
                        # Define helper functions #
                        #-------------------------#
 

def killOPUS(pids):
    
    for pid in pids:
        os.system("taskkill /F /T /PID {}".format(pid))     
    
    #os.system("taskkill /im opus.exe")
    #sleep(30)
    #return True


def get_pid(pName):

    pids = []

    for proc in psutil.process_iter():
        try:
            if pName in proc.name(): pids.append(proc.pid)
        except:
            pass

    return pids


#class OpusWatch():
    #def __init__(self):
        
        ##-------------------------
        ## Initiate TCP data client
        ##-------------------------
        #self.remoteDataCl = FTIRdataClient(TCP_IP="192.168.1.100", TCP_Port=5555,BufferSize=4024)
        

    #def startOPUSwatch(self):
    
        #while True:
            
            ##----------------------------------------
            ## Wait time [seconds] before killing opus
            ##----------------------------------------
            #waitTime = 400
            
            ##--------------------------
            ## Get current date and time
            ##--------------------------
            #crntTime = dt.datetime.utcnow()
            
            ##-------------------------------
            ## Get Time Stamp of last opusIO 
            ## connection to data base server
            ##-------------------------------
            #opusTS = self.remoteDataCl.getParam("OPUS_TS")
            
            ##-----------------------------------------------------
            ## If unable to connect to data base wait and try again
            ##-----------------------------------------------------
            #if opusTS == False:
                #sleep(10)
                #continue
            
            ##----------------------------------------------
            ## Compare time of last connect and current time
            ## If greater than N seconds kill OPUS
            ##----------------------------------------------
            #try:
                #opusLastConnect = dt.datetime(int(opusTS[0:4]),int(opusTS[4:6]),int(opusTS[6:8]),
                                              #int(opusTS[9:11]),int(opusTS[11:13]),int(opusTS[13:15]))
            #except:
                #sleep(10)
                #continue
            
            #if abs((crntTime - opusLastConnect).total_seconds()) > waitTime:
                #try:    
                    #killOPUS()
                    #self.remoteDataCl.setParam("OPUS_KILLOPUS {0:%Y%m%d_%H%M%S}".format(crntTime))
                    #print "OPUS program killed at {}".format(crntTime)
                #except: pass
                #continue
            #else:
                #print "Opus running nominally at {}".format(crntTime)
                #sleep(10)
            

if __name__ == "__main__":
    
    #----------------------------------------------
    # Retrieve command line OPUS time out [seconds]
    #----------------------------------------------
    try:    TO = int(sys.argv[1])
    except: TO = 60

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

    #print("\nLocal input parameters:")
    #for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']
        
    #-------------------------
    # Initiate TCP data client
    #-------------------------
    ##remoteDataCl = FTIRdataClient(TCP_IP="192.168.1.100", TCP_Port=5555,BufferSize=4024)
    remoteDataCl = FTIRdataClient(TCP_IP=dataServer_IP, TCP_Port=portNum,BufferSize=4024)

    #------------------------------------------------
    # Wait 5 minutes on startup for OPUS to initalize
    #------------------------------------------------
    sleep(TO)
    pids = get_pid("opus.exe")
    killOPUS(pids)
    
    #--------------------------
    # Get current date and time
    #--------------------------
    crntTime = dt.datetime.utcnow()    
    remoteDataCl.setParam("OPUS_KILLOPUS {0:%Y%m%d_%H%M%S}".format(crntTime))
