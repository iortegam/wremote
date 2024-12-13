#----------------------------------------------------------------------------------------
# Name:
#        trackerUtils.py
#
# Purpose:
#       This is a collection for Community Solar Tracker
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
import ephem                as     ep
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

    
def sunAzEl(lat, lon, elev,dateT=None,surfP=None,surfT=None,vecFlg=False):
    ''' Routine for calculating Ephimeris data '''
    
    #--------------------------------------------------------------
    # Set conditions for observer
    # -- lat    = Latitude (+N)
    # -- lon    = Longitude (+E)
    # -- elv    = Elevation (m)
    # -- surfT  = Surface Temperature (Deg C) - Default = 25 DegC
    # -- surfP  = Surface Pressure (mBar)     - Default = 1010 mBar
    # -- dateT  = date and time (datetime class)
    #--------------------------------------------------------------
    loc           = ep.Observer()
    loc.lat       = str(lat)
    loc.lon       = str(lon)
    loc.elevation = elev
    if surfT:  loc.temp     = surfT
    if surfP:  loc.pressure = surfP
    else:      loc.compute_pressure()
    if dateT:  loc.date     = dateT

    #---------------------------------------
    # Find Elevation and Azimuth of Sun
    # -- Elevation is Positive above horizon
    # -- Azimuth is East of North
    #---------------------------------------
    if not vecFlg:
        sun = ep.Sun(loc)
    
        sunAz = sun.az  * 180.0 / np.pi
        sunEl = sun.alt * 180.0 / np.pi
        
        #---------------------------------------------
        # PyEphem defines Azimuth East of North
        # Our coordinate system is West of South
        # Convert....
        # 0 <= SunAz < 180    => SunAz = SunAz + 180.0
        # 180 <= SunAz <= 360 => SunAz = SunAz - 180.0
        #---------------------------------------------
        #if (sunAz >= 0) and (sunAz < 180): sunAz += 180.0
        #else:                              sunAz -= 180.0        
        
    else:
        if not dateT:  dateT = dt.datetime.utcnow()
       
        deltaT = 60
 
        #-----------------------------------
        # Create list of minutes for the day
        #-----------------------------------
        crntDay  = dt.datetime(dateT.year,dateT.month,dateT.day)
        times    = np.array([crntDay + dt.timedelta(seconds = (i*int(deltaT))) for i in range(0,86400/int(deltaT))])
        #timesrtn = np.array([dt.timedelta(seconds = (i*int(deltaT))) for i in range(0,86400/int(deltaT))])
        timesrtn = np.array([float(i*int(deltaT)) for i in range(0,86400/int(deltaT))])
    
        #---------------------------------------------
        # Find Elevation and Azimuth Velocities of Sun
        # -- Elevation is Positive above horizon
        # -- Azimuth is East of North
        #---------------------------------------------
        sunAz = np.zeros(np.size(times))
        sunEl = np.zeros(np.size(times))
        
        for i in range(0,np.size(times)):
            loc.date = times[i]
            
            sun      = ep.Sun(loc)
            sunAz[i] = sun.az  * 180.0 / np.pi
            sunEl[i] = sun.alt * 180.0 / np.pi
        
            #---------------------------------------------
            # PyEphem defines Azimuth East of North
            # Our coordinate system is West of South
            # Convert....
            # 0 <= SunAz < 180    => SunAz = SunAz + 180.0
            # 180 <= SunAz <= 360 => SunAz = SunAz - 180.0
            #---------------------------------------------
            #if (sunAz[i] >= 0) and (sunAz[i] < 180): sunAz[i] += 180.0
            #else:                                    sunAz[i] -= 180.0
    
    if not vecFlg:
        return (sunAz,sunEl)
    else:
        return (sunAz,sunEl,timesrtn)

def sunAzElVel(lat, lon, elev,dateT=None,deltaT=60,surfP=None,surfT=None):
    ''' Routine for calculating Ephimeris velocity vector for a day'''
    
    #-----------------------------------------------------------------
    # Set conditions for observer
    # -- lat    = Latitude (+N)
    # -- lon    = Longitude (+E)
    # -- elv    = Elevation (m)
    # -- surfT  = Surface Temperature (Deg C) - Default = 25 DegC
    # -- surfP  = Surface Pressure (mBar)     - Default = 1010 mBar
    # -- dateT  = date and time (datetime class)
    # -- deltaT = Time interval to calculate angular velocities
    #-----------------------------------------------------------------
    loc1           = ep.Observer()
    loc1.lat       = str(lat)
    loc1.lon       = str(lon)
    loc1.elevation = elev
    if surfT:  loc1.temp     = surfT
    if surfP:  loc1.pressure = surfP
    else:      loc1.compute_pressure()
    
    loc2           = ep.Observer()
    loc2.lat       = str(lat)
    loc2.lon       = str(lon)
    loc2.elevation = elev
    if surfT:  loc2.temp     = surfT
    if surfP:  loc2.pressure = surfP
    else:      loc2.compute_pressure()    
    
    
    if not dateT:  dateT = dt.datetime.utcnow()
    
    crntDay = dt.datetime(dateT.year,dateT.month,dateT.day)
    times   = np.array([crntDay + dt.timedelta(seconds = (i*int(deltaT))) for i in range(0,86400/int(deltaT))])

    #---------------------------------------------
    # Find Elevation and Azimuth Velocities of Sun
    # -- Elevation is Positive above horizon
    # -- Azimuth is East of North
    #---------------------------------------------
    sunAzVel = np.zeros(np.size(times[:-1]))
    sunElVel = np.zeros(np.size(times[:-1]))
    
    for i in range(0,np.size(times[:-1])):
        loc1.date = times[i]
        loc2.date = times[i+1]
        
        sun1   = ep.Sun(loc1)
        sun2   = ep.Sun(loc2)
        sunAz1 = sun1.az  * 180.0 / np.pi
        sunEl1 = sun1.alt * 180.0 / np.pi
        sunAz2 = sun2.az  * 180.0 / np.pi
        sunEl2 = sun2.alt * 180.0 / np.pi
        
        if sunAz2 < sunAz1: sunAz2 += 360.0
    
        sunAzVel[i] = (sunAz2 - sunAz1) / deltaT  # Degrees second^-1
        sunElVel[i] = (sunEl1 - sunEl2) / deltaT  # Degrees second^-1

    times = np.delete(times,-1)
    
    return (sunAzVel,sunElVel,times)

def cartesian(arrays, out=None):
    """
    Generate a cartesian product of input arrays.

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])

    """

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = n / arrays[0].size
    out[:,0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m,1:])
        for j in xrange(1, arrays[0].size):
            out[j*m:(j+1)*m,1:] = out[0:m,1:]
    return out
    
    
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
        #rhs       = rhs.replace(" ", "").strip()
    
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
    
