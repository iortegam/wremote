#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        ckpy.py
#
# Purpose:
#       Program to start opusIO.py and check if it is running
#       If opusIO.py is not running it will try to re-start
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
import signal
import psutil
import subprocess 
from   time       import sleep
import re
import datetime

#'----------------------------------'
# Get Python PIDs
#'----------------------------------'
def get_Pypid():

    pids = {}

    for proc in psutil.process_iter():
        
        try:
            _name = proc.name()
           
            if _name in ['python.exe', 'python3.10.exe', 'Python2.7.exe', 'Python3.exe']:
                try:
                    cmd = proc.cmdline()
                except psutil.AccessDenied:
                    continue
             
                if cmd[1].endswith('.py'):
                    since = datetime.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                    pids[proc.pid] = {'since': since, 'pid': proc.pid, 'name':cmd[1]}
           
        except psutil.AccessDenied:
            continue        
	
    return pids

#'----------------------------------'
# Get Specific PID (e.g., opus.exe)
#'----------------------------------'
def get_pid(pName):

    pids = []

    for proc in psutil.process_iter():
        try:
            if pName in proc.name(): pids.append(proc.pid)
        except:
            pass

    return pids

#'----------------------------------'
# Kill specific PID (e.g., opus.exe)
#'----------------------------------'
def killOPUS(pids):
    
    for pid in pids:
        os.system("taskkill /F /T /PID {}".format(pid))  

#'----------------------------------'
# Start opusIO.py and makes sure will be running
#'----------------------------------'
def ckscripts(ctlFile):
    
    print ('-------------------------------------------------------------------------------')
    print ('   Checking on opusIO.py, WebParser.py, MetParser.py, remoteData.py  & flod.py ')
    print ('-------------------------------------------------------------------------------')

    restartopusFlg = False    # 
    restartremFlg  = False
    restartwebFlg  = False
    restartmetFlg  = False
    restartfl0dFlg = False
    restartserdFlg = False
    
    # try:
    #     print 'Starting opusIO.py...at {}'.format(datetime.datetime.utcnow())
    #     proc = psutil.Popen([r"C:\bin\opusIO.bat"])
    #     sleep(10)
    # except:
    #     print 'Unable to Start opusIO.py...at {}'.format(datetime.datetime.utcnow())
    
   
    #----------------------------------
    # Get python PIDs
    #----------------------------------
    #sleep(5)
    
    pids = get_Pypid()
    #print ("\nNumber of python PIDs = {}".format(len(pids)))
    #print(pids)
    #exit()
    
    #----------------------------------
    # Get specific opusIO PID
    #----------------------------------
    opusIOpid = []
    remotepid = []
    webpid    = []
    metpid    = []
    fl0dpid   = []
    
    for p in pids:
        name = pids[p]['name']

        if name.strip().split('\\')[-1] == 'remoteData.py':
            print ('remoteData.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()) )
            remotepid.append(pids[p]['pid'])

        elif name.strip().split('\\')[-1] == 'opusIO.py':
            print ('opusIO.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()) )
            opusIOpid.append(pids[p]['pid'])
        

        elif name.strip().split('\\')[-1] == 'WebParser.py':
            print ('WebParser.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()) )
            webpid.append(pids[p]['pid'])

        elif name.strip().split('\\')[-1] == 'MetParser.py':
            print ('MetParser.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()) )
            metpid.append(pids[p]['pid'])

        elif name.strip().split('\\')[-1] == 'fl0d.py':
            print ('fl0d.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()) )
            fl0dpid.append(pids[p]['pid'])

    #--------------------------------------------------------
    # If opusIO.py e
    #--------------------------------------------------------
    if (len(opusIOpid) == 1) & (len(remotepid) == 1) & (len(webpid) == 1) & (len(metpid) == 1) & (len(fl0dpid) == 1) :
        return True

    else:

        #--------------------------------------------------------
        # If mulitple remoteData.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(remotepid) > 1:
            print ("More than one remoteData.py programs running. Total number = {}\n".format(len(remotepid)))
            print ("Killing current running remoteData.py programs\n")
            for pid in remotepid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartremFlg = True

        #---------------------------------------------
        # If no OPUS programs running set restart flag
        #---------------------------------------------
        if len(remotepid) == 0: 
            print ("No instances of remoteData.py found running!!")
            restartremFlg = True
        
        if restartremFlg:        
            #--------------------------------------------
            # Start remoteData.py
            #--------------------------------------------
            try:
                print ('Starting remoteData.py...at {}'.format(datetime.datetime.utcnow()))
                subprocess.call([r"C:\bin\remoteData.bat",ctlFile], shell=True)
                restartremFlg   = False
                sleep(5)
            except:
                print ('Unable to re-start remoteData.py...at {}'.format(datetime.datetime.utcnow()))

        #--------------------------------------------------------
        # If mulitple WebParser.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(webpid) > 1:
            print ("More than one WebParser.py programs running. Total number = {}\n".format(len(webpid)))
            print ("Killing current running WebParser.py programs\n")
            for pid in webpid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartwebFlg = True

        #---------------------------------------------
        # If no WebParser programs running set restart flag
        #---------------------------------------------
        if len(webpid) == 0: 
            print ("No instances of WebParser.py found running!!")
            restartwebFlg = True
        
        if restartwebFlg:        
            #--------------------------------------------
            # Start WebParser.py
            #--------------------------------------------
            try:
                print ('Starting WebParser.py...at {}'.format(datetime.datetime.utcnow()))
                #proc = psutil.Popen([r"C:\bin\WebParser.bat"])
                subprocess.call([r"C:\bin\WebParser.bat",ctlFile], shell=True)
                restartwebFlg   = False
                sleep(5)
            except:
                print ('Unable to re-start WebParser.py...at {}'.format(datetime.datetime.utcnow()))

        #--------------------------------------------------------
        # If mulitple MetParser.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(metpid) > 1:
            print ("More than one MetParser.py programs running. Total number = {}\n".format(len(metpid)))
            print ("Killing current running MetParser.py programs\n")
            for pid in metpid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartmetFlg = True

        #---------------------------------------------
        # If no MetParser programs running set restart flag
        #---------------------------------------------
        if len(metpid) == 0: 
            print ("No instances of MetParser.py found running!!")
            restartmetFlg = True
        
        if restartmetFlg:        
            #--------------------------------------------
            # Start MetParser.py
            #--------------------------------------------
            try:
                print ('Starting MetParser.py...at {}'.format(datetime.datetime.utcnow()))
                #proc = psutil.Popen([r"C:\bin\MetParser.bat"])
                subprocess.call([r"C:\bin\MetParser.bat",ctlFile], shell=True)
                restartmetFlg   = False
                sleep(5)
            except:
                print ('Unable to re-start MetParser.py...at {}'.format(datetime.datetime.utcnow()))

    
        #--------------------------------------------------------
        # If mulitple opusIO.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(opusIOpid) > 1:
            print ("More than one opusIO.py programs running. Total number = {}\n".format(len(opusIOpid)))
            print ("Killing current running OPUS programs\n")
            for pid in opusIOpid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartopusFlg = True

        #---------------------------------------------
        # If no OPUS programs running set restart flag
        #---------------------------------------------
        if len(opusIOpid) == 0: 
            print ("No instances of opusIO.py found running!!")
            restartopusFlg = True
        
        if restartopusFlg:
            #--------------------------------------------
            # Kill OPUS in case is running (avoid pipe errors)
            #--------------------------------------------
            
            pids = get_pid("opus.exe")
            
            if len(pids) > 1:
                print ('Killing OPUS...at {}'.format(datetime.datetime.utcnow()))
                killOPUS(pids) 
                sleep(2)
            #--------------------------------------------
            # Start opusIO.py
            #--------------------------------------------
            try:
                print ('Starting opusIO.py...at {}'.format(datetime.datetime.utcnow()))
                #proc = psutil.Popen([r"C:\bin\opusIO.bat"])
                subprocess.call([r"C:\bin\opusIO.bat",ctlFile], shell=True)
                restartopusFlg   = False
                sleep(30)
            except:
                print ('Unable to re-start opusIO.py...at {}'.format(datetime.datetime.utcnow()))



        #--------------------------------------------------------
        # If mulitple fl0d.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(fl0dpid) > 1:
            print ("More than one fl0d.py programs running. Total number = {}\n".format(len(fl0dpid)))
            print ("Killing current running fl0d.py programs\n")
            for pid in fl0dpid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartfl0dFlg = True

        #---------------------------------------------
        # If no WebParser programs running set restart flag
        #---------------------------------------------
        if len(fl0dpid) == 0: 
            print ("No instances of fl0d.py found running!!")
            restartfl0dFlg = True
        
        if restartfl0dFlg:        
            #--------------------------------------------
            # Start WebParser.py
            #--------------------------------------------
            try:
                print ('Starting fl0d.py...at {}'.format(datetime.datetime.utcnow()))
                #proc = psutil.Popen([r"C:\bin\WebParser.bat"])
                subprocess.call([r"C:\bin\fl0d.bat",ctlFile], shell=True)
                restartwebFlg   = False
                sleep(5)
            except:
                print ('Unable to re-start fl0d.py...at {}'.format(datetime.datetime.utcnow()))


if __name__ == "__main__":
    ckscripts()


