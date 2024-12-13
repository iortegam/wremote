#----------------------------------------------------------------------------------------
# Name:
#        thule_trackerCtl.py
#
# Purpose:
#       This file contains input parameters for the controlling the sun tracker
#
#
#
# Notes:
#       1) 
#
#
# License:
#    Copyright (c) 2013-2014 NDACC/IRWG
#    This file is part of CST (Community Solar Tracker).
#
#    CST is free software: you can redistribute it and/or modify
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


#-------------------------
# Site location parameters
#--------------------------------------------------------------------------
# lat         - Latitude of site (Deg N)
# lon         - Longitude of site (Deg E)
# elevation   - Elevation of site (m)
# presDefault - Default surface pressure (mBar)
# tempDefault - Default surface temperature (deg C)
# minElAngle  - Minimum Elevation angle in which to initiate tracking [deg]
#--------------------------------------------------------------------------
lat         = 76.52
lon         = 291.23
elevation   = 225.0
presDefault = 995.0
tempDefault = 0.0
minElAngle  = 10.0


baseDataDir = "/home/tabftir/daily/"

#----------------
# Misc Parameters
#----------------------------------------------------------------------------
# AzDeltaEp     -  Azimuth angle amount from software limit before coordinate
#                  flip is initiated
# ElOffSet      -  Elevation off set in degrees. Assuming the tracker is not 
#                  perfectly aligned.
# AzOffSet      -  Azimuth off set in degrees. Assuming the tracker is not 
#                  perfectly aligned.
# ephemUpdate   -  Number of seconds to wait to update tracker position based
#                  on ephemeris data. Used when dome is closed.
#----------------------------------------------------------------------------
AzDeltaEp   = 0.0
ElOffSet    = -0.1
AzOffSet    = -39.17
ephemUpdate = 30.0

#----------------------
# Center Sun Parameters
#---------------------------------------------------------------------------------------------
# optMethod         - Optimization method for moving Sun to center of CCD and aligning
#                     with aperature.
#      Method 1 -- BFGS Algorithm
#      Method 2 -- L-BFGS Algorithm
#      Method 3 -- Nelder-Mead Algorithm
#      Method 4 -- Powell Algorithm                
# optTol            - Optimization tolerance (Note: This value has different meaning for 
#                     different routines)
# calInterval       - Time between calibrations for mapping pixel coordinates to motor angle
#                     coordinates (seconds)
# waitTrckInt       - Time to wait before checking whether to track again [seconds]
# noSunSleep        - Sleep time before trying to find Sun again (seconds)
# holdSunInt        - Interval to recalculate position of hold (seconds)
#---------------------------------------------------------------------------------------------
optMethod        = 3
optTol           = 0.2
optEpsilon       = 0.005
calInterval      = 3600.0
waitTrckInt      = 5.0
noSunSleep       = 1.0
holdSunInt       = 0.5
AzOptBound       = 0.5
ElOptBound       = 0.5

#------------------------------------------
# Newport ESP301 Motion Controller Settings
#------------------------------------------------------------------------------------
# ESPserialPort     - Serial port ESP301 is connected to
# ESPserialBaudrate - Baud rate for serial connection to ESP
# ESPreadTO         - Number of seconds to listen for output from ESP before time-out
#------------------------------------------------------------------------------------
ESPserialPort     = '/dev/ttyS0'        
ESPserialBaudrate = 19200               
ESPreadTO         = 600                  

#----------------------------
# TCP Data server information
#----------------------------
FTS_DataServ_IP    = "192.168.1.100"
FTS_DataServ_PORT  = 5555
FTS_DATASERV_BSIZE = 4024

#-----------------
# Email parameters
#---------------------------------------------------------------
# emailFlg    -- Flag whether to send emails for critical errors
# FromEmail   -- Address email looks like it is sent form
# toEmail     -- Address(s) email is sent to
#---------------------------------------------------------------
emailFlg  = True
FromEmail = "tabftir@thule"
toEmail   = ["jamesw@ucar.edu"]

#------------------------------------------
# Settings for Azimuth and Elevation Motors
#-------------------------------------------------------------------------------
# AzSoftTravelLim - Software travel limit for azimuth motor set as (+/- Degrees) 
# AzAxis          - Axis number on ESP301 for Azimuth motor
# ElAxis          - Axis number on ESP301 of Elevation motor
# AzJogStep       - Amount to jog tracker in Azimuth if sun is not found [Deg]
# ElJogStep       - Amount to jog tracker in Elevation if sun is not found [Deg]
# ellipseN        - Number of ellipse to take average of to find Sun/Aperature
# FastAccelAxis1  - Acceleration of motor on axis 1 for callibrating and putting 
#                   Sun in center of CCD
# FastAccelAxis1  - Acceleration of motor on axis 2 for callibrating and putting 
#                   Sun in center of CCD
# SlowAccelAxis1  - Acceleration of motor on axis 1 for holding Sun on aperature
# SlowAccelAxis2  - Acceleration of motor on axis 2 for holding Sun on aperature
#-------------------------------------------------------------------------------
AzSoftTravelLim = 172.0
AzAxis          = 1
ElAxis          = 2
AzJogStep       = 0.05
ElJogStep       = 0.05
ellipseN        = 3
AzHome          = 24.0
ElHome          = 90.0
FastAccelAxis1  = 4.0
FastAccelAxis2  = 40.0
SlowAccelAxis1  = 0.1
SlowAccelAxis2  = 0.1
FastJerkAxis1   = 16.0
FastJerkAxis2   = 160.0
SlowJerkAxis1   = 0.5
SlowJerkAxis2   = 10.0
NominalVelAxis1 = 10.0 #???????????
NominalVelAxis2 = 10.0 #???????????
deltaTsunEphem  = 60


#------------------------
# Settings for USB camera
#-------------------------------------------------------------------------------
# devLoc         - Device number for the camera. Typically 0 if only one camera connected
# xPix           - Number of pixels in the x-direction of camera
# yPix           - Number of pixesl in the y-direction of camera
# FromEmail      - Email address of sender for SMTP
# toEmail        - Email address of reciepient for SMTP
# targetContrast - Ideal contrast (std of pixels)
# contrastU      - Upper limit of contrast
# contrastL      - Lower limit of contrast
#-------------------------------------------------------------------------------
devLoc         = "/dev/video0"
xPix           = 1280
yPix           = 960
targetContrast = 0
contrastU      = 0
contrastL      = 0

#-------------------------------------
# Settings for processing camera image
#------------------------------------------------------------------------------------------
# thresType          - Method for thresholding camera image
#                       0 - Simple binary threshold
#                       1 - Adaptive threshold (Gaussian) with Gaussian Blur
#                       2 - Adaptive threshold (Mean) with Gaussian Blur
#                       3 - Binary threshold (OTSU) with Gaussian Blur
# delAzSeekLim       - Upper limit of the angle that the tracker must move to center
#                      the sun on CCD (Azimuth Angle). This depends on the alignment
#                      of the tracker.
# delElSeekLim       - Upper limit of the angle that the tracker must move to center
#                      the sun on CCD (Elevation Angle). This depends on the alignment
#                      of the tracker.
# delAzHoldLim       - Upper limit of the angle that the tracker must move to center
#                      the sun on aperature (Azimuth Angle). This should be small, if
#                      the aperature is close to the center of the CCD.
# delElHoldLim       - Upper limit of the angle that the tracker must move to center
#                      the sun on aperature (Elevation Angle). This should be small, if
#                      the aperature is close to the center of the CCD.
# AptFltrType        - Method in which to filter aperature contours
#                       1 - Filter aperature contours by mean pixel intensity 
#                           looks for minimum value of mean pixel intensity
#                       2 - Filter aperature contours by minimum distance of
#                           contour center to center of CCD
# imgThreshold       - if thresType = 0, then this is the threshold value
# FilterAreaDetSize  - This is the approximate size of detector. Typically the contour
#                      rountine picks up the entire detector as a contour. This value 
#                      is used to filter that contour out.
# FilterAreaMinApt   - Minimum pixel area for aperature
# FilterAreaMaxApt   - Maximum pixel area for aperature
# AzimuthCalStep     - Step size for Azimuth motor for calibration (deg)
# ElevationCalStep   - Step size for Elevation motor for calibration (deg)
# minSunPixMean      - Minimum value of the mean pixel intensity of sun countour. Used
#                      to determine if Sun is detected.
# minSunPixArea      - Minimum pixel area to for Sun to be 'detected'
# aptXpixOffset      - Pixel distance of aperature center and center of CCD in X direction:
#                      CCD_Xcenter - Apt_Xcenter
# aptYpixOffset      - Pixel distance of aperature center and center of CCD in Y direction:
#                      CCD_Ycenter - Apt_Ycenter
#------------------------------------------------------------------------------------------
thresType         = 3
delAzSeekLim      = 2.0
delElSeekLim      = 2.0
delAzHoldLim      = 0.5
delElHoldLim      = 0.5
AptFltrType       = 1
imgThreshold      = 128
FilterAreaDetSize = 1000000.0 
FilterAreaMinApt  = 100.0
FilterAreaMaxApt  = 20000.0
AzimuthCalStep    = 0.05
ElevationCalStep  = 0.05
minSunPixMean     = 50.0  #150.0
minSunPixArea     = 20000.0 # ?????
aptXpixOffset     = -15.0 
aptYpixOffset     = 2.0  

