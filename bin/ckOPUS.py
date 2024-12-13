#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        ckOPUS.py
#
# Purpose:
#       Program checks to see if multiple versions of OPUS are running and if pipes are
#       present. If not start new version of OPUS
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

import os
import stat
import signal
import psutil
import subprocess 
from   time       import sleep
from ModUtils     import *

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

ctlFvars      = mainInputParse(ctlFile)

# Get some local variables
opusExe       = ctlFvars["Opus_exe"]
print("opusExe : {}".format(opusExe))



def get_pid(pName):

    pids = []

    for proc in psutil.process_iter():
        try:
            if pName in proc.name(): pids.append(proc.pid)
        except:
            pass

    return pids

def ckOPUS(exeDir=False, overRideRestart=False):

    restartFlg = False

    #----------------------------------
    # Get PIDs of OPUS versions running
    #----------------------------------
    pids = get_pid("opus.exe")

    print ("Number of PIDs = {}".format(len(pids)))

    #---------------------------------------------
    # OverRideRestart just kills all OPUS programs 
    # and restarts no matter what the state is
    #---------------------------------------------


    if overRideRestart:
        for pid in pids:
            os.system("taskkill /F /T /PID {}".format(pid))
        #--------------------------FL0------------------------------------			
        #if exeDir:
        #    psutil.Popen([exeDir, 
        #              r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])
        #else:
        #    psutil.Popen([r"C:\Program Files (x86)\Bruker\OPUS_7.8.44\opus.exe", 
        #              r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])
        psutil.Popen([opusExe, r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])
        

        sleep(20)         

    #------------------
    # Non-overRide mode
    #------------------
    else:

        #--------------------------------------------------------
        # If mulitple PIDs exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(pids) > 1:
            print ("More than one OPUS programs running. Total number = {}\n".format(len(pids)))
            print ("Killing current running OPUS programs\n")
            for pid in pids:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartFlg = True
    
    
        #---------------------------------------------
        # If no OPUS programs running set restart flag
        #---------------------------------------------
        elif len(pids) == 0: 
            print ("No instances of OPUS found running. Starting new OPUS..\n")
            restartFlg = True
    
        #--------------------------------------------
        # Restart OPUS with pipes if restart flag set
        #--------------------------------------------
        if restartFlg:

            psutil.Popen([opusExe, r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])

            #if exeDir:
            #    psutil.Popen([exeDir, 
            #              r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])
            #else:
            #    psutil.Popen([r"C:\Program Files (x86)\Bruker\OPUS_7.8.44\opus.exe", 
            #              r"/OPUSPIPE=ON" r"/DIRECTLOGINPASSWORD=Administrator@OPUS"])
            
            sleep(20)    

if __name__ == "__main__":
    ckOPUS()


