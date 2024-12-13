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

        
        
if __name__ == "__main__":


    ctlFile  = "C:/bin/ops/FL0_Defaults.input"

    ctlFvars = mainInputParse(ctlFile)

    msg = MIMEText("----------------------------Measurement DATA------------------------\n\n"                            + \
                   "Filename            = Test - 3")
    
    msg['From']   = ctlFvars['Email_from']
    msg['To']     = ctlFvars['Email_to'] 
    msg['Subject']= "Test - FL0 email"           

    toemails   = [onemail for onemail in ctlFvars["Email_to"].strip().split(",")]

    print toemails

    #s = smtplib.SMTP('localhost')
    s = smtplib.SMTP(ctlFvars['Local_Server'], int(ctlFvars['Local_port']))
    s.sendmail(msg['From'], toemails, msg.as_string())
    s.quit()                   
    