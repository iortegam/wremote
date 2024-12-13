#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        setMainInputs.py
#
# Purpose:
#       This programs parses the main input file and sends them to the TCP server
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
import sys
from   time           import sleep
from   trackerUtils   import ckFile, mainInputParse
from   remoteData     import FTIRdataClient



class MainInputTCPserver(FTIRdataClient):
    
    
    def __init__(self,inputFileName):
        
        ckFile(inputFileName,exitFlg=True)
        self.data  = {}
        self.fname = inputFileName
        tempData   = mainInputParse(inputFileName)
        
        FTIRdataClient.__init__(self,TCP_IP=tempData["FTS_DataServ_IP"],TCP_Port=tempData["FTS_DataServ_PORT"],BufferSize=tempData["FTS_DATASERV_BSIZE"])        
        
    def parseInput(self):
        
        self.data = mainInputParse(self.fname)
        
    def sendMainInpTCP(self):
        #--------------------------
        # Write data to data server
        #--------------------------
        if not self.data:
            print "No data to write from web parser..."
            return False
        
        for key in self.data:
            message = key + " " + self.data[key]
            self.setParam(message)        

if __name__ == "__main__":
    
    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    try:
        mainInputFile  = sys.argv[1]
    except:
        mainInputFile = "/home/mloftir/remote/ops/MLO_Defaults.input"
    
    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(mainInputFile,exitFlg=True)
    
    mainInp = MainInputTCPserver(mainInputFile)
    mainInp.parseInput()
    mainInp.sendMainInpTCP()
    