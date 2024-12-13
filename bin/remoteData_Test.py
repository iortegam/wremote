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

 
class EmailClass(object):
    
    def __init__(self):

        #-----------------------------------
        # Configuration parameters of server
        #-----------------------------------        
        self.ctlFvars        = {}

        
    def getTS(self,crntTime):
        
        return "{0:%Y%m%d.%H%M%S}".format(crntTime)
                   
    def TestEmail(self):
    
        msgLst = []
        
        msg = ";".join(msgLst)
        
        
        Email_to = 'iortega@ucar.edu,ivan.ortega@colorado.edu'
        
        toemails = [onemail for onemail in Email_to.strip().split(",")]
                            
        #----------------------------------
        # Send email with Measurement Stats
        #----------------------------------
        #toemails = [onemail for onemail in self.ctlFvars["Email_to"].strip().split(",")]
                            
        msg = MIMEText("_________________________Measurement__DATA_______________________________\n\n" + \
                       "Filename         = {1:}\nSNR              = {2:}\nMeasurement time = {0:}\n".format(1,2,3,) )
                        
        msg['Subject']= "Testing: Sucessful Measurement taken at MLO at ????"
        msg['From']   = 'FTIR@mlo'
        msg['To']     = 'iortega@ucar.edu, ivan.ortega@colorado.edu'            
                        
        s = smtplib.SMTP('localhost')
        s.sendmail(msg['From'], toemails, msg.as_string())
        s.quit()                                
                            
                        
if __name__ == "__main__":
    
    #-----------
    # Run Server
    #-----------
    server1 = EmailClass()
    server1.TestEmail()
