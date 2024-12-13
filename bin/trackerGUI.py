#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        trackerGUI.py
#
# Purpose:
#       Program for sending command line arguments to tracker control
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

import sys
import os
import getopt
import ttk
import Image
import datetime       as     dt
import Tkinter        as     tk
from time             import sleep
from trackerUtils     import *
from trackerNCAR      import TrackerNCAR
from tkFileDialog     import askopenfilename
from multiprocessing  import Process
from PIL              import ImageTk


class TrackerGUI(tk.Frame,TrackerNCAR):
    
    
    def __init__(self,parent,ctlFile):
        tk.Frame.__init__(self,parent,background="white")
        
        self.trcker       = TrackerNCAR(ctlFile,TCPflg=False)
        self.parent       = parent
        self.trckFlg      = False
        self.loopCamFlg   = False
        self.EphemFlg     = False
        self.centerSunFlg = False
        self.fullTrckFlg  = False
        self.firstTrckFlg = False
        self.cnctFlg      = False
        self.imgWidth     = 320
        self.imgHeight    = 240  
        self.delay        = 100
        self.camImg       = [None]
        self.initializeGUI()
        
    def fillImg(self,image, color):
        """Fill image with a color=(r,b,g)."""
        r,g,b = color
        width = image.width()
        height = image.height()
        hexcode = "#%02x%02x%02x" % (r,g,b)
        horizontal_line = "{" + " ".join([hexcode]*width) + "}"
        image.put(" ".join([horizontal_line]*height))        
        
    def initializeGUI(self):
        self.grid()
        self.parent.title("NCAR Tracker GUI")
        #self.pack(fill=tk.BOTH,expand=1)        
        self.addButtons()
        self.addCheckBox()
        self.addInputBox()
        self.addTextBox()
        self.loopCam()
        self.centerWindow()
        
    def textCallBack(self,textString):
        self.textBox.insert(tk.END,textString)
        self.textBox.see(tk.END)
        
    def centerWindow(self):
        w = 850
        h = 800
    
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
    
        x = (sw - w)/2
        y = (sh - h)/2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))     
        
    def addTextBox(self):
        self.textBox = tk.Text(self)
        self.textBox.grid(row=5,column=0,columnspan=4,sticky='nsew')
        
    def addCheckBox(self):
        #-----------------------------
        # Add check box for flip state
        #-----------------------------
        self.guiFlip = tk.IntVar()
        flipCB       = tk.Checkbutton(self,text="Flip Mode",variable=self.guiFlip)
        flipCB.grid(row=2,column=1)
        
    def addInputBox(self):
        #-------------------------
        # Add input for angle step
        #-------------------------
        labelAngleStep = tk.Label(self, text="Angle Step [Deg]")
        labelAngleStep.grid(row=3,column=0)
        self.valAngleStep   = tk.Entry(self)
        self.valAngleStep.insert(0, "0.1")
        self.valAngleStep.grid(row=4,column=0)
        
        #------------------------
        # Add input for El offset
        #------------------------
        labelElOffset = tk.Label(self, text="Elevation Offset [Deg]")
        labelElOffset.grid(row=3, column=1)
        self.valElOffset   = tk.Entry(self)
        self.valElOffset.insert(0, "0.0")
        self.valElOffset.grid(row=4,column=1)        
        
        #------------------------
        # Add input for Az offset
        #------------------------
        labelAzOffset = tk.Label(self, text="Azimuth Offset [Deg]")
        labelAzOffset.grid(row=3,column=2)
        self.valAzOffset   = tk.Entry(self)
        self.valAzOffset.insert(0, "0.0")
        self.valAzOffset.grid(row=4,column=2)         
        
    def addButtons(self):

        #------------------------
        # Add find ellipse button
        #------------------------
        ellipseButton =  ttk.Button(self,text="Find Ellipse",command=self.findEll)
        ellipseButton.grid(row=7,column=3)

        #--------------------------
        # Add connect to ESP button
        #--------------------------
        connectButton =  ttk.Button(self,text="Cnct/Discnt ESP",command=self.connectESP)
        connectButton.grid(row=6,column=3)
        
        #----------------
        # Add quit button
        #----------------
        quitButton = ttk.Button(self,text="Quit",command=self.quitGUI)
        quitButton.grid(row=6,column=0)
        
        #-------------------------
        # Add initialize button
        #-------------------------
        initButton = ttk.Button(self,text="Initialize",command=self.initTracker)
        initButton.grid(row=6,column=1)
        
        #-----------------------------
        # Disconnect Everything Button
        #-----------------------------
        discntButton = ttk.Button(self,text="Disconnect",command=self.discntAll)
        discntButton.grid(row=6,column=2)
    
        #-------------
        # Track button
        #-------------
        trackButton = ttk.Button(self,text="Track",command=self.fullTrackButton)
        trackButton.grid(row=0,column=0)

        #------------
        # Hold button
        #------------ 
        #holdButton = ttk.Button(self,text="Tracker Hold",command=self.trckHld)
        #holdButton.grid(row=1,column=0)        
        
        #--------------------
        # Park Tracker button
        #--------------------
        parkButton = ttk.Button(self,text="Park Tracker",command=self.parkPos)
        parkButton.grid(row=1,column=0)    
        
        #---------------------------
        # Add track ephemeris button
        #---------------------------  
        ephemButton = ttk.Button(self,text="Track Ephemeris",command=self.trackEphemButton)
        ephemButton.grid(row=2,column=2)        
        
        #---------------------------
        # Add track Center Sun button
        #---------------------------  
        CenterSunButton = ttk.Button(self,text="Center Sun CCD",command=self.centerSunButton)
        CenterSunButton.grid(row=2,column=0)        
        
        #-----------------------
        # Add stop motion button
        #-----------------------
        stopButton = ttk.Button(self,text="Stop Motion",command=self.stopMotion)
        stopButton.grid(row=7,column=0)         
        
        #-------------------------
        # Add Home position button
        #-------------------------
        zeroButton = ttk.Button(self,text="Zero Position",command=self.zeroTrac)
        zeroButton.grid(row=7,column=1)    
        
        #----------------------
        # Add loop image button
        #----------------------
        loopButton = ttk.Button(self,text="Start/Stop Image Loop",command = self.startStopImgLoop)
        loopButton.grid(row=7,column=2)
        
        #------------------------------
        # Elevation and Azimuth Buttons
        #------------------------------
        posElButton = ttk.Button(self,text="+ El",command=self.posEl)
        posElButton.grid(row=0,column=1)
        negElButton = ttk.Button(self,text="- El",command=self.negEl)
        negElButton.grid(row=1,column=1)        
        posAzButton = ttk.Button(self,text="+ Az",command=self.posAz)
        posAzButton.grid(row=0,column=2)        
        negAzButton = ttk.Button(self,text="- Az",command=self.negAz)
        negAzButton.grid(row=1,column=2)    
              
        #--------------------
        # Add Find Sun Button
        #--------------------
        sunButton = ttk.Button(self,text="Find Sun",command=self.findSun)
        sunButton.grid(row=8,column=0)               

        #--------------------------
        # Add Find Aperature Button
        #--------------------------
        aptButton = ttk.Button(self,text="Find Aperature",command=self.findApt)
        aptButton.grid(row=8,column=1)               
              
    def loopCam(self):
        #-----------------------------------------------
        # If can't find camera image fill with (255,0,0)
        #-----------------------------------------------
        try:
            if self.imgTypeFlg == 1:   ImageTk.PhotoImage.__del__(self.camImg[0])
            elif self.imgTypeFlg == 2: tk.PhotoImage.__del__(self.camImg[0])      
        except: pass
        try:
            if not self.trckFlg:
                self.trcker.captureImg()
                self.camImg[0] = self.trcker.img.resize((self.imgWidth,self.imgHeight),Image.ANTIALIAS)
            else: 
                temp           = Image.fromarray(self.trcker.img_np)
                self.camImg[0] = temp.resize((self.imgWidth,self.imgHeight),Image.ANTIALIAS)
                
            self.camImg[0] = ImageTk.PhotoImage(self.camImg[0])
            self.imgTypeFlg = 1
        except:
            self.camImg[0] = tk.PhotoImage(width=self.imgWidth,height=self.imgHeight)
            self.fillImg(self.camImg[0],(255,0,0))
            self.imgTypeFlg = 2
                
        camPanel       = tk.Label(self) 
        camPanel.configure(image=self.camImg[0])
        #camPanel.image = self.camImg[0]
        camPanel.grid(row=0,column=3,rowspan=3)
        
        #self.parent.update_idletasks()
        if self.loopCamFlg:
            self.parent.after(self.delay,self.loopCam)          
         
    #----------------------
    # Define button actions
    #----------------------
    def initTracker(self):
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{}: Initializing Tracker....\n".format(crntTime))
        self.trcker.initializeTracker()
        self.trckFlg = False
        self.textCallBack("Tracker Initialized.\n\n")     
        
    def discntAll(self):
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{}: Disconnecting Tracker and Camera....\n".format(crntTime))
        self.trcker.disconnect()
        self.trcker.camClose()
        self.trckFlg = False
        self.textCallBack("Tracker and Camera Disconnected\n\n")
        
    def quitGUI(self):
        try:
            self.trcker.disconnect()
            self.trcker.camClose()
        except:
            pass
        self.parent.destroy()
        
    def findEll(self):
        self.loopCamFlg = False
        
        try:
            self.parent.after_cancel(self.loopCam)
        except: pass     
        
        print "Displaying captured image"
        
        self.trcker.findEllipse(aptFlg=True)

        self.trckFlg = True
        self.loopCam()
        self.trckFlg = False
        
    def findSun(self):
        self.loopCamFlg = False
        
        self.trcker.findJustSun()
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{0:}: Sun Delta X pixels to center CCD = {1:}\n".format(crntTime,self.trcker.delX))
        self.textCallBack("{0:}: Sun Delta Y pixels to center CCD = {1:}\n".format(crntTime,self.trcker.delY))
        self.textCallBack("{0:}: Pixel area of Sun                = {1:}\n".format(crntTime,self.trcker.area_sun))
        self.textCallBack("{0:}: Pixel mean radiance of Sun       = {1:}\n\n".format(crntTime,self.trcker.sunPixMean))

        self.trckFlg = True
        self.loopCam()
        self.trckFlg = False    
        
    def findApt(self):
        self.loopCamFlg = False
        
        try:
            self.parent.after_cancel(self.loopCam)
        except: pass           
        
        self.trcker.findJustApt()
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{0:}: Aperature Delta X pixels to center CCD = {1:}\n".format(crntTime,self.trcker.delX))
        self.textCallBack("{0:}: Aperature Delta Y pixels to center CCD = {1:}\n".format(crntTime,self.trcker.delY))
        self.textCallBack("{0:}: Pixel area of Aperature                = {1:}\n\n".format(crntTime,self.trcker.area_apt))

        self.trckFlg = True
        self.loopCam()
        self.trckFlg = False     

    def startStopImgLoop(self):
        self.loopCamFlg = not self.loopCamFlg
        if self.loopCamFlg: 
            crntTime = dt.datetime.utcnow()
            self.textCallBack("{0:}: Looping camera images.\n\n".format(crntTime))
            self.loopCam()
        else:
            crntTime = dt.datetime.utcnow()
            self.textCallBack("{0:}: Stopping camera loop.\n\n".format(crntTime))
            self.parent.after_cancel(self.loopCam)
        
    def trackEphemButton(self):
        self.EphemFlg = not self.EphemFlg
        self.trackEphem()
        
    def fullTrackButton(self):
        self.fullTrckFlg = not self.fullTrckFlg
        self.skipMain       = False
        self.trcker.caltime = False
        self.fullTrack()
    
    def centerSunButton(self):
        self.centerSunFlg = not self.centerSunFlg
        self.firstPass = True
        self.calFlg    = True
        self.centerSun()
    
    def stopMotion(self):
        self.trcker.stop_motion()
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{}: Stopped all axis motion.\n\n".format(crntTime))
      
    def parkPos(self):
        
        self.trcker.parkPos = False
        self.trcker.parkTracker()
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{}: Stopped all axis motion.\n\n".format(crntTime))
        
    def zeroTrac(self):
        #-------------------------------------------------
        # Set acceleration,deceleration, and jerk of motors 
        # for centering of Sun. This is relatively fast.
        #-------------------------------------------------
        self.trcker.setAccelJerk(speed="fast")  
            
        self.trcker.zero_position()
        crntTime = dt.datetime.utcnow()
        self.textCallBack("{0}: Tracker Position Zeroed.\n\n".format(crntTime))
    
    def connectESP(self):
        self.cnctFlg = not self.cnctFlg
        
        if self.cnctFlg:
            self.trcker.connect()
            self.trcker.connectCam()
            crntTime = dt.datetime.utcnow()
            self.textCallBack("{0}: Connected to ESP301 controller and camera\n\n".format(crntTime))
        else:
            self.trcker.disconnect()
            self.trcker.camClose()
            crntTime = dt.datetime.utcnow()
            self.textCallBack("{0}: Disconnected to ESP301 controller and camera\n\n".format(crntTime))
        
    def trackEphem(self):
        
        self.loopCamFlg     = False
        self.trcker.cordFlp = self.guiFlip.get()
        
        if not self.EphemFlg:
            self.parent.after_cancel(self.trackEphem)
            return            
        
        #-------------------------------------------------
        # Set acceleration,deceleration, and jerk of motors 
        # for centering of Sun. This is relatively fast.
        #-------------------------------------------------
        self.trcker.setAccelJerk(speed="fast")  
        
        elOffset = float(self.valElOffset.get())
        azOffset = float(self.valAzOffset.get())        

        crntTime = dt.datetime.utcnow()
        self.textCallBack("{0}: Moving tracker to ephemris calculated position....\n\n".format(crntTime))
        
        crntDateTime = dt.datetime.utcnow()
    
        #-----------------------------------------------------------
        # Get current ephemris data and ephemris data 10 minutes out
        #-----------------------------------------------------------
        (sunAz,sunEl) = sunAzEl(self.trcker.ctlFile['lat'], self.trcker.ctlFile['lon'], self.trcker.ctlFile['elevation'], 
                                dateT=crntDateTime,surfT=self.trcker.ctlFile['tempDefault'], surfP=self.trcker.ctlFile['presDefault'])            

        #-------------------------
        # Print out Ephemeris data
        #-------------------------
        self.textCallBack("{0}: Calculated Azimuth Angle (West of South) = {1:}\n".format(crntTime,sunAz))
        self.textCallBack("{0}: Calculated Elevation Angle = {1:}\n".format(crntTime,sunEl))
        self.textCallBack("{0}: Current UTC date and time  = {1:}\n\n".format(crntTime, crntDateTime))
        
        #---------------------
        # Initial point to Sun
        #---------------------
        elOffset += self.trcker.ctlFile["ElOffSet"]
        azOffset += self.trcker.ctlFile["AzOffSet"]
        self.trcker.pointTracker(sunAz, sunEl,ElOffset=elOffset, AzOffset=azOffset)

        self.trckFlg = False
        self.loopCam()

        self.parent.after(500,self.trackEphem)
          
        
    def centerSun(self):
        self.loopCamFlg = False
        
        jogFlgBool    = False
        
        #-------------------------------------------------
        # Set acceleration,deceleration, and jerk of motors 
        # for centering of Sun. This is relatively fast.
        #-------------------------------------------------
        self.trcker.setAccelJerk(speed="fast")  
    
        if not self.centerSunFlg:
            self.parent.after_cancel(self.centerSun)
            return
        
        elOffset = float(self.valElOffset.get())
        azOffset = float(self.valAzOffset.get())        
    
        self.textCallBack("Centering Sun on CCD....\n\n")
    
        crntDateTime = dt.datetime.utcnow()
        
        #-----------------------------------------------------------
        # Get current ephemris data and ephemris data 10 minutes out
        #-----------------------------------------------------------
        (sunAz,sunEl) = sunAzEl(self.trcker.ctlFile['lat'], self.trcker.ctlFile['lon'], self.trcker.ctlFile['elevation'], 
                                dateT=crntDateTime,surfT=self.trcker.ctlFile['tempDefault'], surfP=self.trcker.ctlFile['presDefault'])            
    
        #---------------------
        # Initial point to Sun
        #---------------------
        elOffset += self.trcker.ctlFile["ElOffSet"]
        azOffset += self.trcker.ctlFile["AzOffSet"]    
    
        if self.firstPass:

            self.trcker.pointTracker(sunAz, sunEl,ElOffset=elOffset, AzOffset=azOffset)    
        
            #-------------
            # Look for Sun
            #-------------
            self.trcker.findEllipseN(N=self.trcker.ctlFile['ellipseN'])
        
            #--------------------------------
            # If Sun is not found jog tracker 
            #--------------------------------
            if all([not self.trcker.sunFound,jogFlgBool]): 
                rtn = self.trcker.jogToFindSun()
        
                if not rtn:
                    print 'Unable to find Sun via jogging tracker.'                            
                    sleep(self.trcker.ctlFile['noSunSleep'])
                    self.parent.after(500,self.centerSun)
        
            #---------------------------------------------
            # If Sun is not found and jog tracker flag was 
            # not chosen then wait to see if Sun appears
            #---------------------------------------------
            elif all([not self.trcker.sunFound,not jogFlgBool]):
                print 'Unable to find Sun, try jog tracker option.'                            
                sleep(self.trcker.ctlFile['noSunSleep'])
                self.parent.after(500,self.centerSun)         
    
            #---------------------------------------
            # Do initial base calibration of tracker
            #---------------------------------------
            if self.calFlg:
                self.trcker.baseCallibrate()
                calTime = dt.datetime.utcnow()
                self.calFlg = False
    
        #----------------------------------
        # Move tracker to center Sun to CCD
        #-------------------------------------------------------
        # Find delta pixels between Sun center and center of CCD
        #-------------------------------------------------------
        self.trcker.findEllipseN(N=self.trcker.ctlFile['ellipseN'])
    
        #-------------------------------------
        # Convert delta pixels to delta angles
        #-------------------------------------
        newAngles = self.trcker.pixel_to_angle(self.trcker.delX, self.trcker.delY)
        delAz     = newAngles[0] 
        delEl     = newAngles[1]
    
        #------------------------------------------------
        # Check Delta Angles. This should be fairly small
        #------------------------------------------------
        if any([delAz>self.trcker.ctlFile['delAzSeekLim'],delEl>self.trcker.ctlFile['delElSeekLim']]):
            print "Delta Angles to move Sun to center of CCD are larger than limits!!!!\n"
            print "Delta Az Angle = {}\n".format(delAz)
            print "Delta El Angle = {}\n\n".format(delEl)
            self.parent.after(500,self.centerSun)
    
        #-------------------------------------------
        # Get current Az and El positions of tracker
        # and add delta angles
        #-------------------------------------------
        crntTrackerAzPos = self.trcker.get_tracker_position(axis=self.trcker.ctlFile['AzAxis'])
        crntTrackerElPos = self.trcker.get_tracker_position(axis=self.trcker.ctlFile['ElAxis'])   
    
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
        #crntTrackerAzPos = self.trcker.tracker_to_abs_Az(crntTrackerAzPos)
        #crntTrackerElPos = self.trcker.tracker_to_abs_El(crntTrackerElPos)
    
        #newTrackerAzPos  = crntTrackerAzPos + delAz
        #newTrackerElPos  = crntTrackerElPos + delEl
    
        if (newTrackerAzPos < 0): newTrackerAzPos += 360.0
        if (newTrackerElPos < 0): newTrackerElPos += 360.0
    
        #------------------------------
        # Point Tracker to new position
        #------------------------------
        self.trcker.pointTracker(newTrackerAzPos, newTrackerElPos,ElOffset=0.0, AzOffset=0.0)
    
        #------------------------------------------------------
        # Find distance between center of Sun and center of CCD
        #------------------------------------------------------
        self.trcker.findEllipseN(aptFlg=False, N=2)    
    
        #-------------------------
        # Print out Ephemeris data
        #-------------------------
        self.textCallBack("Calculated Azimuth Angle (West of South) = {0:}\n".format(sunAz))
        self.textCallBack("Calculated Elevation Angle = {0:}\n".format(sunEl))
        self.textCallBack("Current UTC date and time  = {0:}\n\n".format(crntDateTime))
        
        self.trcker.findJustSun()
        
        self.textCallBack("Sun Delta X pixels to center CCD = {}\n".format(self.trcker.delX))
        self.textCallBack("Sun Delta Y pixels to center CCD = {}\n".format(self.trcker.delY))
        self.textCallBack("Pixel area of Sun                = {}\n".format(self.trcker.area_sun))
        self.textCallBack("Pixel mean radiance of Sun       = {}\n\n".format(self.trcker.sunPixMean))
    
        self.trckFlg   = True
        self.loopCam()
        self.trckFlg   = False           
        self.firstPass = False
        
        self.parent.after(1000,self.centerSun)        
        
    def fullTrack(self):
        self.loopCamFlg = False

        if not self.fullTrckFlg:
            self.parent.after_cancel(self.fullTrack)
            return        
        
        self.textCallBack("Moving Sun to center of CCD....\n")

        elOffset             = float(self.valElOffset.get())
        azOffset             = float(self.valAzOffset.get()) 
        jogFlgBool           = False
        self.trcker.AzOffSet = azOffset
        self.trcker.ElOffSet = elOffset
        self.trcker.cordFlp  = self.guiFlip.get()
        self.trcker.caltime  = self.trcker.track(surfPres=self.trcker.ctlFile["presDefault"],surfTemp=self.trcker.ctlFile["tempDefault"],
                                                 jogFlg=jogFlgBool,guiFlg=True,skipMainLoopFlg=self.skipMain)

        self.skipMain = True
        self.trckFlg  = True
        self.loopCam()
        self.trckFlg  = False         
                
        time = int(self.trcker.ctlFile["holdSunInt"]*1000)
        self.parent.after(time,self.fullTrack)
        
        
    def posEl(self):
        self.trckFlg = False
        angle = float(self.valAngleStep.get())
        self.textCallBack("Moving Elevation Angle +{0:} Degrees\n".format(angle))
        self.trcker.move_tracker_rel(angle,axis=self.trcker.ctlFile['ElAxis'])
        if self.trcker.sunFound: 
            self.textCallBack("Sun Center at: x = {0:} pixels, y = {1:} pixels\n\n".format(self.trcker.x_sun,self.trcker.y_sun))
        else:
            self.textCallBack("Warning...No Sun detected!!!\n\n")        

    def negEl(self):
        self.trckFlg = False
        angle = float(self.valAngleStep.get())
        self.textCallBack("Moving Elevation Angle -{0:} Degrees\n".format(angle))
        self.trcker.move_tracker_rel(-angle,axis=self.trcker.ctlFile['ElAxis'])
        if self.trcker.sunFound: 
            self.textCallBack("Sun Center at: x = {0:} pixels, y = {1:} pixels\n\n".format(self.trcker.x_sun,self.trcker.y_sun))
        else:
            self.textCallBack("Warning...No Sun detected!!!\n\n")         

    def posAz(self):
        self.trckFlg = False
        angle = float(self.valAngleStep.get())
        self.textCallBack("Moving Azimuth Angle +{0:} Degrees\n".format(angle))
        self.trcker.move_tracker_rel(angle,axis=self.trcker.ctlFile['AzAxis'])
        if self.trcker.sunFound: 
            self.textCallBack("Sun Center at: x = {0:} pixels, y = {1:} pixels\n\n".format(self.trcker.x_sun,self.trcker.y_sun))
        else:
            self.textCallBack("Warning...No Sun detected!!!\n\n")         
        
    def negAz(self):
        self.trckFlg = False
        angle = float(self.valAngleStep.get())
        self.textCallBack("Moving Azimuth Angle -{0:} Degrees\n".format(angle))
        self.trcker.move_tracker_rel(-angle,axis=self.trcker.ctlFile['AzAxis'])
        if self.trcker.sunFound: 
            self.textCallBack("Sun Center at: x = {0:} pixels, y = {1:} pixels\n\n".format(self.trcker.x_sun,self.trcker.y_sun))
        else:
            self.textCallBack("Warning...No Sun detected!!!\n\n")         
        

def main():  
    
    #-----------------------
    # Initialize root window
    #-----------------------
    root = tk.Tk()
    
    #----------------------------------------------------------
    # Initialize ctl File. This has to be done after the 
    # root window is initialized. The command 'askopenfilename'
    # automatically creates a root window.
    #----------------------------------------------------------
    ctlF = askopenfilename(title="Please Select Tracker ctl file")      
    
    #---------------
    # Initialize GUI
    #---------------
    app  = TrackerGUI(root,ctlF)
    root.mainloop() 
    
if __name__ == "__main__":
    main()