#----------------------------------------------------------------------------------------
# Name:
#       ModUtils.py
#
# Purpose:
#       This is a collection for common modules
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

import logging
import os
import psutil
import sys
import numpy                as     np
import datetime             as     dt
from email.mime.text       import MIMEText
from email.mime.image      import MIMEImage
from email.mime.multipart  import MIMEMultipart
import smtplib
from   subprocess           import Popen, PIPE



    #------------------#
    # Define functions #
    #------------------#

def ckDir(dirName,logFlg=False,exit=False):
    ''' '''
    if not os.path.exists( dirName ):
        print ('Input Directory %s does not exist' % (dirName))
        if logFlg: logFlg.error('Directory %s does not exist' % dirName)
        if exit: sys.exit()
        return False
    else:
        return True 
    
def find_nearestInd(array,value):
    return (np.abs(array-value)).argmin()

def ckFile(fName,logFlg=False,exitFlg=False):
    '''Check if a file exists'''
    if not os.path.isfile(fName):
        print ('File %s does not exist' % (fName))
        if logFlg: logFlg.error('Unable to find file: %s' % fName)
        if exitFlg: sys.exit()
        return False
    else:
        return True  

def ckDirMk(dirName,logFlg=False):
    ''' '''
    if not ( os.path.exists(dirName) ):

        try: os.makedirs( dirName )
        except: pass 

        if logFlg: logFlg.info( 'Created folder %s' % dirName)  
        return False
    else:
        return True

def smtpEmail(body_msg,from_msg,to_msg,subj_msg):
    ''' Function to send email via SMTP '''
    msg            = MIMEText(body_msg)
    msg['From']    = from_msg
    msg['To']      = to_msg
    msg['Subject'] = subj_msg

    s = smtplib.SMTP("localhost")
    s.sendmail(from_msg,to_msg,msg.as_string())
    s.quit()

def sendEmail(body_msg, subj_msg, ctlFvars ):

    msg            = MIMEText(body_msg)
    msg['From']    = ctlFvars['Email_from']
    msg['Subject'] = subj_msg

    s = smtplib.SMTP(ctlFvars['Local_Server'], int(ctlFvars['Local_port']))    

    toemails   = [onemail for onemail in ctlFvars["Email_to"].strip().split(",")]

    msg['To']     = ctlFvars['Email_to']

    s.sendmail(ctlFvars['Email_from'], toemails, msg.as_string())
    s.quit() 


def killProcess(pName):
    for process in psutil.process_iter():
        if pName in process.name:
            print ('Process: {}, found. Terminating it.'.format(process.name))
            process.terminate()
            return True
        else:
            print ('Process: {}, NOT found. No action taken'.format(pName))
            return False
    
def getCrntDateStr():
    #--------------------------
    # Get current date and time
    #--------------------------
    crntTime = dt.datetime.utcnow()
    yrstr    = "{0:04d}".format(crntTime.year)
    mnthstr  = "{0:02d}".format(crntTime.month)
    daystr   = "{0:02d}".format(crntTime.day)  
    datestr  = yrstr + mnthstr + daystr                

    return datestr    
    
def startProc( fname, logFlg=False ):
    '''This runs a system command and directs the stdout and stderr'''
    rtn = psutil.Popen( fname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    
    try:
        stdout, stderr = rtn.communicate(timeout=30)

    except TimeoutExpired:
        print ('Process: {}, has timed out...killing process...'.format(fname))
        rtn.kill()
        return False

    if logFlg: 
        logFlg.info(stdout)
        logFlg.error(stderr)

    return (stdout,stderr,rtn)    

def findProcess(pName):
    pList = []
    for process in psutil.process_iter():
        if pName in process.name:
            print ('Process: {}, found.'.format(process.name))
            pList.append(process.name)

    if pList: return pList
    else:     return False
    
def sortDict(DataDict,keyval):
    ''' Sort all values of dictionary based on values of one key'''
    base = DataDict[keyval]
    for k in DataDict:
        DataDict[k] = [y for (x,y) in sorted(zip(base,DataDict[k]))]
    return DataDict    

def detSignChange(data):
    ''' Determine the number and of sign changes in numpy array'''
    dataSigns     = np.sign(data)  
    dataSigns     = np.delete(dataSigns,np.where(dataSigns==0)[0])
    num_crossings = len(dataSigns)

    return num_crossings

    
    
    
def ctlFileInit(fname,logF=False):
    ''' Open and read control file for site
    '''

    ckFile(fname, logFlg=logF, exitFlg=True)
    ctlFile = {}


    try:
        execfile(fname, ctlFile)
    except IOError as errmsg:
        print (errmsg)
        sys.exit()

    if '__builtins__' in ctlFile:
        del ctlFile['__builtins__']   
        
    return ctlFile

def mainInputParse(fname):
    
    ckFile(fname,exitFlg=True)
    data = {}
    
    #-------------------------------------
    # Add path and file name of input file
    #-------------------------------------
    data["InputFname"] = fname
    
    with open(fname,'r') as fopen: lines = fopen.readlines()
    
    for line in lines:
        
        line = line.strip()
        
        #------------------------------
        # Handle complete line comments
        #------------------------------
        if line.startswith("#"): continue
        
        if "#" in line: line = line.partition("#")[0]    # For comments embedded in lines "#"
        if "!" in line: line = line.partition("!")[0]    # For comments embedded in lines "!"
        
        #-------------------
        # Handle empty lines
        #-------------------
        if len(line) == 0: continue
    
        #--------------------------
        # Populate input dictionary
        #--------------------------
        lhs,_,rhs = line.partition('=')
        lhs       = lhs.strip()
        rhs       = rhs.strip()
    
        data[lhs] = rhs
        
    return data

def logInit(ctlFile):
    ''' Initialize log file
    '''
    #------------------------------------
    # Start log information for this pull
    #------------------------------------
    logF = logging.getLogger('1')
    logF.setLevel(logging.DEBUG)
    hdlr1   = logging.FileHandler(ctlFile['logFile'], mode='a+')
    fmt1    = logging.Formatter('%(asctime)s %(levelname)-4s -- %(message)s','%a, %d %b %Y %H:%M:%S')
    hdlr1.setFormatter(fmt1)
    logF.addHandler(hdlr1)  
    logF.info('**************** Starting New Logging Session ***********************')
        
    return logF


if __name__ == "__main__":
    lat  = 76.52
    lon  = 291.23
    elev = 225.0
    crntD = dt.datetime.utcnow()
    (t1,t2,t3) = sunAzEl(lat, lon, elev,dateT=crntD,surfP=None,surfT=None,vecFlg=True)
    t5 = 1
    
