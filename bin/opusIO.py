#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        opusIO.py
#
# Purpose:
#       Interface with OPUS software to run scans and read results
#
#
#
# Notes:
#       Arguments should be passed in order:
#       opusIO.py  <1> <2> <3> <4> <5> <6> <7>
#          <1>  - Name and Path of Macro file
#          <2>  - Name and Path of XPM file
#          <3>  - Daydir
#          <4>  - SNR lower
#          <5>  - SNR upper
#          <6>  - Scan duration [seconds]
#          <7>  - Number of scans
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
import datetime    as     dt
from   opusPipe    import OPUSpipe
from   time        import sleep
from   ckOPUS      import ckOPUS
#from   remoteDataWindowsClient  import FTIRdataClient
from   remoteData  import FTIRdataClient
from ModUtils     import *


                        #-------------------------#
                        # Define helper functions #
                        #-------------------------#
def usage():
    ''' Prints to screen standard program usage'''
    print ('opusIO.py')

def ckFile(fName,logFlg=False,exitFlg=False):
    '''Check if a file exists'''
    if not os.path.isfile(fName):
        print ('File %s does not exist' % (fName))
        if logFlg: logFlg.error('Unable to find file: %s' % fName)
        if exitFlg: sys.exit()
        return False
    else:
        return True  

def ckDir(dirName,logFlg=False,exitFlg=False):
    ''' Check the existence of a directory'''
    if not os.path.exists( dirName ):
        print ('Input Directory %s does not exist' % (dirName))
        if logFlg:       logFlg.error('Directory %s does not exist' % dirName)
        if exitFlg:      sys.exit()
        return False
    else:
        return True 


class OpusIO():
    def __init__(self, ctlFile):
        
        self.nArgs   = 4
        self.ctlFile = ctlFile
        
        
    def initialize(self):

        self.ctlFvars          = mainInputParse(self.ctlFile)
        
        #-------------------------
        # Initiate TCP data client
        #-------------------------
        self.remoteDataCl = FTIRdataClient(TCP_IP=self.ctlFvars['FTS_DataServ_IP'], TCP_Port=self.ctlFvars['FTS_DataServ_PORT'],BufferSize=4024)        

        self.opus_exe     = self.ctlFvars['Opus_exe']

        #-------------------------
        # Check if OPUS is running
        #-------------------------
        ckOPUS(exeDir=self.opus_exe)
        
        #-----------------------------
        # Create instance of OPUS pipe
        # and connect
        #-----------------------------
        self.op = OPUSpipe()
        self.op.connectPIPE()
        
    def startWatchDog(self,bin_Path,TO="30"):
        #self.proc = psutil.Popen(["python3",r"C:\bin\opusWatch.py",TO])
        #if not ( self.ctlFvars['Dir_bin'].endswith('\\') ): self.ctlFvars['Dir_bin']         = self.ctlFvars['Dir_bin'] + '\\'
        if not (bin_Path.endswith('\\') ): bin_Path   = bin_Path + '\\'
        #print(self.ctlFvars['Dir_bin']+"opusWatch.py")
        self.proc = psutil.Popen(["python3",bin_Path+"opusWatch.py",TO])
        return True
        
    def stopWatchDog(self):
        try:
            self.proc.kill()
            return True
        except:
            print ("Unable to kill opusWatch.py")
            return False

    def startIOwatch(self):


        #self.remoteDataCl.setParam("OPUS_CMND STANDBY")
    
        while True:
            
            #---------------------------
            # Find current date and time
            #---------------------------
            #crntTime = dt.datetime.utcnow()
            crntTime = dt.datetime.now(dt.timezone.utc)
            
            #-------------------------------------------
            # Indicate to data server that we are currently not 
            # taking a measurement
            #-------------------------------------------
            test = self.remoteDataCl.setParam("OPUS_STATUS IDLE")
		
            if test == False:
                sleep(5)
                continue
            
            #------------------------------------------
            # Send current date and time to data server
            #------------------------------------------
            #msg = "OPUS_TS {0:%Y%m%d.%H%M%S}".format(crntTime)
            #self.remoteDataCl.setParam(msg)
            
            #--------------------------------------------------
            # Determine if Solar Tracker is locked. If not wait 
            # to take measurements
			# Decided to comment this  
            #--------------------------------------------------
            #trckFlg = self.remoteDataCl.getParam("TRACKER_STATUS")
            #trckFlg = trckFlg.strip().split()
            #if trckFlg[0].upper() != "LOCK":
            #    print "Tracker is not currently locked at {}".format(dt.datetime.utcnow())
            #    sleep(10)
            #    continue
            
            #------------------------------------------
            # Check Remote data server for instructions
            #------------------------------------------
            scnFlg = self.remoteDataCl.getParam("OPUS_CMND")
            scnFlg = scnFlg.strip().split()

            print ('\n')
         
            if scnFlg[0].upper() == "QUIT":
                sys.exit()
            elif scnFlg[0].upper() == "STANDBY":
                sleep(5)
                print ("Opus Command is STANDBY...at {}".format(dt.datetime.now(dt.timezone.utc)))
                print ("Opus Status is IDLE.......at {}".format(dt.datetime.now(dt.timezone.utc)))
                continue
            elif scnFlg[0].upper() == "FREE":
                sleep(5)
                print ("OPUS Command is FREE...at {}".format(dt.datetime.now(dt.timezone.utc)))
                print ("Opus Status is IDLE....at {}".format(dt.datetime.now(dt.timezone.utc)))
                continue
            elif scnFlg[0].upper() != "TAKESCAN":
                sleep(5)
                print ("No scan specified......at {}".format(dt.datetime.now(dt.timezone.utc)))
                continue
			
            print ("OPUS Command is TAKESCAN...at {}".format(dt.datetime.now(dt.timezone.utc)))
                        
            #-----------------------------------
            # Check the connection to the PIPE
            # If connection is not good. Restart
            # OPUS and connect again
            #---------------------------------
            print ("\n\nRecieved scan command from TCP server...at {}".format(dt.datetime.now(dt.timezone.utc)))
            print ("Checking PIPE connection to OPUS........")
            #try:
            print("First startWatchDog - 30s") 
            print(bin_Path)
            self.startWatchDog(bin_Path,"30")
            self.op.ckPIPE()
            self.stopWatchDog()
            # except:
            #     print("First Except!!")
            #     self.stopWatchDog()
            #     ckOPUS(exeDir=self.opus_exe, overRideRestart=True)
            #     sleep(5)
            #     self.op.connectPIPE()
            print ("Connection to OPUS......................OK\n\n")
            
            #---------------------------
            # Parse Data Server commands
            #---------------------------
            macroName   = scnFlg[1]
            xpmName     = scnFlg[2]
            dayDir      = scnFlg[3]
            waitTime    = int(scnFlg[4])
            waitTimeStr = scnFlg[4]
            testFlg     = scnFlg[5]          

            print ("Following parameters sent from TCP Server:")
            print (" Macro Name         = {}".format(macroName))
            print (" Data Directory     = {}".format(dayDir))
            print (" Wait Time for Scan = {}".format(waitTimeStr))
            print (" Test Flag          = {}".format(testFlg))
            print (" xpmName            = {}\n\n".format(xpmName))
               
            #-------------------------
            # Check existance of files
            #-------------------------
            if any([not ckFile(macroName),not ckFile(xpmName)]):
                print ("Unable to find macro or xpm file!!")
                sleep(5)
                continue
        
            #----------------------------------------------
            # Have to split XPM into file and path for OPUS
            #----------------------------------------------
            xpmFile = os.path.basename(xpmName)
            xpmPath = os.path.dirname(xpmName)
        
            #-----------------------------
            # Check existance of directory
            #-----------------------------
            if not ckDir(dayDir):
                print ("Data directory does not exist!!!")
                continue
        
            #----------------------------------------
            # Send command to start macro with number 
            # of arguments and wait for "OK" response
            #----------------------------------------
            self.remoteDataCl.setParam("OPUS_STATUS SCANNING")
            
            cmndStr = "START_MACRO {0:} {1:}\n".format(macroName,self.nArgs)
            try:
                print ("\nInitiating Macro........................at {}".format(dt.datetime.now(dt.timezone.utc)))
                print("Second startWatchDog - 40s") 
                self.startWatchDog(bin_Path,"40")
                self.op.writePIPE(cmndStr)
                rtn = self.op.readPIPE(TO=30)
                self.stopWatchDog()
            except:
                print ("UNABLE TO INITIATE MACRO....Killing OPUS...")
                os.system("taskkill /im opus.exe")
                sleep(10)
                continue
        
            print ("Return from START_MACRO: {}".format(rtn))
        
            if not('ok' in rtn.strip().lower()):
                print ("Command: {}, NOT recieved by OPUS\n".format(cmndStr))
                continue
        
            #----------------------------------------
            # Send Input parameters and wait for "OK"
            #----------------------------------------
            cmndStr = "{0:}\n{1:}\n{2:}\n{3:}\n".format(xpmFile,xpmPath,dayDir,testFlg)
            try:
                print ("Sending input parameters to OPUS...")
                print("Third startWatchDog - 40s") 
                self.startWatchDog(bin_Path,"40")
                self.op.writePIPE(cmndStr)
                self.stopWatchDog()
            except:
                print ("UNABLE TO SEND INPUT PARAMETERS TO OPUS....Killing OPUS...")
                os.system("taskkill /im opus.exe")
                sleep(10)
                continue			
        
            #-----------------------------------------------------
            # Wait for return values from OPUS after scan complete
            #-----------------------------------------------------
            try:
                print ("Waiting for OPUS to return data...")
                print("First startWatchDog - waitTimeStr") 
                self.startWatchDog(bin_Path,waitTimeStr)          
                rtn = self.op.readPIPE(TO=waitTime)
                self.stopWatchDog()
            except:
                print ("UNABLE TO READ OPUS RETURN DATA.....Killing OPUS...")
                os.system("taskkill /im opus.exe")
                sleep(10)
                continue
		    
			#--------------------------------------------------
            # Get solar Radiances   
            #--------------------------------------------------
            # ExtERad  = self.remoteDataCl.getParam("EXTERN_E_RADIANCE")
            # ExtERad  = ExtERad.strip().split()
			
            # ExtERadS = self.remoteDataCl.getParam("EXTERN_E_RADIANCES")
            # ExtERadS = ExtERadS.strip().split()
			
            # ExtWRad  = self.remoteDataCl.getParam("EXTERN_W_RADIANCE")
            # ExtWRad  = ExtWRad.strip().split()
			
            # ExtWRadS = self.remoteDataCl.getParam("EXTERN_W_RADIANCES")
            # ExtWRadS = ExtWRadS.strip().split()   
			
            #--------------------------------------------------
            rtns = rtn.strip().split()
			
            print ("Return end program:......................{}\n".format(rtns[0]))		
            print ("Following parameters returned from macro:")
            print (" Time of Scan       = {}".format(rtns[2]))
            print (" OPUS Filename      = {}".format(rtns[4]))
            print (" SNR                = {}".format(rtns[5]))
            print (" Actual Preamp Gain = {}".format(rtns[7]))
            print (" Actual Signal Gain = {}".format(rtns[8]))
            print (" IFGM Peak Signal   = {}".format(rtns[6]))	
            # print " Ext E Rad          = {}".format(ExtERad[0])
            # print " Ext E RadS         = {}".format(ExtERadS[0])
            # print " Ext W Rad          = {}".format(ExtWRad[0])
            # print " Ext W RadS         = {}\n\n".format(ExtWRadS[0])				
			
            if not ('ok' in rtn.strip().lower()):
                print ("Command: {}, NOT received by OPUS\n".format(cmndStr))
                sleep(5)
                continue
            
            #-------------------------------------------
            # Set TAKESCAN parameter to FREE to indicate 
            # that previous scan has been taken
            #-------------------------------------------
            self.remoteDataCl.setParam("OPUS_CMND FREE")
        
            #-----------------------
            # Flush OPUS output pipe
            #-----------------------
            #self.op.flushPipe()
        
            #---------------------------------------------
            # Parse the output and send to the data server
            # for writing to log file
            # Values:
            # [1]   -  Time of Measurement
            # [2]   -  File Name
            # [3]   -  SNR [RMS]
            # [4]   -  Peak Amplitude
            # [5]   -  Pre-Amp Gain
            # [6]   -  Signal Gain
            #---------------------------------------------
            opusRtnVals = rtn.strip().split()[2:]
            opusRtnVals = [val.replace(',','') for val in opusRtnVals]
			
			#-----------------------
			# Append radiances to rtns
			#-----------------------
            # opusRtnVals.append(ExtERad[0])
            # opusRtnVals.append(ExtERadS[0])
            # opusRtnVals.append(ExtWRad[0])
            # opusRtnVals.append(ExtWRadS[0])
        
            #--------------------------------------------------------------
            # Write data to TCP server. The second value in opusRtnVals is 
            # indication of GMT time "(GMT+0)". Remove this from the return
            # string for the data server
            #--------------------------------------------------------------
            print ("\nSending OPUS return data to TCP server.....")
            opusRtnVals.pop(1)
            messg  = (" ").join( opusRtnVals   )
            
            self.remoteDataCl.writeSpectra(messg)
            sleep(2)
            self.remoteDataCl.setParam("OPUS_LASTXPM " + xpmFile)

            
if __name__ == "__main__":

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    # try:
    #     ctlFile  = sys.argv[1]
    # except:
    #     ctlFile  = "C:/bin/ops/FL0_Defaults.input"
        #print('Error: ctlFile needed in remoteData.py ... exiting!')
        #exit()

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

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile, exitFlg=True)
    
    #----------------
    # Create Instance
    #----------------
    opusMeas = OpusIO(ctlFile)
    
    #-----------
    # Initialize
    #-----------
    opusMeas.initialize()
    
    #----
    # Run
    #----
    opusMeas.startIOwatch()
