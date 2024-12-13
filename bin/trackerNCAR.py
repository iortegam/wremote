#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        trackerNCAR.py
#
# Purpose:
#       
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


#---------------
# Import modules
#---------------
import traceback
import serial
import os
import math
import sys
import copy
import datetime       as     dt
from   time           import sleep
from   trackerUtils   import *
from   usbCam         import SunCam
from   controllerCST  import TrackerCntrl
from   scipy          import optimize
from   remoteData     import FTIRdataClient


                        #-------------------------#
                        # Define helper functions #
                        #-------------------------#
def usage():
    ''' Prints to screen standard program usage'''
    print 'trackerNCAR.py <tracker ctl file>'


                                #-------------------#
                                # Class Definitions #
                                #-------------------#

class TrackerNCAR(SunCam,TrackerCntrl,FTIRdataClient):
    ''' This class controlls the movement of the NCAR solar tracker. It is designed to 
        communicate with the Newport ESP301 motion controller
    '''

    def __init__(self, ctlFname,TCPflg=False):
        '''
        '''
        self.AzOffSet = None
        self.ElOffSet = None       
        self.TCPflg   = TCPflg

        #----------------
        # Read Cntrl File
        #----------------
        ckFile(ctlFname,exitFlg=True)
        ctlFile      = ctlFileInit(ctlFname)
        self.dataDir = ctlFile["baseDataDir"]
            
        #--------------------------
        # Initialize parent classes
        #--------------------------
        SunCam.__init__(self,ctlFile,TCPflg=TCPflg)
        TrackerCntrl.__init__(self,ctlFile,TCPflg=TCPflg)
        FTIRdataClient.__init__(self,TCP_IP=self.ctlFile["FTS_DataServ_IP"],
                                TCP_Port=self.ctlFile["FTS_DataServ_PORT"],BufferSize=self.ctlFile["FTS_DATASERV_BSIZE"])
   
    def opt_f(self,x):
        ''' Define optimization function for moving sun 
            x[0] - elevation axis
            x[1] - azimuth axis   '''
        
        #-----------------------------
        # Move tracker to new position
        #-----------------------------
        self.pointTracker(x[1],x[0])

        #--------------------------------------------
        # Find the length of vector between center of
        # Sun and center of CCD or aperature
        #-----------------------------------------------
        # Take N number of images to find smooth average
        #-----------------------------------------------
        rtnDist = np.zeros(10)
        for i in range(0,10):
            rtnDist[i] = self.findEllipse(aptFlg=self.aptFlg)
        
        return np.mean(rtnDist)
    
    def getTempPress(self,surfPressDefault,surfTempDefault):

        press = self.getParam("PRESSURE")
        temp  = self.getParam("TEMPERATURE")
        
        if press: press = float(press)
        if temp:  temp  = float(temp)
        
        if not press:              surfPres = surfPressDefault
        elif not (press < -900.0): surfPres = press
        else:                      surfPres = surfPressDefault
        
        if not temp:               surfTemp = surfTempDefault
        elif not (temp <  -900.0): surfTemp = temp
        else:                      surfTemp = surfTempDefault
        
        return (surfPres,surfTemp)
    
    def logTransform(self,calTime):
        #----------------------------------
        # Logging the transformation matrix
        #---------------------------------- 
        datestr     = getCrntDateStr()        
        crntDataDir = self.dataDir + datestr + "/"
        logF        = crntDataDir + "TransformMat.log"
    
        #-----------------------------------------
        # Write to Measurement summary log file. 
        # Check if Measurement summary file exists
        #-----------------------------------------
        if ckDir(crntDataDir):
            if not ckFile(logF):
                with open(logF,'w') as fopen:
                    fopen.write("{0:20s} {1:20s} {2:20s} {3:20s} {4:20s}\n".format("Time Stamp","X[0,0]","X[0,1]","X[1,0]","X[1,1]"))
            else:
                with open(logF,'a') as fopen:
                    fopen.write("{0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20}\n".format(calTime,self.transform[0][0],self.transform[0][1],self.transform[1][0],self.transform[1][1]))      
    
        #---------------------------------------------
        # Temprorary Store last instance in TCP server
        #---------------------------------------------
        #if self.TCPflg:
            #mssg = "LASTCALMAT {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20}\n".format(calTime,self.transform[0][0],self.transform[0][1],self.transform[1][0],self.transform[1][1])
            #self.setParam(mssg)        
        
    def logRotMat(self,rotAz):
        #----------------------------
        # Logging the rotation matrix
        #---------------------------- 
        datestr     = getCrntDateStr()        
        crntDataDir = self.dataDir + datestr + "/"
        logF        = crntDataDir + "RotMat.log"
        crntTime    = dt.datetime.utcnow()
    
        #-----------------------------------------
        # Write to Measurement summary log file. 
        # Check if Measurement summary file exists
        #-----------------------------------------
        if ckDir(crntDataDir):
            if not ckFile(logF):
                with open(logF,'w') as fopen:
                    fopen.write("{0:20s} {1:20s} {2:20s} {3:20s} {4:20s} {5:20s} {6:20s}\n".format("Time Stamp","X[0,0]","X[0,1]","X[1,0]","X[1,1]","Time of Calib","Delta Az"))
            else:
                with open(logF,'a') as fopen:
                    fopen.write("{0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20} {5:20s} {6:20}\n".format(crntTime,self.transformRot[0][0],self.transformRot[0][1],self.transformRot[1][0],
                                                                                                         self.transformRot[1][1],self.calibrationTime,rotAz))      
    
        #---------------------------------------------
        # Temprorary Store last instance in TCP server
        #---------------------------------------------
        #if self.TCPflg:
            #mssg = "LASTROTMAT {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20} {5:20s} {6:20s}\n".format(crntTime,self.transformRot[0][0],self.transformRot[0][1],self.transformRot[1][0],
                                                                                                         #self.transformRot[1][1],self.calibrationTime,rotAz)
            #self.setParam(mssg)        

    def logSunPix(self,sunCentRef):
        #--------------------------------------------------------------
        # data[1] = Image time stamp
        # data[2] = NOAPT  = Sun reference to center CCD (with offsets)
        #         = YESAPT = Sun reference to center Apterature
        # data[3] = Sun delta X pixels
        # data[4] = Sun delta Y pixels
        # data[5] = Sun Radiance
        # data[6] = Sun Area
        # data[7] = Sqrt(delX**2 + delY**2)
        #-------------------------------------------------------------- 
        datestr     = getCrntDateStr()        
        crntDataDir = self.dataDir + datestr + "/"
        logF        = crntDataDir + "SunPix.log"
                          
        #-----------------------------------------
        # Write to Measurement summary log file. 
        # Check if Measurement summary file exists
        #-----------------------------------------
        if ckDir(crntDataDir):
            if not ckFile(logF):
                with open(logF,'w') as fopen:
                    fopen.write("{0:20s} {1:20s} {2:20s} {3:20s} {4:20s} {5:20s} {6:20s}\n".format("Time Stamp","Sun Center Ref","DeltaX Pixels","DeltaY Pixels","Radiance","Area","Total Distance"))
            else:
                with open(logF,'a') as fopen:
                    fopen.write("{0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20} {5:20} {6:20}\n".format(self.imgTime,sunCentRef,self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.dist))      
                    
        #---------------------------------------------
        # Temprorary Store last instance in TCP server
        #---------------------------------------------
        if self.TCPflg:
            mssg = "TRACKER_SUNPIX {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20} {5:20} {6:20}\n".format(self.imgTime,sunCentRef,self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.dist)
            msg2 = "TRACKER_SUNRAD {0:%Y%m%d.%H%M%S} {1:20}\n".format(self.imgTime,self.sunPixMean/255.0)

            self.setParam(mssg)
            self.setParam(msg2)
                               
    def logSunAngle(self,ephemEl,ephemAz,trackerEl,trackerAz): 
        #----------------------------------
        # data[1] = Time Stamp
        # data[2] = Ephemeris Elevation Angle
        # data[3] = Elevation Angle Offset
        # data[4] = Ephemeris Azimuth Angle
        # data[5] = Azimuth Angle Offset
        #---------------------------------- 
        datestr     = getCrntDateStr()        
        crntDataDir = self.dataDir + datestr + "/"    
        logF        = crntDataDir + "SunAngle.log"
        
        crntT       = dt.datetime.utcnow()    
        
        #----------------------------------------------------
        # Convert tracker coordinates to absolute coordinates
        # Add offsets Tracker is not correctly aligned
        #----------------------------------------------------
        trackerAz = self.tracker_to_abs_Az(trackerAz+self.ctlFile["AzOffSet"])
        trackerEl = self.tracker_to_abs_El(trackerEl+self.ctlFile["ElOffSet"])
        
        #-----------------------------------------
        # Check if Measurement summary file exists
        #-----------------------------------------
        if ckDir(crntDataDir):
            if not ckFile(logF):
                with open(logF,'w') as fopen:
                    fopen.write("{0:20s} {1:20s} {2:20s} {3:20s} {4:20s} \n".format("Time Stamp","Tracker Az Angle","Ephem Az Angle",
                                                                                    "Tracker El Angle","Ephem El Angle"))
        
            else:
                with open(logF,'a') as fopen:
                    fopen.write("{0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20} {4:20}\n".format(crntT,trackerAz,ephemAz,trackerEl,ephemEl))
        
        #---------------------------------------------
        # Temprorary Store last instance in dictionary
        #---------------------------------------------
        if self.TCPflg:
            mssg = "TRACKER_ELEVATION {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20}\n".format(crntT,trackerEl,ephemEl,np.abs(trackerEl-ephemEl)/ephemEl)
            msg2 = "TRACKER_AZIMUTH {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20}\n".format(crntT,trackerAz,ephemAz,np.abs(trackerAz-ephemAz)/ephemAz)
            
            self.setParam(mssg)    
            self.setParam(msg2)
    
    def quitTrackerProgram(self):
        #-----------------
        # shutdown program
        #-----------------
        print "Quiting Tracker program...."
        sys.exit()
    
    def setAccelJerk(self,speed):
        #-------------------------------------------------
        # Set acceleration and deceleration of motors for 
        # centering of Sun. This is relatively fast.
        #-------------------------------------------------
        if speed == "fast": 
            A1 = "FastAccelAxis1"
            J1 = "FastJerkAxis1"
            A2 = "FastAccelAxis2"
            J2 = "FastJerkAxis2"
        if speed == "slow":
            A1 = "SlowAccelAxis1"
            J1 = "SlowJerkAxis1"
            A2 = "SlowAccelAxis2"
            J2 = "SlowJerkAxis2"           
            
        accelVals = self.get_accel()
        if accelVals[0] != self.ctlFile[A1]: 
            self.stop_motion()
            self.set_accel(self.ctlFile[A1],axis=1)
        if accelVals[1] != self.ctlFile[A2]: 
            self.stop_motion()
            self.set_accel(self.ctlFile[A2],axis=2)  
            
        decelVals = self.get_decel()
        if decelVals[0] != self.ctlFile[A1]: 
            self.stop_motion()
            self.set_decel(self.ctlFile[A1],axis=1)
        if decelVals[1] != self.ctlFile[A2]: 
            self.stop_motion()
            self.set_decel(self.ctlFile[A2],axis=2)                  
            
        #--------------------------------------------
        # Set Jerk values of motors for centering Sun
        #--------------------------------------------
        jerkVals = self.get_jerk()
        if jerkVals[0] != self.ctlFile[J1]: 
            self.stop_motion()
            self.set_jerk(self.ctlFile[J1],axis=1)
        if jerkVals[1] != self.ctlFile[J2]: 
            self.stop_motion()
            self.set_jerk(self.ctlFile[J2],axis=2)   
            
    def setVel(self,speed):
        #-----------------------------------------
        # Set the velocity of motors. This is for
        # setting the velocities back to nominal 
        # state
        #-----------------------------------------
        if speed == "normal":
            v1 = "NominalVelAxis1"
            v2 = "NominalVelAxis2"
            
        velVals = self.get_vel()
        if velVals[0] != self.ctlFile[v1]:
            self.stop_motion()
            self.set_vel(self.ctlFile[v1], axis=1)
        if velVals[1] != self.ctlFile[v2]:
            self.stop_motion()
            self.set_vel(self.ctlFile[v2], axis=2)        
        
    def initializeTracker(self):
        #----------------------------------------
        # Initialize connection to ESP controller
        #----------------------------------------
        self.setParam("TRACKER_STATUS INITIALIZING")
        self.motorInit()
        
        #------------------------------------
        # Initialize connection to USB camera
        #------------------------------------
        self.connectCam()        
            
    def parkTracker(self):
        ''' Send Tracker to park position '''
        
        if self.TCPflg: self.setParam("TRACKER_STATUS PARK")
        self.stop_motion()
        self.setAccelJerk(speed="fast")
        self.move_tracker_abs(self.ctlFile['AzHome'],axis=self.ctlFile['AzAxis'])
        self.move_tracker_abs(self.ctlFile['ElHome'],axis=self.ctlFile['ElAxis'])
        self.cordFlp  = False       
            
    def shutdownTracker(self):
        #---------------------------------------------------
        # Turn off motors and disconnect from ESP controller
        #---------------------------------------------------
        self.parkTracker()
        self.axis_off()
        self.disconnect()
        
        #-------------------------------
        # Close connection to USB camera
        #-------------------------------
        self.camClose()

        #--------------------------
        # Terminate tracker program
        #--------------------------
        self.setParam("TRACKER_STATUS TERMINATED")
        self.quitTrackerProgram()
                
    def baseCallibrate(self):
        '''Calibrate tracker. Ideally a change in Elevation angle would soley correspond to a change
           in the y pixels and a change in the Azimuth angle would correspond to a change in the x
           pixels (The azimuth and elevation angles are orthogonal and therefore the change in pixels
           should be orthogonal); however, there is going to be some rotation so a change in one angle
           (elevation or azimuth) will cause a change in both x and y pixels. This rotation and scaling is
           determined by finding the transformation matrix

           **Note: As the Azimuth angle change so will the transformation matrix (i.e. the 
           amount the x & y axis are rotated will change) because of the geometry of the solar tracker. 
           Therefore, calibrations should be done through out the day.
           
           **Note: The callibration is done in the coordinate system of the tracker!!!'''

        #-----------------------------------------------
        # Iterate over several azimuth and elevation
        # delta to determine corresponding pixel changes
        #-----------------------------------------------
        del_az_pos = [self.ctlFile['AzimuthCalStep']    + i*self.ctlFile['AzimuthCalStep']   for i in range(0,5,1)]
        del_az_neg = [-self.ctlFile['AzimuthCalStep']   - i*self.ctlFile['AzimuthCalStep']   for i in range(0,5,1)]
        del_el_pos = [self.ctlFile['ElevationCalStep']  + i*self.ctlFile['ElevationCalStep'] for i in range(0,5,1)]
        del_el_neg = [-self.ctlFile['ElevationCalStep'] - i*self.ctlFile['ElevationCalStep'] for i in range(0,5,1)]

        self.cal_az = np.array(del_az_pos + del_az_neg)
        self.cal_el = np.array(del_el_pos + del_el_neg)

        #---------------------------------------------------
        # Determine flip state when callibration takes place
        #---------------------------------------------------
        self.calFlipState = self.cordFlp

        #-----------------------------------------------
        # Get current tracker position and calculate all
        # delta angles in tracker position
        #-----------------------------------------------
        self.origEl = self.get_tracker_position(self.ctlFile['ElAxis'])
        self.origAz = self.get_tracker_position(self.ctlFile['AzAxis'])
        
        el_orig     = copy.copy(self.origEl)
        az_orig     = copy.copy(self.origAz)

        self.findEllipseN(N=self.ctlFile['ellipseN'])
        xSun_orig = self.x_sun
        ySun_orig = self.y_sun

        del_az = self.cal_az + self.origAz
        del_el = self.cal_el + self.origEl

        del_xPixEl = np.zeros(len(del_el))
        del_yPixEl = np.zeros(len(del_el))
        del_xPixAz = np.zeros(len(del_az))
        del_yPixAz = np.zeros(len(del_az))

        #-------------------------------------
        # Loop through delta Azimuth angles
        # and then return to original position
        #-------------------------------------
        for i,val in enumerate(del_az):
            self.move_tracker_abs(val,self.ctlFile['AzAxis'])
            self.findEllipseN(aptFlg=False,N=self.ctlFile['ellipseN'])       
            #del_xPixAz[i] = xSun_orig - self.x_sun
            #del_yPixAz[i] = ySun_orig - self.y_sun
            del_xPixAz[i] = self.x_sun - xSun_orig
            del_yPixAz[i] = self.y_sun - ySun_orig            

        self.move_tracker_abs(el_orig,self.ctlFile['ElAxis'])
        self.move_tracker_abs(az_orig,self.ctlFile['AzAxis'])

        #-------------------------------------
        # Loop through delta Elevation angles
        # and then return to original position
        #-------------------------------------
        for i,val in enumerate(del_el):
            self.move_tracker_abs(val,self.ctlFile['ElAxis'])
            self.findEllipseN(aptFlg=False,N=self.ctlFile['ellipseN'])         
            #del_xPixEl[i] = xSun_orig - self.x_sun
            #del_yPixEl[i] = ySun_orig - self.y_sun
            del_xPixEl[i] = self.x_sun - xSun_orig
            del_yPixEl[i] = self.y_sun - ySun_orig           

        self.move_tracker_abs(el_orig,self.ctlFile['ElAxis'])
        self.move_tracker_abs(az_orig,self.ctlFile['AzAxis'])        

        #-----------------------------------
        # Calculate transformation matrix 
        # using least squares solver:
        # X*A = Y where Y is the El and Az
        # angles, X are the change in pixels
        # and A is the transformation matrix
        #-----------------------------------
        stackAz = np.hstack([self.cal_az,np.zeros(len(self.cal_el))])
        stackEl = np.hstack([np.zeros(len(self.cal_az)),self.cal_el])
        Y       = np.vstack([stackAz, stackEl]).T  

        xyPixEl = np.vstack([del_xPixEl,del_yPixEl]).T
        xyPixAz = np.vstack([del_xPixAz,del_yPixAz]).T
        xyPix   = np.vstack([xyPixAz,xyPixEl])

        #-----------------------------------------------------------
        # Find transformation matrix in Tracker coordinate system!!!
        #-----------------------------------------------------------
        A,res,rank,s = np.linalg.lstsq(xyPix,Y)

        #-------------------------------------
        # Set really small values of A to zero
        #-------------------------------------
        A[np.abs(A) < 1e-10] = 0.0

        self.transform = A
        
        
    def rotateTransform(self):
        ''' This method uses the initial calibration and applies a rotation based
            on the change in Azimuth angle from the intial calibration. Transformation
            matrix is in Tracker coordinate system!!!! '''
        
        #--------------------------------------------------
        # Get Original Azimuth angle in tracker coordinates
        #--------------------------------------------------
        origAzAbsCords = self.origAz
        
        #-------------------------------------------------
        # Get Current Azimuth angle in tracker coordinates
        #-------------------------------------------------
        crntAzAbsCords = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
        
        #----------------------------------------------------------------
        # Find change in Azimuth angle and apply to transformation matrix
        #----------------------------------------------------------------
        rotAz = origAzAbsCords - crntAzAbsCords
        
        #------------------------------------
        # Determine secondary rotation matrix
        #------------------------------------
        rotMat = np.array([[math.cos(math.radians(rotAz)),-math.sin(math.radians(rotAz))],
                           [math.sin(math.radians(rotAz)), math.cos(math.radians(rotAz))]])        
        
        #-------------------------------------------
        # Get delta pixels between Sun and aperature
        #-------------------------------------------
        #self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
        
        #---------------------------------------
        # Apply initial transformation to angles
        #---------------------------------------
        #self.pixMatRot = np.dot(self.transform,np.array([self.delX,self.delY]))
        
        #----------------------------------------
        # Apply rotation to transformation matrix
        #----------------------------------------
        self.transformRot = np.dot(rotMat,self.transform)
        
        #-----------
        # Log values
        #-----------
        self.logRotMat(rotAz)

        return self.transformRot
    
    def pixel_to_angle(self,xpix,ypix):
        '''Convert delta pixels to delta angles.
           deltaAngles[0] - Azimuth Angle
           deltaAngles[1] - Elevation Angle '''
        
        #-------------------------------------
        # Call to update transformation matrix
        # based on change in Az angle
        #-------------------------------------
        #self.rotateTransform()
        
        #-----------------------
        # Calculate delta Angles
        #-----------------------
        deltaAngles = np.dot(np.array([xpix,ypix]),self.transform)
        #deltaAngles = np.dot(np.array([xpix,ypix]),self.transformRot)
    
        return deltaAngles
       
    def jogToFindSun(self):
        ''' If Sun is not initially detected, this joggs tracker to find sun '''
        
        #----------------------------------------------
        # Compose a matrix of Az and El delta values to 
        # try to find the Sun
        #---------------------------------------------------
        # Get Current position in Absolute coordinate system
        #---------------------------------------------------
        crntAz      = self.tracker_to_abs_Az(self.get_tracker_position(axis=self.ctlFile['AzAxis']))
        crntEl      = self.tracker_to_abs_El(self.get_tracker_position(axis=self.ctlFile['ElAxis']))

        #----------------------------------------------------------
        # Add current position to deltas in Tracker Coordinates
        # Find Cartesian product of possible delta El and Az angles
        #----------------------------------------------------------
        #---------------------------------------
        # Iterate over multiples of delta angles
        # to find Sun
        #---------------------------------------
        for i in range(1,11):
            AzAngles       = np.array([0,-self.ctlFile['AzJogStep'],self.ctlFile['AzJogStep']])*i
            ElAngles       = np.array([0,-self.ctlFile['ElJogStep'],self.ctlFile['ElJogStep']])*i
            AzAngles      += crntAz
            ElAngles      += crntEl
            
            deltaAngles    = cartesian((AzAngles,ElAngles))
            deltaAngles    = np.delete(deltaAngles,0,axis=0)   # Delete First row, which is just [0,0]    
        
            #----------------------------------------
            # Iterate through positive and negative 
            # combinations of delta angle to find sun
            #----------------------------------------
            for angles in deltaAngles:
                
                #--------------
                # Point Tracker
                #--------------
                self.pointTracker(angles[0], angles[1])
            
                #-------------------
                # Look for Sun image
                #-------------------
                self.findEllipseN(N=self.ctlFile['ellipseN'])
                
                if self.sunFound: break
            
            if self.sunFound: break
        
        if self.sunFound:
            self.jogDeltaAz = angles[0]
            self.jogDeltaEl = angles[1]
            return True
        else:             
            return False
        
    
    def track(self,surfPres=None,surfTemp=None,jogFlg=False,guiFlg=False,skipMainLoopFlg=False):
        ''' This method is used bring the sun to the center of the CCD using
             optimization routines to minimize the distance between Sun center
             and center of CCD
             guiFlg and firstFlg are only used by the GUI.
             '''
            
        #----------------------------------------------
        # Set initial flags and calculate initial 
        # Sun azimuth and elevation angles. Determine
        # time to flip and report to data server. This
        # flip time is only for Nominal mode!!! In flip
        # mode the times will be different!!!
        #----------------------------------------------
        entranceAngleLim = -self.ctlFile["AzSoftTravelLim"]+self.ctlFile['AzOffSet']
        exitAngleLim     =  self.ctlFile["AzSoftTravelLim"]+self.ctlFile['AzOffSet']
        if entranceAngleLim  < -180.0: entranceAngleLim  += 360.0
        if exitAngleLim      < -180.0: exitAngleLim      += 360.0
        
        entranceAngleLimAbs = self.tracker_to_abs_Az(entranceAngleLim)
        exitAngleLimAbs     = self.tracker_to_abs_Az(exitAngleLim)
        
        calFlg   = True
        crntD    = dt.datetime.utcnow()
        crntSec  = (crntD-dt.datetime(crntD.year,crntD.month,crntD.day)).total_seconds()
        
        (sunAzVec,sunElVec,sunTimes) = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'],
                                               dateT=crntD,surfP=None,surfT=None,vecFlg=True)
        
        ent_ind     = find_nearestInd(sunAzVec,entranceAngleLimAbs)
        ext_ind     = find_nearestInd(sunAzVec,exitAngleLimAbs)
        
        #--------------------------------------------------------------
        # Find time in minutes from begining of day of for entrance and 
        # exit of azimuth motor exclusion zone. This should be the same
        # for all days. The Sun's azimuth angle associated with a
        # specific time will remain constant
        #--------------------------------------------------------------
        ent_Seconds = sunTimes[ent_ind]
        ext_Seconds = sunTimes[ext_ind]
        
        deltaEnt_T = (ent_Seconds - crntSec) / 60.0          # Delta time [minutes] to next entrance side of Az motor exclusion zone
        deltaExt_T = (ext_Seconds - crntSec) / 60.0          # Delta time [minutes] to next exit side of Az motor exclusion zone
        
        if deltaEnt_T < 0.0:  deltaEnt_T += 1440.0
        if deltaExt_T < 0.0:  deltaExt_T += 1440.0   
        
        if self.TCPflg:
            self.setParam("TRACKER_TIMETOFLIP {:10.2f}".format(deltaEnt_T))  
            self.setParam("TRACKER_TIMETONOMINAL {:10.2f}".format(deltaExt_T))
        
        print "Time to entrance side of Az motor exclusion zone (Nominal Mode) = {:10.2f} minutes".format(deltaEnt_T)
        print "Time to exit side of Az motor exclusion zone (Nominal Mode)     = {:10.2f} minutes\n".format(deltaExt_T)
        
        while True:
            if all([guiFlg,skipMainLoopFlg]):
                calTime = self.caltime
                pass
            else:
                ephemFlg = False
    
                #-------------------------------------------------
                # Set acceleration,deceleration, and jerk of motors 
                # for centering of Sun. This is relatively fast.
                #-------------------------------------------------
                self.setAccelJerk(speed="fast")              

                #----------------------------------------------
                # Check TCP Server for Temperature and Pressure
                #----------------------------------------------
                if self.TCPflg:
                    surfPres,surfTemp = self.getTempPress(surfPres,surfTemp)
                                        
                #--------------------------------------------
                # Calculate delta flip time for nominal mode!
                #--------------------------------------------
                crntDateTime  = dt.datetime.utcnow()
                crntSec       = (crntDateTime-dt.datetime(crntDateTime.year,crntDateTime.month,crntDateTime.day)).total_seconds()
                deltaEnt_T    = (ent_Seconds - crntSec) / 60.0          # Delta time [minutes] to next entrance side of Az motor exclusion zone
                deltaExt_T    = (ext_Seconds - crntSec) / 60.0          # Delta time [minutes] to next exit side of Az motor exclusion zone
                
                if deltaEnt_T < 0.0:  deltaEnt_T += 1440.0
                if deltaExt_T < 0.0:  deltaExt_T += 1440.0   
                
                if self.TCPflg:
                    self.setParam("TRACKER_TIMETOFLIP {:10.2f}".format(deltaEnt_T))  
                    self.setParam("TRACKER_TIMETONOMINAL {:10.2f}".format(deltaExt_T))
                
                print "Time to entrance side of Az motor exclusion zone (Nominal Mode) = {:10.2f} minutes".format(deltaEnt_T)
                print "Time to exit side of Az motor exclusion zone (Nominal Mode)     = {:10.2f} minutes\n".format(deltaExt_T)   
                    
                #------------------------------------
                # Check TCP server for how to proceed
                #------------------------------------
                if self.TCPflg:
                    trckFlg    = self.getParam("TRACKER_CMND")    
                    if any([not trckFlg,trckFlg == "-999"]):trckFlg = "STANDBY"
                    
                    #-------------------------------------------
                    # Shutdown the tracker and terminate program
                    #-------------------------------------------
                    if trckFlg.upper() == "QUIT": 
                        self.setParam("TRACKER_STATUS STANDBY")
                        self.shutdownTracker()
                    
                    #----------------------------------------------------
                    # Place tracker in park position but do not terminate
                    #----------------------------------------------------
                    if trckFlg.upper() == "PARK": 
                        self.setParam("TRACKER_STATUS PARK")
                        
                        #---------------------------------------------
                        # Check if tracker is already in park position
                        #---------------------------------------------
                        trackerAz = self.get_tracker_position(axis=self.ctlFile["AzAxis"])
                        trackerEl = self.get_tracker_position(axis=self.ctlFile["ElAxis"])
                        
                        if all([trackerAz == self.ctlFile['AzHome'], trackerEl == self.ctlFile['ElHome']]):
                            sleep(self.ctlFile['waitTrckInt'])
                            continue
                        else:
                            self.parkTracker()
                            continue
                    
                    #-----------------------------------------
                    # Just stop tracking and wait for commands
                    #-----------------------------------------
                    if trckFlg.upper() == "STANDBY":
                        self.setParam("TRACKER_STATUS STANDBY")
                        sleep(self.ctlFile['waitTrckInt'])
                        continue
                    
                    #-----------------
                    # Regular tracking
                    #-----------------
                    elif trckFlg.upper() == "CAM": 
                        self.setParam("TRACKER_STATUS SEARCHING")
                        pass
                    
                    #---------------------
                    # Track only ephemeris
                    #---------------------
                    elif trckFlg.upper() == "EPHEM": 
                        self.setParam("TRACKER_STATUS EPHEM")
                        ephemFlg = True
                        
                    #------------------
                    # Unrecognized case
                    #------------------
                    else:
                        self.setParam("TRACKER_STATUS STANDBY")
                        sleep(self.ctlFile['waitTrckInt'])
                        continue                        
                
                #-----------------------
                # Find current date time
                #-----------------------
                crntDateTime  = dt.datetime.utcnow()
    
                #-----------------------------------------------------------
                # Get current ephemris data and ephemris data 10 minutes out
                #-----------------------------------------------------------
                (sunAz,sunEl) = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'], dateT=crntDateTime, surfT=surfTemp, surfP=surfPres)            
                                             
                #---------------------
                # Initial point to Sun
                #---------------------
                #try:
                    #self.AzOffSet
                    #self.ElOffSet
                    #self.pointTracker(sunAz, sunEl, deltaAz,ElOffset=self.ElOffSet, AzOffset=self.AzOffSet)
                #except NameError:
                self.pointTracker(sunAz, sunEl, ElOffset=self.ctlFile['ElOffSet'], AzOffset=self.ctlFile['AzOffSet'])

                #-------------------------------
                # Log ephem and tracker position
                #-------------------------------
                trackerAz = self.get_tracker_position(axis=self.ctlFile["AzAxis"])
                trackerEl = self.get_tracker_position(axis=self.ctlFile["ElAxis"])                
                self.logSunAngle(sunEl,sunAz,trackerEl,trackerAz)
    
                #------------------------------------------------
                # Send timestamp indicating tracker still running
                #------------------------------------------------
                #if self.TCPflg:
                    #dateTstr = "{0:}{1:02}{2:02}_{3:02}{4:02}{5:02}".format(crntDateTime.year,crntDateTime.month,crntDateTime.day,crntDateTime.hour,
                                                                            #crntDateTime.minute,crntDateTime.second)
                    #self.setParam("TRACKER_TS " + dateTstr)
                
                #------------------------------
                # If tracking by ephemeris only
                #------------------------------
                if ephemFlg: 
                    sleep(2)
                    if self.TCPflg:
                        if self.cordFlp: self.setParam("TRACKER_ELMIRROR FLIP")
                        else:            self.setParam("TRACKER_ELMIRROR NOMINAL")
                    continue
                
                #-------------
                # Look for Sun
                #-------------
                self.findEllipseN(N=self.ctlFile['ellipseN'])
    
                #--------------------------------
                # If Sun is not found jog tracker 
                #--------------------------------
                if all([not self.sunFound,jogFlg]): 
                    rtn = self.jogToFindSun()
    
                    if not rtn:
                        print 'Unable to find Sun via jogging tracker.'                            
                        sleep(self.ctlFile['noSunSleep'])
                        continue
     
                #---------------------------------------------
                # If Sun is not found and jog tracker flag was 
                # not chosen then wait to see if Sun appears
                #---------------------------------------------
                elif all([not self.sunFound,not jogFlg]):
                    print 'Unable to find Sun, try jog tracker option.'                            
                    sleep(self.ctlFile['noSunSleep'])
                    continue         
    
                #---------------------------------------
                # Do initial base calibration of tracker
                #---------------------------------------
                if calFlg:
                    self.baseCallibrate()
                    calTime = dt.datetime.utcnow()
                    self.calibrationTime = calTime
                    self.logTransform(calTime)
    
                #----------------------------------
                # Move tracker to center Sun to CCD
                #-------------------------------------------------------
                # Find delta pixels between Sun center and center of CCD
                #-------------------------------------------------------
                self.findEllipseN(N=self.ctlFile['ellipseN'])
                
                #-------------------------------------
                # Convert delta pixels to delta angles
                #-------------------------------------
                newAngles = self.pixel_to_angle(self.delX, self.delY)
                delAz     = newAngles[0] 
                delEl     = newAngles[1]
    
                #------------------------------------------------
                # Check Delta Angles. This should be fairly small
                #------------------------------------------------
                if any([abs(delAz)>self.ctlFile['delAzSeekLim'],abs(delEl)>self.ctlFile['delElSeekLim']]):
                    print "Delta Angles to move Sun to center of CCD are larger than limits!!!!\n"
                    print "Delta Az Angle = {}\n".format(delAz)
                    print "Delta El Angle = {}\n".format(delEl)
                    continue
                    
                #-------------------------------------------
                # Get current Az and El positions of tracker
                # and add delta angles
                #-------------------------------------------
                crntTrackerAzPos = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
                crntTrackerElPos = self.get_tracker_position(axis=self.ctlFile['ElAxis'])   
                
                #-------------------------------
                # Add offset to current position 
                # in tracker coordinates
                #-------------------------------
                crntTrackerAzPos += delAz
                
                #----------------------------------------------------------------------
                # Determine if flip state is different than when calibration took place
                # If this is the case, change in elevation must be handled differently
                #----------------------------------------------------------------------
                flpState = self.determine_flip(setState=False)
                if self.calFlipState == flpState: crntTrackerElPos += delEl
                else:                             crntTrackerElPos -= delEl
                                
                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                newTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
                newTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)

                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                #crntTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
                #crntTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)
            
                #newTrackerAzPos  = crntTrackerAzPos + delAz
                #newTrackerElPos  = crntTrackerElPos + delEl                


                if (newTrackerAzPos < 0): newTrackerAzPos += 360.0
                if (newTrackerElPos < 0): newTrackerElPos += 360.0
                
                #------------------------------
                # Point Tracker to new position
                #------------------------------
                print "Ephemeris position  Az = {0:7.3f}, El = {1:7.3f}".format(sunAz,sunEl)
                print "Pointing tracker to Az = {0:7.3f}, El = {1:7.3f}".format(newTrackerAzPos,newTrackerElPos)
                
                self.pointTracker(newTrackerAzPos, newTrackerElPos, ElOffset=0.0, AzOffset=0.0)
                
                #------------------------------------------------------
                # Find distance between center of Sun and center of CCD
                #------------------------------------------------------
                self.findEllipseN(aptFlg=False, N=2)
    
                #---------------------------------------------------------
                # Check if findEllipse find the Sun. If not try seek again
                #---------------------------------------------------------
                if not self.sunFound: 
                    print "Unable to find the Sun!!"
                    continue 
                
                #--------------------
                # Log Sun information
                #--------------------
                self.logSunPix("NOAPT")
                print "Distance between center of Sun and Center of CCD: deltaX pixels = {0:}, deltaY pixels = {1:}".format(self.delX,self.delY)
                
            #-------------------------------------------
            # Loop on holding Sun on center of aperature
            #-------------------------------------------------
            # Set acceleration,deceleration, and jerk of motors 
            # for centering of Sun. This is relatively fast.
            #-------------------------------------------------
            self.setAccelJerk(speed="slow")              
                
            while True:
                
                if guiFlg: skipMainLoopFlg = False
                
                calFlg = False
                #----------------------------------------------------
                # Calibration is run on an interval specified in the
                # control file. Determine if it's time to calibrate.
                #----------------------------------------------------
                crntT = dt.datetime.utcnow()
                if ((crntT - calTime).total_seconds() > self.ctlFile['calInterval']):
                    
                    #------------------------------------------------------
                    # Check TCP server is measurement is currently running.
                    # If so do not do a calibration, wait till measurement
                    # is done.
                    #------------------------------------------------------
                    if self.TCPflg:
                        measFlg = self.getParam("OPUS_STATUS")
                        if measFlg.upper() == "SCANNING": pass
                        else:
                            calFlg = True
                            break
                    else:
                        calFlg = True
                        break
                    
                #--------------------------------------------
                # Calculate delta flip time for nominal mode!
                #--------------------------------------------
                crntSec       = (crntT-dt.datetime(crntT.year,crntT.month,crntT.day)).total_seconds()
                deltaEnt_T    = (ent_Seconds - crntSec) / 60.0          # Delta time [minutes] to next entrance side of Az motor exclusion zone
                deltaExt_T    = (ext_Seconds - crntSec) / 60.0          # Delta time [minutes] to next exit side of Az motor exclusion zone
                
                if deltaEnt_T < 0.0:  deltaEnt_T += 1440.0
                if deltaExt_T < 0.0:  deltaExt_T += 1440.0   
                
                if self.TCPflg:
                    self.setParam("TRACKER_ENTRANCELIMITTIME {:10.2f}".format(deltaEnt_T))  
                    self.setParam("TRACKER_EXITLIMITTIME {:10.2f}".format(deltaExt_T))
                
                print "Time to entrance side of Az motor exclusion zone (Nominal Mode) = {:10.2f} minutes".format(deltaEnt_T)
                print "Time to exit side of Az motor exclusion zone (Nominal Mode)     = {:10.2f} minutes\n".format(deltaExt_T)                   

                #------------------------------------
                # Check if tracker comand has changed
                #------------------------------------
                trckCmnd = self.getParam("TRACKER_CMND")
                if trckCmnd.upper() != "CAM": break                
                
                #----------------------------------------
                # Move tracker to center Sun to aperature
                #---------------------------------------------------
                # Find delta pixels between Sun center and Aperature
                #---------------------------------------------------
                testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
                
                #-------------------------------------------------------------
                # Check if findEllipse could not find the Sun or aperature. If
                # this is the case go back to seek loop and try moving Sun to 
                # center of CCD or waiting for Sun to re-appear
                #-------------------------------------------------------------
                if not testRtn: break
                
                #----------------------------------
                # Print track information to stdout
                #----------------------------------
                print "-"*42
                print "* {0:7.2f} {1:7.2f} {2:7.2f} {3:7.2f} {4:7.2f}".format(self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.area_apt)
                print "-"*42 + "\n"               
    
                #-------------------------------------
                # Convert delta pixels to delta angles
                #-------------------------------------
                # TESTING !!!!
                #if all([np.abs(self.delX) < 5.0,np.abs(self.delX) < 5.0 ]):
                    #xPix = self.delX * 1.25
                    #yPix = self.delY * 1.25
                #else:
                    #xPix = self.delX
                    #yPix = self.delY
                    
                newAngles = self.pixel_to_angle(self.delX, self.delY)
                #newAngles = self.pixel_to_angle(xPix, yPix)
                delAz     = newAngles[0] 
                delEl     = newAngles[1]
    
                #-------------------------------------------
                # Get current Az and El positions of tracker
                # and add delta angles
                #-------------------------------------------
                crntTrackerAzPos = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
                crntTrackerElPos = self.get_tracker_position(axis=self.ctlFile['ElAxis'])       
                
                #-------------------------------
                # Add offset to current position 
                # in tracker coordinates
                #-------------------------------
                crntTrackerAzPosDel = crntTrackerAzPos + delAz
                
                #----------------------------------------------------------------------
                # Determine if flip state is different than when calibration took place
                # If this is the case, change in elevation must be handled differently
                #----------------------------------------------------------------------
                flpState = self.determine_flip(setState=False)
                if self.calFlipState == flpState: crntTrackerElPosDel = crntTrackerElPos + delEl
                else:                             crntTrackerElPosDel = crntTrackerElPos + delEl            

                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                newTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPosDel)
                newTrackerElPos = self.tracker_to_abs_El(crntTrackerElPosDel)
                
                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                #crntTrackerAzPosDel = self.tracker_to_abs_Az(crntTrackerAzPosDel)
                #crntTrackerElPosDel = self.tracker_to_abs_El(crntTrackerElPosDel)
            
                #newTrackerAzPos  = crntTrackerAzPosDel + delAz
                #newTrackerElPos  = crntTrackerElPosDel + delEl                
                
                if (newTrackerAzPos < 0): newTrackerAzPos += 360.0
                if (newTrackerElPos < 0): newTrackerElPos += 360.0           
                
                #------------------------------------------------
                # Check Delta Angles. This should be fairly small
                #------------------------------------------------
                if any([delAz>self.ctlFile['delAzHoldLim'],delEl>self.ctlFile['delElHoldLim']]):
                    print "Delta Angles to move Sun to center of Aperature are larger than limits!!!!\n"
                    print "Delta Az Angle = {}\n".format(delAz)
                    print "Delta El Angle = {}\n".format(delEl)
                    break              
                
                #---------------------------------------------------
                # Find difference between Ephemeris position and new
                # position calculated with calibration
                #---------------------------------------------------
                crntDateTime  = dt.datetime.utcnow()
                (sunAz,sunEl) = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'], dateT=crntDateTime,surfT=surfTemp,surfP=surfPres)            
                self.AzOffSet = newTrackerAzPos - sunAz
                self.ElOffSet = newTrackerElPos - sunEl
                
                #------------------------------
                # Point Tracker to new position
                #------------------------------
                self.pointTracker(newTrackerAzPos, newTrackerElPos, ElOffset=0.0, AzOffset=0.0)        

                testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
                
                #-------------------------------------------------------------
                # Check if findEllipse could not find the Sun or aperature. If
                # this is the case go back to seek loop and try moving Sun to 
                # center of CCD or waiting for Sun to re-appear
                #-------------------------------------------------------------
                if not testRtn: break                

                #---------------------------------------------
                # Log data related to finding sun and aperture
                #---------------------------------------------
                self.logSunAngle(sunEl,sunAz,crntTrackerElPos,crntTrackerAzPos)
                self.logSunPix("YESAPT")

                #---------------------------------------------
                # Send information to the TCP server regarding 
                # offset angles, sun radiance, etc
                #-----------------------------------------------
                # Tracker is locked on Sun send OK to TCP server
                #-----------------------------------------------
                if self.TCPflg: 
                    #dateTstr = "{0:}{1:02}{2:02}_{3:02}{4:02}{5:02}".format(crntDateTime.year,crntDateTime.month,crntDateTime.day,crntDateTime.hour,
                                                                            #crntDateTime.minute,crntDateTime.second)
                    #self.setParam("TRACKER_TS " + dateTstr)                        
                    self.setParam("TRACKER_STATUS LOCK")
                    if self.cordFlp: self.setParam("TRACKER_ELMIRROR FLIP")
                    else:            self.setParam("TRACKER_ELMIRROR NOMINAL")                    
                             
                #----------------------------------
                # Print track information to stdout
                #----------------------------------
                print "-"*42   
                print "  {0:7.2f} {1:7.2f} {2:7.2f} {3:7.2f} {4:7.2f}".format(self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.area_apt)
                print "-"*42 + "\n"
                
                #-----------------------------------------
                # If in GUI mode return control to the GUI
                #-----------------------------------------
                if guiFlg: return calTime
                
                #----------------------------
                # Recalculate every N seconds
                #----------------------------
                sleep(self.ctlFile['holdSunInt'])

        return True
              
        
    def trackVel(self,surfPres=None,surfTemp=None,jogFlg=False,guiFlg=False,skipMainLoopFlg=False):
        ''' This method is used bring the sun to the center of the CCD using
             optimization routines and tracks velocities
             guiFlg and firstFlg are only used by the GUI.
             '''
            
        #----------------------------------------
        # Set initial flags and calculate initial 
        # Sun azimuth and elevation velocities
        #----------------------------------------
        calFlg   = True
        prevDate = dt.datetime.utcnow()
        (sunAzVel,sunElVel,sunTimes) = sunAzElVel(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'],
                                                  dateT=prevDate,deltaT=self.ctlFile['deltaTsunEphem'],surfP=None,surfT=None)

        while True:
            if all([guiFlg,skipMainLoopFlg]):
                calTime = self.caltime
                pass
            else:
                ephemFlg = False
    
                #-------------------------------------------------
                # Set acceleration,deceleration, and jerk of motors 
                # for centering of Sun. This is relatively fast.
                # Set the velocity back to nominal state.
                #-------------------------------------------------
                self.setAccelJerk(speed="fast")              
                self.setVel(speed="normal")

                #----------------------------------------------
                # Check TCP Server for Temperature and Pressure
                #----------------------------------------------
                if self.TCPflg:
                    surfPres,surfTemp = self.getTempPress(surfPres,surfTemp)
                    
                #------------------------------------
                # Check TCP server for how to proceed
                #------------------------------------
                if self.TCPflg:
                    trckFlg    = self.getParam("TRACKER_CMND")    
                    if any([not trckFlg,trckFlg == "-999"]):trckFlg = "STANDBY"
                    
                    #-------------------------------------------
                    # Shutdown the tracker and terminate program
                    #-------------------------------------------
                    if trckFlg.upper() == "QUIT": 
                        self.setParam("TRACKER_STATUS STANDBY")
                        self.shutdownTracker()
                    
                    #----------------------------------------------------
                    # Place tracker in park position but do not terminate
                    #----------------------------------------------------
                    if trckFlg.upper() == "PARK": 
                        self.setParam("TRACKER_STATUS PARK")
                        self.parkTracker()
                        sleep(self.ctlFile['waitTrckInt'])
                        continue
                    
                    #-----------------------------------------
                    # Just stop tracking and wait for commands
                    #-----------------------------------------
                    if trckFlg.upper() == "STANDBY":
                        self.setParam("TRACKER_STATUS STANDBY")
                        sleep(self.ctlFile['waitTrckInt'])
                        continue
                    
                    #-----------------
                    # Regular tracking
                    #-----------------
                    elif trckFlg.upper() == "CAM": 
                        self.setParam("TRACKER_STATUS SEARCHING")
                        pass
                    
                    #---------------------
                    # Track only ephemeris
                    #---------------------
                    elif trckFlg.upper() == "EPHEM": 
                        self.setParam("TRACKER_STATUS EPHEM")
                        ephemFlg = True
                        
                    #------------------
                    # Unrecognized case
                    #------------------
                    else:
                        self.setParam("TRACKER_STATUS STANDBY")
                        sleep(self.ctlFile['waitTrckInt'])
                        continue                        
                
                #--------------------------------------------------------------------
                # Find current date time and see if this is the same as previous time
                #--------------------------------------------------------------------
                crntDateTime  = dt.datetime.utcnow()
    
                #-----------------------------------------------------------
                # Get current ephemris data and ephemris data 10 minutes out
                #-----------------------------------------------------------
                (sunAz,sunEl) = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'], dateT=crntDateTime,surfT=surfTemp, surfP=surfPres)            
                
                #----------------------
                # Initial point to Sun
                #---------------------
                #try:
                    #self.AzOffSet
                    #self.ElOffSet
                    #self.pointTracker(sunAz, sunEl, deltaAz,ElOffset=self.ElOffSet, AzOffset=self.AzOffSet)
                #except NameError:
                self.pointTracker(sunAz, sunEl, ElOffset=self.ctlFile['ElOffSet'], AzOffset=self.ctlFile['AzOffSet'])
    
                #------------------------------------------------
                # Send timestamp indicating tracker still running
                #------------------------------------------------
                #if self.TCPflg:
                    #dateTstr = "{0:}{1:02}{2:02}_{3:02}{4:02}{5:02}".format(crntDateTime.year,crntDateTime.month,crntDateTime.day,crntDateTime.hour,
                                                                            #crntDateTime.minute,crntDateTime.second)
                    #self.setParam("TRACKER_TS " + dateTstr)

                #------------------------------
                # If tracking by ephemeris only
                #------------------------------
                if ephemFlg: 
                    sleep(2)
                    if self.TCPflg:
                        if self.cordFlp: self.setParam("TRACKER_ELMIRROR FLIP")
                        else:            self.setParam("TRACKER_ELMIRROR NOMINAL")
                    continue
                
                #-------------
                # Look for Sun
                #-------------
                self.findEllipseN(N=self.ctlFile['ellipseN'])
    
                #--------------------------------
                # If Sun is not found jog tracker 
                #--------------------------------
                if all([not self.sunFound,jogFlg]): 
                    rtn = self.jogToFindSun()
    
                    if not rtn:
                        print 'Unable to find Sun via jogging tracker.'                            
                        sleep(self.ctlFile['noSunSleep'])
                        continue
     
                #---------------------------------------------
                # If Sun is not found and jog tracker flag was 
                # not chosen then wait to see if Sun appears
                #---------------------------------------------
                elif all([not self.sunFound,not jogFlg]):
                    print 'Unable to find Sun, try jog tracker option.'                            
                    sleep(self.ctlFile['noSunSleep'])
                    continue         
    
                #---------------------------------------
                # Do initial base calibration of tracker
                #---------------------------------------
                if calFlg:
                    self.baseCallibrate()
                    calTime = dt.datetime.utcnow()
                    self.calibrationTime = calTime
                    self.logTransform(calTime)
    
                #----------------------------------
                # Move tracker to center Sun to CCD
                #-------------------------------------------------------
                # Find delta pixels between Sun center and center of CCD
                #-------------------------------------------------------
                self.findEllipseN(N=self.ctlFile['ellipseN'])
                
                #-------------------------------------
                # Convert delta pixels to delta angles
                #-------------------------------------
                newAngles = self.pixel_to_angle(self.delX, self.delY)
                delAz     = newAngles[0] 
                delEl     = newAngles[1]
    
                #------------------------------------------------
                # Check Delta Angles. This should be fairly small
                #------------------------------------------------
                if any([abs(delAz)>self.ctlFile['delAzSeekLim'],abs(delEl)>self.ctlFile['delElSeekLim']]):
                    print "Delta Angles to move Sun to center of CCD are larger than limits!!!!\n"
                    print "Delta Az Angle = {}\n".format(delAz)
                    print "Delta El Angle = {}\n\n".format(delEl)
                    continue
                    
                #-------------------------------------------
                # Get current Az and El positions of tracker
                # and add delta angles
                #-------------------------------------------
                crntTrackerAzPos = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
                crntTrackerElPos = self.get_tracker_position(axis=self.ctlFile['ElAxis'])   
                
                #-------------------------------
                # Add offset to current position 
                # in tracker coordinates
                #-------------------------------
                crntTrackerAzPos += delAz
                
                #----------------------------------------------------------------------
                # Determine if flip state is different than when calibration took place
                # If this is the case, change in elevation must be handled differently
                #----------------------------------------------------------------------
                flpState = self.determine_flip(setState=False)
                if self.calFlipState == flpState: crntTrackerElPos += delEl
                else:                             crntTrackerElPos -= delEl
                                
                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                newTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
                newTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)

                #----------------------------------------------
                # Convert tracker position to absolute position
                #----------------------------------------------
                #crntTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
                #crntTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)
            
                #newTrackerAzPos  = crntTrackerAzPos + delAz
                #newTrackerElPos  = crntTrackerElPos + delEl                


                if (newTrackerAzPos < 0): newTrackerAzPos += 360.0
                if (newTrackerElPos < 0): newTrackerElPos += 360.0
                
                #------------------------------
                # Point Tracker to new position
                #------------------------------
                print "Ephemeris position  Az = {0:7.3f}, El = {1:7.3f}".format(sunAz,sunEl)
                print "Pointing tracker to Az = {0:7.3f}, El = {1:7.3f}".format(newTrackerAzPos,newTrackerElPos)
                
                self.pointTracker(newTrackerAzPos, newTrackerElPos, ElOffset=0.0, AzOffset=0.0)
                
                #------------------------------------------------------
                # Find distance between center of Sun and center of CCD
                #------------------------------------------------------
                self.findEllipseN(aptFlg=False, N=2)
    
                #---------------------------------------------------------
                # Check if findEllipse find the Sun. If not try seek again
                #---------------------------------------------------------
                if not self.sunFound: 
                    print "Unable to find the Sun!!"
                    continue 
                
                #--------------------
                # Log Sun information
                #--------------------
                self.logSunPix("NOAPT")
                print "Distance between center of Sun and Center of CCD: deltaX pixels = {0:}, deltaY pixels = {1:}".format(self.delX,self.delY)
                
            #---------------------------------
            # Move Sun to center with Aperture
            #-------------------------------------------------
            # Set acceleration,deceleration, and jerk of motors 
            # for centering of Sun. This is relatively fast.
            #-------------------------------------------------
            self.setAccelJerk(speed="slow")              
                
            #----------------------------------------
            # Move tracker to center Sun to aperature
            #---------------------------------------------------
            # Find delta pixels between Sun center and Aperature
            #---------------------------------------------------
            testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
        
            #-------------------------------------------------------------
            # Check if findEllipse could not find the Sun or aperature. If
            # this is the case go back to seek loop and try moving Sun to 
            # center of CCD or waiting for Sun to re-appear
            #-------------------------------------------------------------
            if not testRtn: continue
                
            #-------------------------------------
            # Convert delta pixels to delta angles
            #-------------------------------------
            newAngles = self.pixel_to_angle(self.delX, self.delY)
            delAz     = newAngles[0] 
            delEl     = newAngles[1]
        
            #-------------------------------------------
            # Get current Az and El positions of tracker
            # and add delta angles
            #-------------------------------------------
            crntTrackerAzPos = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
            crntTrackerElPos = self.get_tracker_position(axis=self.ctlFile['ElAxis'])       
        
            #-------------------------------
            # Add offset to current position 
            # in tracker coordinates
            #-------------------------------
            crntTrackerAzPos += delAz
        
            #----------------------------------------------------------------------
            # Determine if flip state is different than when calibration took place
            # If this is the case, change in elevation must be handled differently
            #----------------------------------------------------------------------
            flpState = self.determine_flip(setState=False)
            if self.calFlipState == flpState: crntTrackerElPos += delEl
            else:                             crntTrackerElPos -= delEl            
        
            #----------------------------------------------
            # Convert tracker position to absolute position
            #----------------------------------------------
            newTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
            newTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)
        
            #----------------------------------------------
            # Convert tracker position to absolute position
            #----------------------------------------------
            #crntTrackerAzPos = self.tracker_to_abs_Az(crntTrackerAzPos)
            #crntTrackerElPos = self.tracker_to_abs_El(crntTrackerElPos)
        
            #newTrackerAzPos  = crntTrackerAzPos + delAz
            #newTrackerElPos  = crntTrackerElPos + delEl                
        
            if (newTrackerAzPos < 0): newTrackerAzPos += 360.0
            if (newTrackerElPos < 0): newTrackerElPos += 360.0           
        
            #------------------------------------------------
            # Check Delta Angles. This should be fairly small
            #------------------------------------------------
            if any([delAz>self.ctlFile['delAzHoldLim'],delEl>self.ctlFile['delElHoldLim']]):
                print "Delta Angles to move Sun to center of Aperature are larger than limits!!!!\n"
                print "Delta Az Angle = {}\n".format(delAz)
                print "Delta El Angle = {}\n\n".format(delEl)
                continue              
        
            #------------------------------
            # Point Tracker to new position
            #------------------------------
            self.pointTracker(newTrackerAzPos, newTrackerElPos, ElOffset=0.0, AzOffset=0.0)        
        
            testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
        
            #-------------------------------------------------------------
            # Check if findEllipse could not find the Sun or aperature. If
            # this is the case go back to seek loop and try moving Sun to 
            # center of CCD or waiting for Sun to re-appear
            #-------------------------------------------------------------
            if not testRtn: continue               
                           
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!               
            #----------------------------------------------------------------
            # Now that Sun is centered on aperture, start tracking velocities
            #----------------------------------------------------------------
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            while True:
                
                if guiFlg: skipMainLoopFlg = False
                
                calFlg = False
                #----------------------------------------------------
                # Calibration is run on an interval specified in the
                # control file. Determine if it's time to calibrate.
                #----------------------------------------------------
                crntT = dt.datetime.utcnow()
                if ((crntT - calTime).total_seconds() > self.ctlFile['calInterval']):
                    
                    #------------------------------------------------------
                    # Check TCP server is measurement is currently running.
                    # If so do not do a calibration, wait till measurement
                    # is done.
                    #------------------------------------------------------
                    if self.TCPflg:
                        measFlg = self.getParam("OPUS_STATUS")
                        if measFlg.upper() == "SCANNING": pass
                        else:
                            calFlg = True
                            self.stop_motion()
                            break
                    else:
                        calFlg = True
                        self.stop_motion()
                        break
                
                #-----------------------------------------------
                # Determine if close to Azimuth motor limits and 
                # if flip coordinates is necessary. If flip is
                # necessary break out of 
                #-----------------------------------------------
                prevState = self.cordFlp
                self.determine_flip()
                
                if self.cordFlp != prevState: 
                    self.stop_motion()
                    break
                
                #-----------------------------------------------
                # Check if El and Az velocity profiles have been 
                # calculated for the current day. These are in
                # absolute coordinates
                #-----------------------------------------------
                if crntT.day != prevDate.day:
                    prevDate = crntT
                    (sunAzVel,sunElVel,sunTimes) = sunAzElVel(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'],
                                                              dateT=prevDate,deltaT=self.ctlFile['deltaTsunEphem'],surfP=surfPres,surfT=surfTemp)                    
                               
                #--------------------------------------------------
                # Find the current azimuth and elevation velocities
                #--------------------------------------------------
                velInd = find_nearestInd(sunTimes,crntT)
                                
                #--------------------------------------------------------------------
                # Convert velocities from absolute coordinates to tracker coordinates
                # This gives abs value of velocity and direction (+/-)
                #--------------------------------------------------------------------
                (sunAzVelTrak,AzVelDir) = self.abs_to_tracker_velAz(sunAzVel[velInd])                
                (sunElVelTrak,ElVelDir) = self.abs_to_tracker_velEl(sunElVel[velInd])

                #-----------------------------------------------------------------
                # Determine Sun offset from aperture to find correcting velocities
                #---------------------------------------------------
                # Find delta pixels between Sun center and Aperature
                #---------------------------------------------------
                testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
            
                #-------------------------------------------------------------
                # Check if findEllipse could not find the Sun or aperature. If
                # this is the case go back to seek loop and try moving Sun to 
                # center of CCD or waiting for Sun to re-appear
                #-------------------------------------------------------------
                if not testRtn: 
                    self.stop_motion()
                    break
                    
                #-------------------------------------
                # Convert delta pixels to delta angles
                #-------------------------------------
                newAngles = self.pixel_to_angle(self.delX, self.delY)
                delAz     = newAngles[0] 
                delEl     = newAngles[1]                
                
                #------------------------------------------------
                # Check Delta Angles. This should be fairly small
                #------------------------------------------------
                if any([delAz>self.ctlFile['delAzHoldLim'],delEl>self.ctlFile['delElHoldLim']]):
                    print "Delta Angles to move Sun to center of Aperature are larger than limits!!!!\n"
                    print "Delta Az Angle = {}\n".format(delAz)
                    print "Delta El Angle = {}\n\n".format(delEl)
                    self.stop_motion()
                    break                     
                
                #---------------------------------------------
                # Determine delta angular velocity corrections
                # These are in tracker coordinates
                #---------------------------------------------
                delAzVel = delAz / self.ctlFile['holdSunInt']
                delElVel = delEl / self.ctlFile['holdSunInt']
                                
                print "Delta AzVel = {0:}".format(delAzVel)
                print "Delta ElVel = {0:}".format(delElVel)
                #--------------------------------------------
                # Add velocity correction to ephem velocities
                #--------------------------------------------
                newAzVel = sunAzVelTrak*AzVelDir + delAzVel
                newElVel = sunElVelTrak*ElVelDir + delElVel
                
                print "New Az Velocity Before = {}".format(newAzVel)
                print "New El Velocity Before = {}".format(newElVel)
                
                (newAzVel,newAzVelDir) = self.determine_velDir(newAzVel)
                (newElVel,newElVelDir) = self.determine_velDir(newElVel)
                
                print "New Az Velocity After = {}".format(newAzVel)
                print "New El Velocity After = {}".format(newElVel)                
                #--------------------------------------------------------------------
                # Check if corrected velocity changes sign compared to ephem velocity
                # This would indicate that the velocity correction is larger than
                # the ephem and in opposite direction. Since we don't want to stop
                # the motor and change direction, just reduce the ephem velocity
                # by 80%
                #--------------------------------------------------------------------
                if newAzVelDir != AzVelDir: 
                    newAzVel    = sunAzVelTrak * 0.2
                    newAzVelDir = AzVelDir
                if newElVelDir != ElVelDir: 
                    newElVel    = sunElVelTrak * 0.2
                    newElVelDir = ElVelDir
                                
                #----------------------------------
                # Determine if motors are in motion
                # 1 (True)  = motion done
                # 0 (False) = motion in progress
                # If motors not in motion initiate
                # indefinte motion
                #----------------------------------
                if (self.det_motion(axis=self.ctlFile["AzAxis"]) > 0.0):  # Motors in motion
                    
                    #----------------------------------------------
                    # Check if new El direction is same as previous
                    #----------------------------------------------
                    if newElVelDir == prevElDir:
                        #------------------------------------
                        # Set velocities of indefinite motion
                        #------------------------------------
                        self.set_dualVel(newAzVel, newElVel, self.ctlFile['AzAxis'], self.ctlFile['ElAxis'])                          

                    else:
                        self.stop_motion(axis=None)
                        
                        prevElDir = newElVelDir
                    
                        if newAzVelDir > 0.: AzDir = "+"
                        else:                AzDir = "-"
                        if newElVelDir > 0.: ElDir = "+"
                        else:                ElDir = "-"                    
                    
                        #------------------------------------
                        # Set velocities of indefinite motion
                        #------------------------------------
                        self.set_dualVel(newAzVel, newElVel, self.ctlFile['AzAxis'], self.ctlFile['ElAxis'])                    
                    
                        #-------------
                        # Start motion
                        #-------------
                        self.move_indefinite(self.ctlFile["AzAxis"], AzDir, self.ctlFile["ElAxis"], ElDir)
                
                else:  # Motors are stopped
                    prevElDir = newElVelDir
                    
                    if newAzVelDir > 0.: AzDir = "+"
                    else:                AzDir = "-"
                    if newElVelDir > 0.: ElDir = "+"
                    else:                ElDir = "-"                    
                    
                    #------------------------------------
                    # Set velocities of indefinite motion
                    #------------------------------------
                    self.set_dualVel(newAzVel, newElVel, self.ctlFile['AzAxis'], self.ctlFile['ElAxis'])                    

                    #-------------
                    # Start motion
                    #-------------
                    self.move_indefinite(self.ctlFile["AzAxis"], AzDir, self.ctlFile["ElAxis"], ElDir)
                
                #-----------------------------------------
                # If in GUI mode return control to the GUI
                #-----------------------------------------
                if guiFlg: return calTime
                
                #----------------------------
                # Recalculate every N seconds
                #----------------------------
                sleep(self.ctlFile['holdSunInt'])
                
                #--------------------------------------------------------------------
                # Find difference between Sun and Aperture for logging and statistics
                #---------------------------------------------------
                # Find delta pixels between Sun center and Aperature
                #---------------------------------------------------
                testRtn = self.findEllipseN(aptFlg=True,N=self.ctlFile['ellipseN'])
            
                #-------------------------------------------------------------
                # Check if findEllipse could not find the Sun or aperature. If
                # this is the case go back to seek loop and try moving Sun to 
                # center of CCD or waiting for Sun to re-appear
                #-------------------------------------------------------------
                if not testRtn: 
                    self.stop_motion()
                    break
                    
                #----------------------------------
                # Print track information to stdout
                #----------------------------------
                print "-"*42
                print "* {0:7.2f} {1:7.2f} {2:7.2f} {3:7.2f} {4:7.2f}".format(self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.area_apt)
                print "-"*42                        
                    
                #---------------------------------------------
                # Log data related to finding sun and aperture
                #---------------------------------------------
                self.logSunAngle(sunEl,sunAz)
                self.logSunPix("YESAPT")

                #---------------------------------------------
                # Send information to the TCP server regarding 
                # offset angles, sun radiance, etc
                #-----------------------------------------------
                # Tracker is locked on Sun send OK to TCP server
                #-----------------------------------------------
                if self.TCPflg: 
                    #dateTstr = "{0:}{1:02}{2:02}_{3:02}{4:02}{5:02}".format(crntDateTime.year,crntDateTime.month,crntDateTime.day,crntDateTime.hour,
                                                                            #crntDateTime.minute,crntDateTime.second)
                    #self.setParam("TRACKER_TS " + dateTstr)                        
                    self.setParam("TRACKER_STATUS LOCK")
                    if self.cordFlp: self.setParam("TRACKER_ELMIRROR FLIP")
                    else:            self.setParam("TRACKER_ELMIRROR NOMINAL")                    
                             
                #----------------------------------
                # Print track information to stdout
                #----------------------------------
                print "  {0:7.2f} {1:7.2f} {2:7.2f} {3:7.2f} {4:7.2f}".format(self.delX,self.delY,self.sunPixMean/255.0,self.area_sun,self.area_apt)

        return True
           
        
if __name__ == "__main__":
    
    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    try:
        ctlFile  = sys.argv[1]
    except:
        ctlFile  = "/home/tabftir/remote/ops/thule_trackerCtl.py"

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile,exitFlg=True)

    #-------------------------
    # Import ctlFile variables
    #-------------------------
    cltFvars = ctlFileInit(ctlFile)
    
    #-----------------------
    # Initiate tracker class
    #-----------------------
    tracker1 = TrackerNCAR(ctlFile,TCPflg=True)
    
    #---------------------------------------------
    # Initialize camera and controller for tracker
    #---------------------------------------------
    tracker1.initializeTracker()

    #------------
    # Run tracker
    #------------
    while True:
        try:
            tracker1.track(surfPres=cltFvars["presDefault"],surfTemp=cltFvars["tempDefault"])
        except SystemExit:
            sys.exit()
        except ValueError:
            try: tracker1.initializeTracker()
            except: continue
            continue
