##! c:\Python27\python
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
import ntpath
from ModUtils     import *


#---------------------------
# Edit here only
 #---------------------------
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

dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
portNum        = ctlFvars['FTS_DATASERV_PORT']
bin_Path       = ctlFvars['DIR_WINBIN']
ctlFile        = ctlFvars['CTL_FILE']

#'----------------------------------'
# Get Python PIDs
#'----------------------------------'
def get_Pypid():

    pids = {}

    for proc in psutil.process_iter():
        
        try:
            _name = proc.name()

            #print(_name)
           
            if _name in ['python.exe', 'python3.10.exe', 'Python2.7.exe', 'Python', 'Python3.exe', 'python3.exe']:
                try:
                    cmd = proc.cmdline()
                except psutil.AccessDenied:
                    continue

                try:
             
                    if cmd[1].endswith('.py'):
                        since = datetime.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                        pids[proc.pid] = {'since': since, 'pid': proc.pid, 'name':cmd[1]}
                except: continue
           
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
# Start a python script via .bat 
#'----------------------------------'
def startPy(pyScript, args=False):
    #----------------------------------
    # Get python PIDs
    #----------------------------------
    
    pids = get_Pypid()
  
    #----------------------------------
    # Get specific opusIO PID
    #----------------------------------
    
    for p in pids:
        name = pids[p]['name']        
        if name.strip().split('\\')[-1] == pyScript+'.py':
            print(pyScript+'.py is already running... exiting')
            exit()
 
    print ("\nNo instances of {}.py found running!!".format(pyScript))

    #--------------------------------------------
    # Start remoteData.py
    #--------------------------------------------
    try:
        print ('Starting {}.py...at {}'.format(pyScript, datetime.datetime.utcnow()))
        if args: 
            #subprocess.call([r"C:\bin\{}.bat".format(pyScript),args], shell=True)
            subprocess.call([r"{}{}.bat".format(bin_Path,pyScript),args], shell=True)
        
        else:    
            #subprocess.call([r"C:\bin\{}.bat".format(pyScript)], shell=True)
            subprocess.call([r"{}{}.bat".format(bin_Path,pyScript)], shell=True)
        sleep(5)
    except:
        print ('Unable to re-start {}.py...at {}'.format(pyScript,datetime.datetime.utcnow()))


def killPy(pyScript):

    pids = get_Pypid()

    for p in pids:
        name = pids[p]['name']

        if name.strip().split('\\')[-1] == pyScript+'.py':
            print (pyScript+'.py is currently running ...at {}\n'.format(datetime.datetime.utcnow()))
            print('Killing current running {}.py program'.format(pyScript))
            os.system("taskkill /F /T /PID {}".format(pids[p]['pid']))


#'----------------------------------'
# Start opusIO.py and makes sure will be running
#'----------------------------------'
def ckscripts(ctlFile, ln2ResFlg=False):
   
    # INPUT
    if ln2ResFlg: pyPrograms     = ['remoteData', 'opusIO', 'WebParser']
    else:         pyPrograms     = ['remoteData', 'opusIO', 'WebParser']


    print ('-------------------------------------------------------------------------------')
    print ('   Checking on {}'.format(pyPrograms))
    print ('-------------------------------------------------------------------------------')

    #----------------------------------
    # Get python PIDs
    #----------------------------------
    pids = get_Pypid()
    print ("\nNumber of python PIDs = {}".format(len(pids)))
    #print(pids)
    #exit()
    
    #----------------------------------
    # Get specific opusIO PID
    #----------------------------------
    pidName      = []
    pidNumber    = []
    
    for p in pids:
        name = pids[p]['name']        

        for pyP in pyPrograms:

            if name.strip().split('\\')[-1] == pyP+'.py':
                print ('{}.py is currently running ...at {}\n'.format(pyP, datetime.datetime.utcnow()) )
                head, tail = ntpath.split(pids[p]['name'])
                pidName.append(tail.split('.')[0])
                pidNumber.append(pids[p]['pid'])
    
    #pidName.sort()
    #pyPrograms.sort()

    pidName = sorted(pidName, key=lambda x: pyPrograms.index(x))

    if pidName == pyPrograms:
        print('\nAll Needed programs are running!!')
        return True

    newlist = [] # empty list to hold unique elements from the list
    duplist = [] # empty list to hold the duplicate elements from the list
    dupID   = [] # empty list to hold the duplicate elements from the list
    
    for i, p_i in enumerate(pidName):

        if p_i not in newlist:
            newlist.append(p_i)
        else:
            duplist.append(p_i) 
            dupID.append(pidNumber[i])

    #print("\nList of duplicates:{}".format(duplist))
    #print("Unique Item List: {}\n".format(newlist)) 


    if len(duplist) >= 1:
        for d_i, d in enumerate(duplist):

            print ("More than one {}.py programs running\n".format(d))
            print ("Killing current running {}.py programs\n".format(d))
            os.system("taskkill /F /T /PID {}".format(dupID[d_i]))


    #----------------------------------
    #
    #----------------------------------
    for pyP in pyPrograms:

        if pyP in newlist: continue
        else:
            print ("\nNo instances of {}.py found running!!".format(pyP))

            #--------------------------------------------
            # Start remoteData.py
            #--------------------------------------------
            try:
                print ('Starting {}{}.py...at {}'.format(bin_Path,pyP, datetime.datetime.utcnow()))
                subprocess.call([r"{}{}.bat".format(bin_Path, pyP),ctlFile], shell=True)
                restartremFlg   = False
                sleep(5)
            except:
                print ('Unable to re-start {}.py...at {}'.format(pyP,datetime.datetime.utcnow()))



if __name__ == "__main__":
    ckscripts()


