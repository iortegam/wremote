import datetime as dt
import numpy    as np
from scipy import interpolate
import sys
import os
import time
from itertools import islice

if "C:\\bin" not in sys.path:
    sys.path.append("C:\\bin")

from trackerUtils     import *


#
# ps -fA | grep python
# kill -9 6702
#

def toYearFraction(dates):
    ''' Convert datetime to year and fraction of year'''

    #def sinceEpoch(date): # returns seconds since epoch
        #return time.mktime(date.timetuple())
    #s = sinceEpoch
    ep_fnc = lambda x: time.mktime(x.timetuple())
    
    retrnDates = np.zeros(len(dates))
    
    for i,sngDate in enumerate(dates):
        year = sngDate.year
        startOfThisYear = dt.datetime(year=year, month=1, day=1)
        startOfNextYear = dt.datetime(year=year+1, month=1, day=1)
    
        yearElapsed = ep_fnc(sngDate) - ep_fnc(startOfThisYear)
        yearDuration = ep_fnc(startOfNextYear) - ep_fnc(startOfThisYear)
        fraction = yearElapsed/yearDuration
        retrnDates[i] = sngDate.year + fraction


    return retrnDates

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

#-------------------------------------------
# ***** Read Measurement log ******
#-------------------------------------------
def readMeas(file):

    baseDataDir = 'X:\\id\\fl0\\'

    now            = dt.datetime.utcnow()
    yrstr          = "{0:04d}".format(now.year)
    daystr         = "{0:02d}".format(now.day)
    mnthstr        = "{0:02d}".format(now.month)
    datestr        = yrstr + mnthstr + daystr

    crntDataDir    = baseDataDir + datestr + "\\"    

    fname          = crntDataDir + 'Measurement.log'

    if not ckFile(fname,exitFlg=False): 
        return False

    logMeas = {}

    #-------------------
    # Open and read file
    #-------------------
    with open(fname,"r") as fopen: lines = fopen.readlines()

    hdrs   = ['Measurement_Time', 'Filename', 'SNR_RMS', 'Peak_Amplitude', 'Pre_Amp_Gain', 'Signal_Gain']#, 'Ext_E_Rad', 'Ext_E_RadS', 'Ext_W_Rad', 'Ext_E_Rads']
     
    #-------------------------
    # Choose variables to plot
    #-------------------------
    ii    = []
    idVal = []
    for i,v in enumerate(hdrs):
        ii.append(ii)
        idVal.append(v)      

    #----------------------
    # Read in date and time
    #----------------------
    logMeas['DT_Meas'] = [dt.datetime(int(yrstr),int(mnthstr),int(daystr),
                                int(line[0:2]),int(line[3:5]),int(line[6:8])) for line in lines[1:-2] ]

    if len(logMeas['DT_Meas']) >= 1: MeasFlg = True

    for i, v in enumerate(idVal):
        try:
            logMeas.setdefault(v,[]).append(np.asarray([float(line.strip().split()[i]) for line in lines[1:-2] ]) )
        except:
            logMeas.setdefault(v,[]).append(np.asarray([line.strip().split()[i] for line in lines[1:-2] ]) )

    return logMeas

def readMeasUpdate(logMeas):

    baseDataDir = 'X:\\id\\fl0\\'

    now            = dt.datetime.utcnow()
    yrstr          = "{0:04d}".format(now.year)
    daystr         = "{0:02d}".format(now.day)
    mnthstr        = "{0:02d}".format(now.month)
    datestr        = yrstr + mnthstr + daystr     

    crntDataDir    = baseDataDir + datestr + "\\"    

    fname          = crntDataDir + 'Measurement.log'

    if not ckFile(fname,exitFlg=False): 
        return False

    with open(fname,"r") as fopen: lines = fopen.readlines()

    hdrs   = ['Measurement_Time', 'Filename', 'SNR_RMS', 'Peak_Amplitude', 'Pre_Amp_Gain', 'Signal_Gain']#, 'Ext_E_Rad', 'Ext_E_RadS', 'Ext_W_Rad', 'Ext_E_Rads']
         
    #-------------------------
    # Choose variables to plot
    #-------------------------
    ii    = []
    idVal = []
    for i,v in enumerate(hdrs):
        ii.append(ii)
        idVal.append(v)     
    #----------------------
    # Read in date and time
    #----------------------
    logMeas['DT_Meas'].append( dt.datetime(int(yrstr),int(mnthstr),int(daystr),
                                int(lines[-1][0:2]),int(lines[-1][3:5]),int(lines[-1][6:8]))) 

    for i, v in enumerate(idVal):
        try:
            logMeas.setdefault(v,[]).append(float(lines[-1].strip().split()))
        except:
            logMeas.setdefault(v,[]).append(lines[-1].strip().split())

    for i, v in enumerate(idVal):
        logMeas[v] = logMeas[v][0]

    return logMeas


#-------------------------------------------
# ***** Read Measurement log ******
#-------------------------------------------
# def readHK(file):

#     #self.date  = str(iyear) + str(imnth) + str(iday) 

#     now            = dt.datetime.now()
#     iyear          = "{0:04d}".format(now.year)
#     iday           = "{0:02d}".format(now.day)
#     imnth          = "{0:02d}".format(now.month)

#     fname ='house.log'
    

#     logHK   = {}

#     #-------------------
#     # Open and read file
#     #-------------------
#     with open(fname,"r") as fopen: lines = fopen.readlines()
    
#     #---------------
#     # Read in Header
#     #---------------
#     for line in lines:
#         if line.strip().startswith("#$"):
#             hdrs = [ val for val in line.strip().split()[3:]]

     
#     #-------------------------
#     # Choose variables to plot
#     #-------------------------
#     ii    = []
#     idVal = []
#     for i,v in enumerate(hdrs):
#         ii.append(ii)
#         idVal.append(v)

#     #----------------------
#     # Read in date and time
#     #----------------------
#     obsTime = [dt.datetime(int(line[0:4]),int(line[4:6]),int(line[6:8]),
#                                 int(line[9:11]),int(line[12:14]),int(line[15:17])) for line in lines[:-2] if (not line.startswith("#"))]

#     for i, v in enumerate(idVal):
#         #----------------------
#         # FOR NOW READ ONLY < 15 INDEX
#         #----------------------
#         try:
#             logHK.setdefault(v,[]).append(np.array([float(line.strip().split()[i+2]) for line in lines[:-2] if not line.startswith("#")]))
#         except ValueError:
#             logHK.setdefault(v,[]).append(np.array([line.strip().split()[i+2] for line in lines[:-2] if not line.startswith("#")]))
    
#     hkFlg  = True  
            
#     return logHK, obsTime

    #-------------------------------------------
    # ***** Read Measurement log ******
    #-------------------------------------------

def readHK(file):

    #self.date  = str(iyear) + str(imnth) + str(iday) 

    now            = dt.datetime.now()
    iyear          = "{0:04d}".format(now.year)
    iday           = "{0:02d}".format(now.day)
    imnth          = "{0:02d}".format(now.month)

    fname ='house.log'
    

    logHK   = {}

    with open(fname,"r") as f: lines = f.readlines()

    #---------------
    # Read in Header
    #---------------
    for i in range(200):
        if lines[i].strip().startswith("#$"):
            hdrs = [ val for val in lines[i].strip().split()[3:]]

    #-------------------------
    # Choose variables to plot
    #-------------------------
    ii    = []
    idVal = []
    for i,v in enumerate(hdrs):
        ii.append(ii)
        idVal.append(v)

    #-------------------
    # Open and read file
    #-------------------
    step = 1000

    obsTime = []
    
    with open(fname,"r") as fopen:

        for lineno, line in enumerate(fopen):
            if lineno % step == 0:
                #print(line)

                obsTime.append(dt.datetime(int(line[0:4]),int(line[4:6]),int(line[6:8]),
                                int(line[9:11]),int(line[12:14]),int(line[15:17])) for line in lines[:-2] if (not line.startswith("#")))

                for i, v in enumerate(idVal):
                #----------------------
                # FOR NOW READ ONLY < 15 INDEX
                #----------------------
                    try:
                        logHK.setdefault(v,[]).append(np.array([float(line.strip().split()[i+2]) for line in lines[:-2] if not line.startswith("#")]))
                    except ValueError:
                        logHK.setdefault(v,[]).append(np.array([line.strip().split()[i+2] for line in lines[:-2] if not line.startswith("#")]))
    
    hkFlg  = True  
            
    return logHK, obsTime

# def readHK(file):

#     #self.date  = str(iyear) + str(imnth) + str(iday) 

#     now            = dt.datetime.now()
#     iyear          = "{0:04d}".format(now.year)
#     iday           = "{0:02d}".format(now.day)
#     imnth          = "{0:02d}".format(now.month)

#     fname ='house.log'
    

#     logHK   = {}

#     #-------------------
#     # Open and read file
#     #-------------------
#     with open(fname,"r") as fopen: lines = fopen.readlines()

#     lastline = lines[-2]
    
#     #---------------
#     # Read in Header
#     #---------------
#     for line in lines:
#         if line.strip().startswith("#$"):
#             hdrs = [ val for val in line.strip().split()[3:]]

     
#     #-------------------------
#     # Choose variables to plot
#     #-------------------------
#     ii    = []
#     idVal = []
#     for i,v in enumerate(hdrs):
#         ii.append(ii)
#         idVal.append(v)

#     obsTime = []

#     #----------------------
#     # Read in date and time
#     #----------------------
#     obsTime.append(dt.datetime(int(lastline[0:4]),int(lastline[4:6]),int(lastline[6:8]),
#                                 int(lastline[9:11]),int(lastline[12:14]),int(lastline[15:17])))

#     for i, v in enumerate(idVal):
#         #----------------------
#         # FOR NOW READ ONLY < 15 INDEX
#         #----------------------
#         try:
#             logHK.setdefault(v,[]).append(float(lastline.strip().split()[i+2]))
#         except ValueError:
#             logHK.setdefault(v,[]).append(lastline.strip().split()[i+2])
    
#     hkFlg  = True  
            
#     return logHK, obsTime


#-------------------------------------------
# ***** Read Measurement log ******
#-------------------------------------------
# def readMet(file):

#     now            = dt.datetime.now()
#     iyear          = "{0:04d}".format(now.year)
#     iday           = "{0:02d}".format(now.day)
#     imnth          = "{0:02d}".format(now.month)


#     if dt.date(int(iyear), int(imnth), int(iday) ) >= dt.date(2019,05,05):

#         #try:
#         fname2 = 'houseMet.log'

#         logMet   = {}

#         with open(fname2,"r") as fopen: lines = fopen.readlines()
        
        
#         hdrs = [ val for val in lines[0].strip().split()[2:]]
        
#         #-------------------------
#         # Choose variables to plot
#         #-------------------------
#         ii    = []
#         idValMet = []
#         for i,v in enumerate(hdrs):
#             ii.append(ii)
#             idValMet.append(v)
#             #print "{0:4}= {1:}".format(i,v)
       
#         obsTime = [dt.datetime(int(line[0:4]),int(line[4:6]),int(line[6:8]),
#                             int(line[13:15]),int(line[16:18]),int(line[19:21])) for line in lines[1:-2] if (not line.startswith("#"))]

#         for i, v in enumerate(idValMet):
#             try:
#                 logMet.setdefault(v,[]).append(np.array([float(line.strip().split()[i+2]) for line in lines[1:-2] if not line.startswith("#")]))
#                 #self.vars[v] = np.interp(self.obsTime, self.obsTime2, np.asarray(self.vars[v]) )
#             except ValueError:
#                 #print v
#                 logMet.setdefault(v,[]).append(np.array([line.strip().split()[i+2] for line in lines[1:-2] if not line.startswith("#")]))


#         flgMet = True


#         return logMet, obsTime

def readMet(file):

    now            = dt.datetime.now()
    iyear          = "{0:04d}".format(now.year)
    iday           = "{0:02d}".format(now.day)
    imnth          = "{0:02d}".format(now.month)


    if dt.date(int(iyear), int(imnth), int(iday) ) >= dt.date(2019,05,05):

        #try:
        fname2 = 'houseMet.log'

        logMet   = {}

        with open(fname2,"r") as fopen: lines = fopen.readlines()

        lastline = lines[-2]
        
        
        hdrs = [ val for val in lines[0].strip().split()[2:]]
        
        #-------------------------
        # Choose variables to plot
        #-------------------------
        ii    = []
        idValMet = []
        for i,v in enumerate(hdrs):
            ii.append(ii)
            idValMet.append(v)
            #print "{0:4}= {1:}".format(i,v)

        obsTime = []
       
        obsTime.append(dt.datetime(int(lastline[0:4]),int(lastline[4:6]),int(lastline[6:8]),
                            int(lastline[13:15]),int(lastline[16:18]),int(lastline[19:21])))

        for i, v in enumerate(idValMet):
            try:
                logMet.setdefault(v,[]).append(float(lastline.strip().split()[i+2]))
                #self.vars[v] = np.interp(self.obsTime, self.obsTime2, np.asarray(self.vars[v]) )
            except ValueError:
                #print v
                logMet.setdefault(v,[]).append(lastline.strip().split()[i+2])


        flgMet = True


        return logMet, obsTime

def readHKUpdate(logHK, obsTime):

    #self.date  = str(iyear) + str(imnth) + str(iday) 

    now            = dt.datetime.now()
    iyear          = "{0:04d}".format(now.year)
    iday           = "{0:02d}".format(now.day)
    imnth          = "{0:02d}".format(now.month)

    fname ='house.log'
    

    #-------------------
    # Open and read file
    #-------------------
    with open(fname,"r") as fopen: lines = fopen.readlines()

    lastline = lines[-2]
    
    #---------------
    # Read in Header
    #---------------
    for line in lines:
        if line.strip().startswith("#$"):
            hdrs = [ val for val in line.strip().split()[3:]]

    #-------------------------
    # Choose variables to plot
    #-------------------------
    ii    = []
    idVal = []
    for i,v in enumerate(hdrs):
        ii.append(ii)
        idVal.append(v)

    #----------------------
    # Read in date and time
    #----------------------
    obsTime.append(dt.datetime(int(lastline[0:4]),int(lastline[4:6]),int(lastline[6:8]),
                                int(lastline[9:11]),int(lastline[12:14]),int(lastline[15:17])))

    for i, v in enumerate(idVal):
        #----------------------
        # FOR NOW READ ONLY < 15 INDEX
        #----------------------
        try:
            logHK.setdefault(v,[]).append(float(lastline.strip().split()[i+2]))
        except ValueError:
            logHK.setdefault(v,[]).append(lastline.strip().split()[i+2])
    
    hkFlg  = True  
            

    return logHK, obsTime

def readMetUpdate(logMet, obsTime):

    now            = dt.datetime.now()
    iyear          = "{0:04d}".format(now.year)
    iday           = "{0:02d}".format(now.day)
    imnth          = "{0:02d}".format(now.month)



    if dt.date(int(iyear), int(imnth), int(iday) ) >= dt.date(2019,05,05):

        #try:
        fname2 = 'houseMet.log'

        with open(fname2,"r") as fopen: lines = fopen.readlines()

        lastline = lines[-2]
        
     
        hdrs = [ val for val in lines[0].strip().split()[2:]]
        
        #-------------------------
        # Choose variables to plot
        #-------------------------
        ii    = []
        idValMet = []
        for i,v in enumerate(hdrs):
            ii.append(ii)
            idValMet.append(v)
           
        obsTime.append(dt.datetime(int(lastline[0:4]),int(lastline[4:6]),int(lastline[6:8]),
                            int(lastline[13:15]),int(lastline[16:18]),int(lastline[19:21])))

        for i, v in enumerate(idValMet):
            try:
                logMet.setdefault(v,[]).append(float(lastline.strip().split()[i+2]))
                #self.vars[v] = np.interp(self.obsTime, self.obsTime2, np.asarray(self.vars[v]) )
            except ValueError:
                #print v
                logMet.setdefault(v,[]).append(lastline.strip().split()[i+2])


    return logMet, obsTime
