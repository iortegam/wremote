#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        MetParser.py
#
# Purpose:
#       Interface with OPUS software to run scans and read results
#
#
#
# Notes:
#
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
import sys
#import urllib2
from urllib.request import urlopen
import os
import socket
import select
import datetime       as     dt
from time             import sleep
from trackerUtils     import *
from remoteData       import FTIRdataClient
from bs4              import BeautifulSoup  as bs


class WebParser(FTIRdataClient):

    def __init__(self,WebPageParse_IP="192.168.50.110",TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=4024):

        self.TCPserverIP = TCP_IP_in
        self.webAddress  = WebPageParse_IP
        self.data        = {}

        FTIRdataClient.__init__(self,TCP_IP=TCP_IP_in,TCP_Port=TCP_Port_in,BufferSize=BufferSize_in)
        
    def checkWebAddress(self):
        #print(self.webAddress)

        #------------------------
        # Check if address exists
        #------------------------
        try:
            #urllib2.urlopen(self.webAddress)
            res = urlopen(self.webAddress)
        #content = res.read()
        #print(content)
            return True
        except:
            print ("Unable to open web address: {}".format(self.webAddress))
            print (" at : {}".format(dt.datetime.now(dt.timezone.utc)))
            return False

    def sendData(self):
        #--------------------------
        # Write data to data server
        #--------------------------
        if not self.data:
            print ("No data to write from web parser...")
            return False

        for key in self.data:
            message = key + " " + self.data[key]
            self.setParam(message)

        #---------------------------------------------
        # Send time stamp of connection to data server
        #---------------------------------------------
        crntDateTime = dt.datetime.now(dt.timezone.utc)
        #dateTstr = "{0:}{1:02}{2:02}_{3:02}{4:02}{5:02}".format(crntDateTime.year,crntDateTime.month,crntDateTime.day,crntDateTime.hour,
                                                                #crntDateTime.minute,crntDateTime.second)
        #self.setParam("BRUKER_TS " + dateTstr)




class MetwebParser(WebParser):

    def __init__(self,WebPageParse_IP="192.168.50.110",TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=1024):

        WebParser.__init__(self,WebPageParse_IP=WebPageParse_IP,TCP_IP_in=TCP_IP_in,TCP_Port_in=TCP_Port_in,BufferSize_in=BufferSize_in)


    def parseDiagnostics(self):
        #----------------------------
        # Check if address is visible
        #----------------------------
        if not self.checkWebAddress(): return False

        #print('here')

        diagPage = self.webAddress
        #webpg    = urllib2.urlopen(diagPage)
        webpg    = urlopen(diagPage)
        data     = []

        #-----------------------------
        # Open page with Beautifulsoup
        #-----------------------------
        soup = bs(webpg)

        for i, s in enumerate(soup):
           
            rows  = s.split('\n')

        for i, r in enumerate(rows):

            if i >=2:

                r = r.strip().split(':')
                cols = [element.strip() for element in r]
                data.append([element for element in cols if element])

        #print(data)
        #---------------------------
        # Add elements to dictionary
        #---------------------------

        for row in data:
            try:
                self.data["ATM_"+('_').join(row[0].upper().split())+'_EOL'] = row[1].upper()
            except:
                continue


    def parseCUDiagnostics(self):
        #----------------------------
        # Check if address is visible
        #----------------------------
        if not self.checkWebAddress(): return False

        diagPage = self.webAddress
        #webpg    = urllib2.urlopen(diagPage)
        webpg    = urlopen(diagPage)
        data     = []

        #-----------------------------
        # Open page with Beautifulsoup
        #-----------------------------
        soup = bs(webpg)

        print (soup)

        #--------------
        # Extract Table
        #--------------
        table = soup.find('table')

        print (table)

        #---------
        # Get rows
        #---------
        rows = table.find_all('tr')

        print (rows)

        exit()

        for i, s in enumerate(soup):
           
            rows  = s.split('\n')

        for i, r in enumerate(rows):

            if i >=2:

                r = r.strip().split(':')
                cols = [element.strip() for element in r]
                data.append([element for element in cols if element])

        #---------------------------
        # Add elements to dictionary
        #---------------------------

        for row in data:
            try:
                self.data["ATM_"+('_').join(row[0].upper().split())] = row[1].upper()
            except:
                continue

class RadwebParser(WebParser):

    def __init__(self,WebPageParse_IP="192.168.50.110",TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=1024):

        WebParser.__init__(self,WebPageParse_IP=WebPageParse_IP,TCP_IP_in=TCP_IP_in,TCP_Port_in=TCP_Port_in,BufferSize_in=BufferSize_in)


    def parseDiagnostics(self):
        #----------------------------
        # Check if address is visible
        #----------------------------
        if not self.checkWebAddress(): return False

        diagPage = self.webAddress
        #webpg    = urllib2.urlopen(diagPage)
        webpg    = urlopen(diagPage)
        data     = []

        #-----------------------------
        # Open page with Beautifulsoup
        #-----------------------------
        soup = bs(webpg)

        print (soup)

        #--------------
        # Extract Table
        #--------------
        table = soup.find('table')

        print (table)

        #---------
        # Get rows
        #---------
        rows = table.find_all('tr')

        print (rows)


        exit()

        for i, s in enumerate(soup):
           
            rows  = s.split('\n')

        for i, r in enumerate(rows):

            if i >=2:

                r = r.strip().split(':')
                cols = [element.strip() for element in r]
                data.append([element for element in cols if element])

        #---------------------------
        # Add elements to dictionary
        #---------------------------

        for row in data:
            try:
                self.data["ATM_"+('_').join(row[0].upper().split())] = row[1].upper()
            except:
                continue

if __name__ == "__main__":

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    #try:
    #    ctlFile  = sys.argv[1]
    #except:
    #    ctlFile  = "C:/bin/ops/FL0_Defaults.input"
    #    print('ctlFile not provided as input, trying to use C:/bin/ops/FL0_Defaults.input')
        #exit()

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
    # Initialize EWS parser object
    #-----------------------------
    # radData = RadwebParser(WebPageParse_IP=ctlFvars["CLD_URL"],TCP_IP_in=ctlFvars["FTS_DataServ_IP"],
    #                         TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))
     
    # radData.parseDiagnostics()
    # exit()
    #-----------------------------
    # Initialize EWS parser object - FL0
    #-----------------------------
    metData = MetwebParser(WebPageParse_IP=ctlFvars["FL0_URL"],TCP_IP_in=ctlFvars["FTS_DataServ_IP"],
                            TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))
    
    # MESA LAB
    #metData = MetwebParser(WebPageParse_IP=ctlFvars["ML_URL"],TCP_IP_in=ctlFvars["FTS_DataServ_IP"],
    #                        TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))

     #-----------------------------
    # Initialize EWS parser object - CU SKYWATCH (IN PROGRESS)
    #-----------------------------
    #metData = MetwebParser(WebPageParse_IP=ctlFvars["CU_MET"],TCP_IP_in=ctlFvars["FTS_DataServ_IP"],
    #                        TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))

    #metData.parseCUDiagnostics()

    #exit()
     

    #---------------------------------
    # Initialize APC UPS parser object
    #---------------------------------
    #apcData = APCwebParser(WebPageParse_IP=ctlFvars["UPS_IP"],TCP_IP_in=ctlFvars["FTS_DataServ_IP"],
    #                        TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))

    #-----------------------------------------
    # Start indefinite loop to update TCP data
    # server with Bruker EWS information
    #-----------------------------------------
    while True:

    

        #------------------
        # Parse diagnostics
        #------------------
        try:
            metData.parseDiagnostics()
            print ("\nSuccessfully obtained Met data at........{}".format(dt.datetime.now(dt.timezone.utc)))
        except:
            print ("Unable to parse Met page!")

        #------------------------
        # Send data to TCP server
        #------------------------
        try:
            metData.sendData()
        except:
            print ("Unable to send data from web parser program to TCP data server!")

        #--------------------------
        # Hold for updated interval
        #--------------------------
        sleep(int(ctlFvars["FL0_UpdateInt"]))
