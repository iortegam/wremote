#----------------------------------------------------------------------------------------
# Name:
#        usbCam.py
#
# Purpose:
#       This file contains class to interact with USB camera
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
import cv2
import sys
import Image
import time
import select
import smtplib
import numpy               as     np
import datetime            as     dt
import v4l2capture         as     vc
import scipy.optimize      as     so
from trackerUtils          import *
from remoteData            import FTIRdataClient
from email.mime.text       import MIMEText
from email.mime.multipart  import MIMEMultipart
from email.mime.image      import MIMEImage

    #---------#
    # Classes #
    #---------#


class SunCam(FTIRdataClient):

    def __init__(self, ctlFile,TCPflg=False):
        
        self.ctlFile     = ctlFile
        self.img         = False
        self.emailFlg    = self.ctlFile['emailFlg']
        self.setExposure = False
        self.img_array   = False
        self.sunFound    = False        
        FTIRdataClient.__init__(self,TCP_IP=self.ctlFile["FTS_DataServ_IP"],
                                TCP_Port=self.ctlFile["FTS_DataServ_PORT"],BufferSize=self.ctlFile["FTS_DATASERV_BSIZE"])
          
    def connectCam(self,TCPflg=False):
        ''' Initalize the camera and set image size'''
        #--------------------------
        # Open connection to camera
        #--------------------------
        self.cam = False
        
        try:
            self.cam = vc.Video_device(self.ctlFile['devLoc'])
            
            #----------------------------------------------
            # Set size of image to be retrieved from Camera
            # Another size may be returned if not supported
            #----------------------------------------------
            self.xSize, self.ySize = self.cam.set_format(self.ctlFile['xPix'],self.ctlFile['yPix'])      
            
            #-----------------------------------
            # Create a buffer to store the image
            #-----------------------------------
            self.cam.create_buffers(1)    
            
            #-----------------
            # Start the camera
            #-----------------
            self.cam.start()               
            
        except:
            #--------------------------------------------------------
            # If unable to connect to the camera log a critical error
            # and send an email indicating connection error
            #--------------------------------------------------------
            if TCPflg: self.camCriticalErr()
            
    def camCriticalErr(self):
        #-------------------------------------------------------
        # Camera critical error: Unable to connect to USB camera
        #-------------------------------------------------------
        toemails = [onemail for onemail in self.ctlFile["Email_to"].strip().split(",")]
    
        msg = MIMEText("Unable to connect to USB camera at {} UTC".format(dt.datetime.utcnow())) 
        msg['Subect'] = "USB Camera Critical Error!"
        msg['From']   = self.ctlFile['Email_from']
        msg['To']     = self.ctlFile['Email_to']            
    
        s = smtplib.SMTP('localhost')
        s.sendmail(self.ctlFile['Email_from'], toemails, msg.as_string())
        s.quit()           
        
    def captureImg(self,setExp=False):
        ''' This gets an image from the camera'''
        
        img      = None
        
        #--------------------------------
        # Open connection to video device
        #--------------------------------
        #self.connectCam()
        
        try:
            #----------------------------------
            # Set absolute exposure if prompted
            #----------------------------------
            if setExp: self.cam.set_exposure_absolute(setExp)
                                 
            #----------------------
            # Send buffer to camera
            #----------------------
            self.cam.queue_all_buffers()
            
            #-------------------------------
            # Wait for camera to fill buffer
            #-------------------------------
            select.select((self.cam,),(),())
            
            #-----------------------------
            # Get image data and timestamp
            #-----------------------------
            img         = self.cam.read()
            #print "Size of img = {}\n".format(len(img))
            self.img_TS = dt.datetime.now()
            
            #-------------------------------------------------------------
            # Convert raw image data (string)to image. 'L' is hardcoded to 
            # convert to a gray scale image. This is a PIL image... not 
            # compatible with opencv.
            #-------------------------------------------------------------
            self.img = Image.fromstring("L",(self.xSize,self.ySize),img)
            #self.img = self.img.convert("L")
                
            #----------------------------------------
            # Convert to Numpy array for manipulation
            #----------------------------------------
            self.img_np = np.array(self.img)
            
        except:
            #self.camClose()
            print  sys.exc_info()     
            
        #---------------------------
        # Close connection to camera
        #---------------------------
        #self.camClose()
        
        
    def camClose(self):
        '''Close connection to camera'''
        try:
            self.cam.close()
            del(self.cam)
        except:
            print 'No USB camera connected to close\n'
                        
    def saveImg(self,imgDname):
        '''Save captured image and email image if prompted'''
    
        #---------------------------------------
        # Check directory for writing image file
        #---------------------------------------
        ckDir(imgDname)
        
        #----------------
        # Save image file
        #----------------
        if not(imgDname.endswith('/')): imgDname = imgDname + '/'
        imgFname = imgDname + 'camImage_{:%Y%m%d_%H%M%S}'.format(self.img_TS) + '.jpg'
        self.img.save(imgFname)
        
        #------------------------
        # Email image if prompted
        #------------------------
        if self.emailFlg:
            toemails = [onemail for onemail in self.ctlFile["toEmail"].strip().split(",")]
            msg = MIMEMultipart()
            msg['Subect'] = 'Cam Tracker image from {}'.format(self.img_TS)
            msg['From']   = self.ctlFile['Email_from']
            msg['To']     = self.ctlFile['Email_to']            
            img           = MIMEImage(self.img)
            msg.attach(img)
            
            s = smtplib.SMTP('localhost')
            s.sendmail(self.ctlFile['FromEmail'], toemails, msg.as_string())
            s.quit()        
        
    def calibrateExposure(self):
        '''Calibrate exposure based on configuration file settings'''
        
        #------------------------------
        # Get current value of exposure
        #------------------------------
        self.exposureInit = self.cam.get_exposure_absolute()
        
        #------------------------------------------------
        # Adjust exposure to reach desired contrast level
        #------------------------------------------------
        bananna = lambda x: self.contrastFunc(x) - self.ctlFile['targetContrast']
        
        optCon  = so.fmin(bananna,x0=self.exposureInit,full_output=True)
        warnFlg = optCon[4]
        expCal  = optCon[0][0]
        
        #------------------
        # No solution found
        #------------------
        if warnFlg > 0:
            self.setExposure = self.exposureInit
        
        elif (expCal > self.ctlFile['contrastU']) or (expCal < self.ctlFile['contrastL']):
            self.setExposure = self.exposureInit
            
        else: 
            self.setExposure = optCon[0][0]
    
    
    def contrastFunc(self,ExpVal):
        '''Functional definition to return std of captured image using specified absolute exposure'''
        
        #--------------------------------------------
        # Grab image using specific absolute exposure
        #--------------------------------------------
        self.captureImg(ExpVal,setExp=False)
        
        #-------------------------------
        # Return STD of image (contrast)
        #-------------------------------
        return np.std(self.img_np)
    
    def findEllipseN(self,aptFlg=False,N=1,pause=False,TCPflg=False):
        ''' Do N iterations of findEllipse. This is used to filter any noise'''
        delX      = np.zeros(N)
        delY      = np.zeros(N)
        x_sun     = np.zeros(N)
        y_sun     = np.zeros(N)
        rad_sun   = np.zeros(N)
        area_sun  = np.zeros(N)     
        dist      = np.zeros(N)     
        
        if aptFlg:
            x_apt    = np.zeros(N)
            y_apt    = np.zeros(N)
            rad_apt  = np.zeros(N)
            area_apt = np.zeros(N)
            
        for i in range(0,N):
            if pause: time.sleep(pause)
            
            ellipseRtn  = self.findEllipse(aptFlg=aptFlg,TCPflg=TCPflg)
            
            #-------------------------------------------
            # Check if findEllipse failed to find either
            # Sun or aperature
            #-------------------------------------------
            if ellipseRtn is False: return False
            
            dist[i]      = ellipseRtn
            delX[i]      = self.delX
            delY[i]      = self.delY
            x_sun[i]     = self.x_sun
            y_sun[i]     = self.y_sun
            rad_sun[i]   = self.rad_sun
            area_sun[i]  = self.area_sun      
                        
            if aptFlg:
                x_apt[i]    = self.x_apt
                y_apt[i]    = self.y_apt
                rad_apt[i]  = self.rad_apt
                area_apt[i] = self.area_apt
        
        self.delX     = np.mean(delX)
        self.delY     = np.mean(delY)
        self.x_sun    = np.mean(x_sun)
        self.y_sun    = np.mean(y_sun)
        self.rad_sun  = np.mean(rad_sun)
        self.area_sun = np.mean(area_sun)
        self.dist     = np.mean(dist)
        
        if aptFlg:
            self.x_apt    = np.mean(x_apt)
            self.y_apt    = np.mean(y_apt)
            self.rad_apt  = np.mean(rad_apt)
            self.area_apt = np.mean(area_apt)            
        
        return self.dist
            
    def findEllipse(self,aptFlg=False,TCPflg=False):
        '''Thresholds the image and finds contours'''
        
        #---------------------
        # Reset Sun found flag
        #---------------------
        self.sunFound = False
    
        #--------------------------
        # Capture image from camera
        #--------------------------
        self.captureImg()
    
        #---------------------------
        # Timestamp of image capture
        #---------------------------
        self.imgTime = dt.datetime.utcnow()
    
        #----------------------------------------------------
        # Threshold image. Do two thresholds. One to find the 
        # aperature and one to find the Sun
        #----------------------------------------------------
        #if   self.ctlFile['thresType'] == 0:
            #ret, thres = cv2.threshold(self.img_np,self.ctlFile['imgThreshold'],255,cv2.THRESH_BINARY)
    
        #elif self.ctlFile['thresType'] == 1:
            #blur  = cv2.GaussianBlur(self.img_np,(15,15),0)
            #thres = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
    
        #elif self.ctlFile['thresType'] == 2:
            #blur  = cv2.GaussianBlur(self.img_np,(15,15),0)
            #thres = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
    
        #elif self.ctlFile['thresType'] == 3:
            #blur      = cv2.GaussianBlur(self.img_np,(15,15),0)
            #ret,thres = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)        
    
        blur         = cv2.GaussianBlur(self.img_np,(15,15),0)
        ret,thresSun = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thresApt     = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
    
        #cv2.imwrite("/home/tabftir/imageSun.jpg",thresSun)
        #cv2.imwrite("/home/tabftir/imageApt.jpg",thresApt)
        
        #--------------
        # Find contours
        #--------------
        #kernel              = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        #res                 = cv2.morphologyEx(thres,cv2.MORPH_OPEN,kernel)
        contoursSun, hierarchy = cv2.findContours(thresSun,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)   
        contoursApt, hierarchy = cv2.findContours(thresApt,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        #contours  = cv2.HoughCircles(thres,cv2.cv.CV_HOUGH_GRADIENT,1,2.0,param1=self.ctlFile['HoughParam1'],param2=self.ctlFile['HoughParam2'],
                        #minRadius=self.ctlFile['HoughMinRad'],maxRadius=self.ctlFile['HoughMaxRad'] )        
    
        #----------------------
        # Sort contours by area
        #----------------------
        contoursSun = sorted(contoursSun, key=cv2.contourArea, reverse=True)
        contoursSun = np.array(contoursSun)
    
        contoursApt = sorted(contoursApt, key=cv2.contourArea, reverse=True)
        contoursApt = np.array(contoursApt)        
    
        #----------------------
        # Find area of contours
        #----------------------
        contAreaSun = np.array([cv2.contourArea(c) for c in contoursSun])
        contAreaApt = np.array([cv2.contourArea(c) for c in contoursApt])
    
        #--------------------------
        # Filter out bogus contours
        #--------------------------        
        #-----------------------------------------------
        # cv2.contours usually picks up the contour of
        # the entire frame. Filter out contour which have
        # areas close to detector size. For DMK 23U445
        # 1280x960 = 1,228,800 (use 1,000,000)
        #-----------------------------------------------
        rmind       = np.where(contAreaSun > self.ctlFile['FilterAreaDetSize'])[0]
        if rmind:
            contoursSun = np.delete(contoursSun,rmind,axis=1)
            contAreaSun = np.delete(contAreaSun,rmind,axis=1)        
    
        #-----------------------------------------------------
        # Determine where we expect the aperature to be. This
        # is close to the center of the CCD with an offset due
        # to not being able to fully adjust the camera
        #-----------------------------------------------------
        self.xCenter  = self.xSize/2.0
        self.yCenter  = self.ySize/2.0        
        self.xCenter -= self.ctlFile["aptXpixOffset"]
        self.yCenter -= self.ctlFile["aptYpixOffset"]
    
        #---------------
        # Search for Sun        
        #-------------------------------------------
        # Largest contour area assumed to be the sun
        # This may not be true if the sun is only
        # partially illuminating the aperature wheel
        #-------------------------------------------
        sunInd               = np.argmax(contAreaSun)
        self.sunContour      = contoursSun[sunInd]
        
        #-----------------------------------------------
        # Test to see if Sun is visible. If not 
        # something is wrong (i.e. Sun has been blocked)
        #-----------------------------------------------        
        try:
            sunCenter, sunRadius = cv2.minEnclosingCircle(self.sunContour)
        except:
            print "Sun is not visible!!!"
            return False
        
        self.x_sun           = sunCenter[0]
        self.y_sun           = sunCenter[1]
        self.rad_sun         = sunRadius 
        self.area_sun        = np.pi * sunRadius**2
    
        #----------------------------------------
        # Convert sunRadius and center points to 
        # integers for cv2 circle drawing routine
        #----------------------------------------
        sunRadius = int(np.round(sunRadius))
        sunCenter = (int(np.round(sunCenter[0])),int(np.round(sunCenter[1])))
    
        #------------------------------------------------
        # Find mean pixel intensity and the area within 
        # Sun contour to determine if Sun is found
        #------------------------------------------------
        mask = np.zeros(self.img_np.shape,np.uint8)
        cv2.circle(mask,sunCenter,sunRadius,255,-1)
        self.sunPixMean = cv2.mean(self.img_np,mask=mask)[0]
    
        if (self.sunPixMean >= self.ctlFile['minSunPixMean']): 
            if (self.area_sun >= self.ctlFile['minSunPixArea']): self.sunFound = True
            else: 
                #crntT = dt.datetime.utcnow()
                #cv2.imwrite("/home/tabftir/imageSun.jpg",thresSun)
                #cv2.imwrite("/home/tabftir/Sunfit.jpg",mask)                
                #if TCPflg: self.writeCameraErr("1 {} /home/tabftir/imageSun.jpg /home/tabftir/Sunfit.jpg".format(crntT))
                print "Unable to find Sun"
                return False
    
        #---------------------
        # Search for Aperature
        #---------------------
        if aptFlg:
            #----------------------------------------
            # Search for aperature:
            # Filter contours based on largest and
            # smallest possible aperature size
            #----------------------------------------
            rmind1 = np.where(contAreaApt < self.ctlFile['FilterAreaMinApt'])[0] 
            rmind2 = np.where(contAreaApt > self.ctlFile['FilterAreaMaxApt'])[0]
            rmind  = np.union1d(rmind1,rmind2)
        
            contoursApt = np.delete(contoursApt,rmind)
            contAreaApt = np.delete(contAreaApt,rmind) 
        
            #--------------------------------------
            # Aperature should be close to a circle
            # therefore we fit a circle
            #--------------------------------------
            aptCenterPnts = []
            aptAreas      = []
            aptRad        = []
            aptMeanInt    = []

            for singCon in contoursApt:
                
                #-----------------------------------------------
                # Test to see if aperature is visible. If not 
                # something is wrong (i.e. Sun has been blocked)
                #-----------------------------------------------
                try:
                    center, radius = cv2.minEnclosingCircle(singCon)
                except:
                    #crntT = dt.datetime.utcnow()
                    #cv2.imwrite("/home/tabftir/imageApt2.jpg",thresApt)              
                    #if TCPflg: self.writeCameraErr("2 {} /home/tabftir/imageApt2.jpg".format(crntT))   
                    print "Unable to find Aperature"
                    return False
                
                aptCenterPnts.append(center)
                aptRad.append(radius)
                aptAreas.append(np.pi*radius**2)
                
                #----------------------------------------------------------
                # Find mean pixel intensity and the area within 
                # aperature contour to help determine if aperature is found
                #----------------------------------------------------------
                aptCentInt = (int(np.round(center[0])),int(np.round(center[1])))
                aptRadInt  = int(np.round(radius))
                mask       = np.zeros(self.img_np.shape,np.uint8)
                cv2.circle(mask,aptCentInt,aptRadInt,255,-1)
                aptMeanInt.append(cv2.mean(self.img_np,mask=mask)[0]) 
        
            aptAreas   = np.array(aptAreas)
            aptMeanInt = np.array(aptMeanInt)
            
            #--------------------------------------------------
            # Find the fitted circle with the area closest to 
            # aperature area (for specific filter) specified in
            # the ctl file
            #--------------------------------------------------
            #-----------------------------------------------------
            # The aperature should be close to center of the image
            # If center of aperature is off from the center of the 
            # image by a certain amount than try another
            #-----------------------------------------------------        
            while True:
                if len(aptAreas) == 0:
                    #crntT = dt.datetime.utcnow()
                    #cv2.imwrite("/home/tabftir/imageApt3.jpg",mask)              
                    #if TCPflg: self.writeCameraErr("3 {} /home/tabftir/imageApt3.jpg".format(crntT)) 
                    print "No suitable aperature found"
                    return False
        
                if   self.ctlFile['AptFltrType'] == 1:
                    indApt = aptMeanInt.argmin()
                elif self.ctlFile['AptFltrType'] == 2:
                    indApt = (np.sqrt((self.xCenter-aptCenterPnts[:][0])**2 + (self.yCenter-aptCenterPnts[:][1])**2)).argmin()
            
                dist = np.sqrt((self.xCenter-aptCenterPnts[indApt][0])**2 + (self.yCenter-aptCenterPnts[indApt][1])**2)
        
                #-------------------------------
                # Test distance if within limits
                #-------------------------------
                if dist < (0.3*np.min([self.xCenter,self.yCenter])): 
                    self.x_apt    = aptCenterPnts[indApt][0]
                    self.y_apt    = aptCenterPnts[indApt][1]
                    self.rad_apt  = aptRad[indApt]
                    self.area_apt = aptAreas[indApt]
                    break
                else:
                    aptAreas      = np.delete(aptAreas,indApt)
                    aptCenterPnts = np.delete(aptCenterPnts,indApt,axis=0)
                    aptMeanInt    = np.delete(aptMeanInt,indApt)
        
            #----------------------------------------------
            # Find distance between center of aperature and 
            # center of sun spot
            # Defined as: Aperature (x,y) - Sun Spot (x,y)
            #----------------------------------------------
            self.delX = self.x_apt - self.x_sun
            self.delY = self.y_apt - self.y_sun
        
        #-------------------------------------------------
        # If not detecting aperature look for 
        # the delta distance between sun and center of CCD
        #-------------------------------------------------
        else:
            #---------------------------------------------
            # Find distance between center of sun spot and 
            # where we except the aperature to be 
            #---------------------------------------------
            self.delX = self.xCenter - self.x_sun
            self.delY = self.yCenter - self.y_sun           
        
        #--------------------------------------------
        # Find total distance sqrt(delX**2 + delY**2)
        #--------------------------------------------
        self.dist = np.sqrt(self.delX**2 + self.delY**2)
            
        #--------------------------------------------------------------
        # Draw circles around Sun spot and aperature (if aptFlg = True)
        #--------------------------------------------------------------
        cv2.circle(self.img_np,sunCenter,sunRadius,(255,255,255),2)
        if aptFlg: cv2.circle(self.img_np,(int(np.round(self.x_apt)),int(np.round(self.y_apt))),
                                          int(np.round(self.rad_apt)),(255,255,255),2)
        
        #--------
        # Testing
        #--------
        #cv2.imwrite('/home/tabftir/imageSunApt.jpg',self.img_np)
        
        #----------------------------------------
        # Return the length of the vector between 
        # the sun center and either aperature or 
        # center of CCD
        #----------------------------------------
        #print "CCD center: x-pixel = {0:}, y-pixel = {1:}\n".format(self.xCenter,self.yCenter)
        #print "Pixel Area of Sun = {}\n".format(self.area_sun)
        #print "Intensity of Sun  = {}\n".format(self.sunPixMean)
        #print "Sun center: x-pixel = {0:}, y-pixel = {1:}\n".format(self.x_sun,self.y_sun)
        #if aptFlg:
            #print "Aperature center: x-pixel = {0:}, y-pixel = {1:}\n".format(self.x_apt,self.y_apt)
            #print "Aperature area = {}".format(self.area_apt)
            #print "Pixel distance between Sun and aperature  = {}\n\n".format(np.sqrt(self.delX**2 + self.delY**2))
        #else:
            #print "Pixel distance between Sun and center of CCD  = {}\n\n".format(np.sqrt(self.delX**2 + self.delY**2))
            
        return self.dist
            
    def findJustApt(self):
        '''Find Just the aperature and give size and offset from center of CCD'''
        
        #--------------------------
        # Capture image from camera
        #--------------------------
        self.captureImg()
    
        #---------------------------
        # Timestamp of image capture
        #---------------------------
        self.imgTime = dt.datetime.utcnow()
    
        #----------------------------------------------------
        # Threshold image. Do two thresholds. One to find the 
        # aperature and one to find the Sun
        #----------------------------------------------------      
        blur         = cv2.GaussianBlur(self.img_np,(15,15),0)
        thresApt     = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
    
        #cv2.imwrite("/home/tabftir/imageSun.jpg",thresSun)
        #cv2.imwrite("/home/tabftir/imageApt.jpg",thresApt)
        
        #--------------
        # Find contours
        #-------------- 
        contoursApt, hierarchy = cv2.findContours(thresApt,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)      
    
        #----------------------
        # Sort contours by area
        #----------------------
        contoursApt = sorted(contoursApt, key=cv2.contourArea, reverse=True)
        contoursApt = np.array(contoursApt)        
    
        #----------------------
        # Find area of contours
        #----------------------
        contAreaApt = np.array([cv2.contourArea(c) for c in contoursApt])
    
        #----------------------------------
        # Determine center of CCD in pixels
        #----------------------------------
        self.xCenter = self.xSize/2.0
        self.yCenter = self.ySize/2.0      

        #---------------------
        # Search for Aperature
        #---------------------
        #----------------------------------------
        # Search for aperature:
        # Filter contours based on largest and
        # smallest possible aperature size
        #----------------------------------------
        rmind1 = np.where(contAreaApt < self.ctlFile['FilterAreaMinApt'])[0] 
        rmind2 = np.where(contAreaApt > self.ctlFile['FilterAreaMaxApt'])[0]
        rmind  = np.union1d(rmind1,rmind2)
    
        contoursApt = np.delete(contoursApt,rmind)
        contAreaApt = np.delete(contAreaApt,rmind) 
    
        #--------------------------------------
        # Aperature should be close to a circle
        # therefore we fit a circle
        #--------------------------------------
        aptCenterPnts = []
        aptAreas      = []
        aptRad        = []
        aptMeanInt    = []

        for singCon in contoursApt:
            
            #-----------------------------------------------
            # Test to see if aperature is visible. If not 
            # something is wrong (i.e. Sun has been blocked)
            #-----------------------------------------------
            try:
                center, radius = cv2.minEnclosingCircle(singCon)
            except:
                crntT = dt.datetime.utcnow()
                print "Unable to find an aperature. All aperatures filtered!!"                   
                return False
            
            aptCenterPnts.append(center)
            aptRad.append(radius)
            aptAreas.append(np.pi*radius**2)
            
            #----------------------------------------------------------
            # Find mean pixel intensity and the area within 
            # aperature contour to help determine if aperature is found
            #----------------------------------------------------------
            aptCentInt = (int(np.round(center[0])),int(np.round(center[1])))
            aptRadInt  = int(np.round(radius))
            mask       = np.zeros(self.img_np.shape,np.uint8)
            cv2.circle(mask,aptCentInt,aptRadInt,255,-1)
            aptMeanInt.append(cv2.mean(self.img_np,mask=mask)[0]) 
    
        aptAreas   = np.array(aptAreas)
        aptMeanInt = np.array(aptMeanInt)
        
        #--------------------------------------------------
        # Find the fitted circle with the area closest to 
        # aperature area (for specific filter) specified in
        # the ctl file
        #--------------------------------------------------
        #-----------------------------------------------------
        # The aperature should be close to center of the image
        # If center of aperature is off from the center of the 
        # image by a certain amount than try another
        #-----------------------------------------------------        
        while True:
            if len(aptAreas) == 0:
                crntT = dt.datetime.utcnow()
                #cv2.imwrite("/home/tabftir/imageApt3.jpg",mask)              
                if TCPflg: self.writeCameraErr("3 {} /home/tabftir/imageApt3.jpg".format(crntT)) 
                return False
    
            if self.ctlFile['AptFltrType'] == 1:
                indApt = aptMeanInt.argmin()
            elif self.ctlFile['AptFltrType'] == 2:
                indApt = (np.sqrt((self.xCenter-aptCenterPnts[:][0])**2 + (self.yCenter-aptCenterPnts[:][1])**2)).argmin()
        
            dist = np.sqrt((self.xCenter-aptCenterPnts[indApt][0])**2 + (self.yCenter-aptCenterPnts[indApt][1])**2)
    
            #-------------------------------
            # Test distance if within limits
            #-------------------------------
            if dist < (0.3*np.min([self.xCenter,self.yCenter])): 
                self.x_apt    = aptCenterPnts[indApt][0]
                self.y_apt    = aptCenterPnts[indApt][1]
                self.rad_apt  = aptRad[indApt]
                self.area_apt = aptAreas[indApt]
                break
            else:
                aptAreas      = np.delete(aptAreas,indApt)
                aptCenterPnts = np.delete(aptCenterPnts,indApt,axis=0)
                aptMeanInt    = np.delete(aptMeanInt,indApt)
    
        #----------------------------------------------
        # Find distance between center of aperature and 
        # center of CCD
        #----------------------------------------------
        self.delX = self.xCenter - self.x_apt
        self.delY = self.yCenter - self.y_apt         
        
        #--------------------------------------------
        # Find total distance sqrt(delX**2 + delY**2)
        #--------------------------------------------
        self.dist = np.sqrt(self.delX**2 + self.delY**2)
            
        #--------------------------------------------------------------
        # Draw circles around Sun spot and aperature (if aptFlg = True)
        #--------------------------------------------------------------
        cv2.circle(self.img_np,(int(np.round(self.x_apt)),int(np.round(self.y_apt))),
                                int(np.round(self.rad_apt)),(255,255,255),2)
                 
        return self.dist
    
    def findJustSun(self):
        '''Thresholds the image and finds contours'''
        
        #---------------------
        # Reset Sun found flag
        #---------------------
        self.sunFound = False
    
        #--------------------------
        # Capture image from camera
        #--------------------------
        self.captureImg()
    
        #---------------------------
        # Timestamp of image capture
        #---------------------------
        self.imgTime = dt.datetime.utcnow()
    
        #----------------------------------------------------
        # Threshold image. Do two thresholds. One to find the 
        # aperature and one to find the Sun
        #----------------------------------------------------
        blur         = cv2.GaussianBlur(self.img_np,(15,15),0)
        ret,thresSun = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thresApt     = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
    
        #cv2.imwrite("/home/tabftir/imageSun.jpg",thresSun)
        #cv2.imwrite("/home/tabftir/imageApt.jpg",thresApt)
        
        #--------------
        # Find contours
        #--------------
        contoursSun, hierarchy = cv2.findContours(thresSun,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)       
    
        #----------------------
        # Sort contours by area
        #----------------------
        contoursSun = sorted(contoursSun, key=cv2.contourArea, reverse=True)
        contoursSun = np.array(contoursSun)
        
        #----------------------
        # Find area of contours
        #----------------------
        contAreaSun = np.array([cv2.contourArea(c) for c in contoursSun])

        #--------------------------
        # Filter out bogus contours
        #--------------------------        
        #-----------------------------------------------
        # cv2.contours usually picks up the contour of
        # the entire frame. Filter out contour which have
        # areas close to detector size. For DMK 23U445
        # 1280x960 = 1,228,800 (use 1,000,000)
        #-----------------------------------------------
        rmind       = np.where(contAreaSun > self.ctlFile['FilterAreaDetSize'])[0]
        if rmind:
            contoursSun = np.delete(contoursSun,rmind,axis=1)
            contAreaSun = np.delete(contAreaSun,rmind,axis=1)        
    
        #----------------------------------
        # Determine center of CCD in pixels
        #----------------------------------
        self.xCenter = self.xSize/2.0
        self.yCenter = self.ySize/2.0        
    
        #---------------
        # Search for Sun        
        #-------------------------------------------
        # Largest contour area assumed to be the sun
        # This may not be true if the sun is only
        # partially illuminating the aperature wheel
        #-------------------------------------------
        sunInd               = np.argmax(contAreaSun)
        self.sunContour      = contoursSun[sunInd]
        
        #-----------------------------------------------
        # Test to see if Sun is visible. If not 
        # something is wrong (i.e. Sun has been blocked)
        #-----------------------------------------------        
        try:
            sunCenter, sunRadius = cv2.minEnclosingCircle(self.sunContour)
        except:
            return False
        
        self.x_sun           = sunCenter[0]
        self.y_sun           = sunCenter[1]
        self.rad_sun         = sunRadius 
        self.area_sun        = np.pi * sunRadius**2
    
        #----------------------------------------
        # Convert sunRadius and center points to 
        # integers for cv2 circle drawing routine
        #----------------------------------------
        sunRadius = int(np.round(sunRadius))
        sunCenter = (int(np.round(sunCenter[0])),int(np.round(sunCenter[1])))
    
        #------------------------------------------------
        # Find mean pixel intensity and the area within 
        # Sun contour to determine if Sun is found
        #------------------------------------------------
        mask = np.zeros(self.img_np.shape,np.uint8)
        cv2.circle(mask,sunCenter,sunRadius,255,-1)
        self.sunPixMean = cv2.mean(self.img_np,mask=mask)[0]
    
        if (self.sunPixMean >= self.ctlFile['minSunPixMean']): 
            if (self.area_sun >= self.ctlFile['minSunPixArea']): self.sunFound = True
            else: 
                crntT = dt.datetime.utcnow()
                print "Unable to find the Sun!!!"
                return False
    
        #----------------------------------------------
        # Find distance between center of sun spot and 
        # the center of CCD
        #----------------------------------------------
        self.delX = self.xCenter - self.x_sun
        self.delY = self.yCenter - self.y_sun    
        
        #--------------------------------------------
        # Find total distance sqrt(delX**2 + delY**2)
        #--------------------------------------------
        self.dist = np.sqrt(self.delX**2 + self.delY**2)
            
        #--------------------------------------------------------------
        # Draw circles around Sun spot and aperature (if aptFlg = True)
        #--------------------------------------------------------------
        cv2.circle(self.img_np,sunCenter,sunRadius,(255,255,255),2)       
            
        return self.dist
    
    
    
    
  