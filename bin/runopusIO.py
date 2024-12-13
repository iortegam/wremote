#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        ckopusIO.py
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
           
            if _name in ['python.exe', 'python3.exe', 'Python.exe', 'Python3.exe']:
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
def ckopusIO():
    
    print '----------------------------------'
    print '     Starting runopusIO.py        '
    print '----------------------------------'
    
    restartFlg = False
    
    try:
        print 'Starting opusIO.py...at {}'.format(datetime.datetime.utcnow())
        proc = psutil.Popen([r"C:\bin\opusIO.bat"])
        sleep(10)
    except:
        print 'Unable to Start opusIO.py...at {}'.format(datetime.datetime.utcnow())
    
    while True:
        #----------------------------------
        # Get python PIDs
        #----------------------------------
        sleep(5)
        
        pids = get_Pypid()
        print "\nNumber of python PIDs = {}".format(len(pids))
        
        #----------------------------------
        # Get specific opusIO PID
        #----------------------------------
        opusIOpid = []
        
        for p in pids:
            name = pids[p]['name']
            if name.strip().split('\\')[-1] == 'opusIO.py':
                print 'opusIO.py is currently running ...at {}'.format(datetime.datetime.utcnow())
                opusIOpid.append(pids[p]['pid'])
        
        #--------------------------------------------------------
        # If mulitple opusIO.py exist... Kill all and set restart flag
        #--------------------------------------------------------
        if len(opusIOpid) > 1:
            print "More than one opusIO.py programs running. Total number = {}\n".format(len(opusIOpid))
            print "Killing current running OPUS programs\n"
            for pid in opusIOpid:
                os.system("taskkill /F /T /PID {}".format(pid))
            restartFlg = True

        #---------------------------------------------
        # If no OPUS programs running set restart flag
        #---------------------------------------------
        if len(opusIOpid) == 0: 
            print "No instances of opusIO.py found running!!"
            restartFlg = True
        
        if restartFlg:
            #--------------------------------------------
            # Kill OPUS in case is running (avoid pipe errors)
            #--------------------------------------------
            
            pids = get_pid("opus.exe")
            
            if len(pids) >= 1:
                print 'Killing OPUS...at {}'.format(datetime.datetime.utcnow())
                killOPUS(pids) 
                sleep(5)
            #--------------------------------------------
            # Start opusIO.py
            #--------------------------------------------
            try:
                print 'Starting opusIO.py...at {}'.format(datetime.datetime.utcnow())
                proc = psutil.Popen([r"C:\bin\opusIO.bat"])
                restartFlg   = False
                sleep(5)
            except:
                print 'Unable to re-start opusIO.py...at {}'.format(datetime.datetime.utcnow())
  

if __name__ == "__main__":
    ckopusIO()


