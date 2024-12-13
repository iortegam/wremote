#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        opusPipe.py
#
# Purpose:
#       This class is used for piping commands to OPUS via FIFO
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


import os
import win32pipe, win32file
#import win32file
#import pywin32
#from pywin32 import win32pipe, win32file
#from Queue import Queue,Empty       
import queue
#import Empty       
import string  
import time  

import multiprocessing
from ModUtils     import *

                #-------------------------#
                # Define helper functions #
                #-------------------------#

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

dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
portNum        = ctlFvars['FTS_DATASERV_PORT']
bin_Path       = ctlFvars['DIR_WINBIN']
ctlFile        = ctlFvars['CTL_FILE']


class OPUSpipe(object):
    '''This class with OPUS via named pipes'''

    def __init__(self):

        self.opusPIPE =  r"\\.\pipe\OPUS"
        #self.q        = Queue()
        self.q        = queue.Queue()
        #--------------------------------
        # Set default time out 30 seconds
        #--------------------------------
        self.defaultTO = 30
        
    def connectPIPE(self):
        #-------------------------------------------------
        # Open OPUS pipe. This must stay open all the time
        # If it is closed the OPUS will destroy the pipe
        #-------------------------------------------------
        self.opusHndl = win32file.CreateFile(self.opusPIPE,win32file.GENERIC_READ | win32file.GENERIC_WRITE,\
                                             win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,   \
                                             None, win32file.OPEN_EXISTING, 0 , None)        
           
    def writePIPE(self,command):
        
        if not command.endswith("\r\n"): command += "\r\n"
        
        win32file.SetFilePointer(self.opusHndl,0,win32file.FILE_BEGIN)
        win32file.WriteFile(self.opusHndl,command.encode(),None)
        win32file.FlushFileBuffers(self.opusHndl)
    
        return 1

    def readPIPE(self,TO=60.0):
    
        win32file.SetFilePointer(self.opusHndl,0,win32file.FILE_BEGIN)
        self.q.put(win32file.ReadFile(self.opusHndl,1024,None),timeout=60.0)
        win32file.FlushFileBuffers(self.opusHndl)
    
        try: 
            data = self.q.get(timeout=TO)[1]
        except: 
            data = ""
            
        #---------------------------
        # Clear all entries in queue
        #---------------------------
        with self.q.mutex:
            self.q.queue.clear()
    
        return data.decode()
    
    def readPIPE2(self,queue,TO):
    
        win32file.SetFilePointer(self.opusHndl,0,win32file.FILE_BEGIN)
        queue.put(win32file.ReadFile(self.opusHndl,1024,None))
        queue.close()

    def readPipe(self,TO=60.0):

        queue = multiprocessing.Queue(1)
        proc  = multiprocessing.Process(target=self.readPIPE2,args=(queue,TO))
        proc.start()
        
        try:
            data = queue.get(True,timeout=10.0)
            win32file.FlushFileBuffers(self.opusHndl)
        except Queue.empty:
            data = ""
        finally:
            proc.terminate()           

    def ckPIPE(self):
        #self.writePIPE("START_MACRO c:\\\\bin\\testPIPE.mtx 1\r\n")
        self.writePIPE("START_MACRO {}testPIPE.mtx 1\r\n".format(bin_Path))
        
        rtn1 = self.readPIPE(1)
        self.writePIPE("3\n")
        rtn2 = self.readPIPE(1)
        
        if (rtn2.strip().split()[-1] == "8"): return True
        else:                                 return False
        
    def flushPipe(self):
        #-------------------------------------
        # Flush pipe until nothing is returned
        #-------------------------------------
        flushFlg = True

        while flushFlg:

            rtn = self.readPIPE(TO=1.0)

            if not rtn: flushFlg = False

        return rtn



