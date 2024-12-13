#----------------------------------------------------------------------------------------
# Name:
#        controllerCST.py
#
# Purpose:
#       This file contains code moving the CST
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
import datetime       as     dt
from   time           import sleep
from   trackerUtils   import *
from   remoteData     import FTIRdataClient


class TrackerCntrl(FTIRdataClient):
    ''' This class controlls the movement of the NCAR solar tracker. It is designed to 
        communicate with the Newport ESP301 motion controller
    '''
    
    def __init__(self, ctlFile,TCPflg=False):
        '''
        '''
        
        self.rt        = '\r\n'
        self.reset     = False
        self.offlimit  = False
        self.shutdown  = True
        self.cordFlp   = False
        self.ctlFile   = ctlFile
        self.TCPflg    = TCPflg
        FTIRdataClient.__init__(self,TCP_IP=self.ctlFile["FTS_DataServ_IP"],
                                TCP_Port=self.ctlFile["FTS_DataServ_PORT"],BufferSize=self.ctlFile["FTS_DATASERV_BSIZE"])        

    #----------------------------------------------
    # Builder functions (Wrappers for ESP commands)
    #----------------------------------------------
    def connect(self):
        self.tty = serial.Serial(port=self.ctlFile['ESPserialPort'], baudrate=self.ctlFile['ESPserialBaudrate'], timeout=1)         

        #-------------------------------------------
        # Log if unable to connect to ESP controller
        #-------------------------------------------
        if (self.tty.isOpen() == -1):
            if self.TCPflg:
                crntT = dt.datetime.utcnow()
                self.writeControllerErr("1 {}".format(crntT))            

        return self.tty.isOpen()

    def disconnect(self):
        self.tty.close()
        
    def read_rtn(self):
        return self.tty.readline().strip()
    
    def listen(self,TO):
        st     = dt.datetime.now()
        rtnStr = ''
        
        while not rtnStr:
            rtnStr = self.read_rtn()
            
            if (dt.datetime.now() - st).seconds > TO:
                return -1
          
        return rtnStr  
    
    def reset_esp(self):
        self.tty.write('RS{0:}'.format(self.rt))
        sleep(10)

    def axis_on(self,axis=None):
        if axis==None:
            return ( self.axis_on(1),
                     self.axis_on(2) )
    
        else:
            self.tty.write('{0:}MO;{0:}MO?{1:}'.format(axis,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])      
        
    def axis_off(self,axis=None):
        if axis==None:
            return ( self.axis_off(1),
                     self.axis_off(2) )

        else:
            self.tty.write('{0:}MF;{0:}MF?{1:}'.format(axis,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])          

    def get_tracker_position(self,axis=None):
        ''' This does not take into account if the tracker coordinate system is flipped. To
            take this into account use get_tracker_position() '''
        if axis==None:
            return ( self.get_tracker_position(1),
                     self.get_tracker_position(2) )
        
        else:
            self.tty.write('{0:}TP{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))
        
    def get_vel(self,axis=None):
        
        if axis==None:
            return ( self.get_vel(1),
                     self.get_vel(2) )
        
        else:
            self.tty.write('{0:}VA?{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))
        
    def get_accel(self,axis=None):
        
        if axis==None:
            return ( self.get_accel(1),
                     self.get_accel(2) )
        
        else:
            self.tty.write('{0:}AC?{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))     
        
    def get_decel(self,axis=None):
        
        if axis==None:
            return ( self.get_decel(1),
                     self.get_decel(2) )
        
        else:
            self.tty.write('{0:}AG?{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))          
        
    def get_jerk(self,axis=None):
        
        if axis==None:
            return ( self.get_jerk(1),
                     self.get_jerk(2) )
        
        else:
            self.tty.write('{0:}JK?{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))        
        
    def det_motion(self,axis=None):
        
        if axis==None:
            return ( self.det_indefMotion(1),
                     self.det_indefMotion(2) )
        
        else:
            self.tty.write('{0:}TV{1:}'.format(axis,self.rt))
            return float(self.listen(self.ctlFile['ESPreadTO']))          
    
        
    #def get_tracker_position(self,axis=None):
        #''' This takes into account if the tracker coordinate system is flipped.
            #One still specifies the non-flipped coordinate system. '''        
        #if axis==None:
            #return ( self.get_tracker_position(1),
                     #self.get_tracker_position(2) )
        
        #else:
            #rtn = self.get_position(axis)        
            
        #if self.cordFlp: 
            #if    axis == self.ctlFile['ElAxis']: 
                #if (rtn<=-90): rtn += 90.0
                #else:          rtn -= 90.0
            #elif  axis == self.ctlFile['AzAxis']: 
                #if (rtn >= 0): rtn -= 180.0
                #else:          rtn += 180.0
                
        #return rtn
      
    def set_vel(self,vel,axis=None):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        if axis==None:
            return ( self.set_vel(vel,1),
                     self.set_vel(vel,2) )
        
        else:
            self.tty.write('{0:}VA{1:};{0:}VA?{2:}'.format(axis,vel,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])        
    
    def set_dualVel(self,azVel,elVel,azAxis,elAxis):
        ''' This sets the velocity for both axis and does not wait for response '''
        
        self.tty.write("{0:}VA{1:};{2:}VA{3:}{4:}".format(azVel,azAxis,elVel,elAxis,self.rt))
    
    def set_dualAccel(self,azAcc,elAcc,azAxis,elAxis):
        ''' This sets the acceeleration for both axis and does not wait for response '''
        
        self.tty.write("{0:}AC{1:};{2:}AC{3:}{4:}".format(azAcc,azAxis,elAcc,elAxis,self.rt))    
        
    def set_dualDecel(self,azDecel,elDecel,azAxis,elAxis):
        ''' This sets the deceleration for both axis and does not wait for response '''
        
        self.tty.write("{0:}AG{1:};{2:}AG{3:}{4:}".format(azDecel,azAxis,elDecel,elAxis,self.rt))         
        
    def set_accel(self,accel,axis=None):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        if axis==None:
            return ( self.set_accel(accel,1),
                     self.set_accel(accel,2) )
        
        else:
            self.tty.write('{0:}AC{1:};{0:}AC?{2:}'.format(axis,accel,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])  
        
    def set_decel(self,decel,axis=None):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        if axis==None:
            return ( self.set_decel(decel,1),
                     self.set_decel(decel,2) )
        
        else:
            self.tty.write('{0:}AG{1:};{0:}AG?{2:}'.format(axis,decel,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])         
        
    def set_jerk(self,accel,axis=None):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        if axis==None:
            return ( self.set_jerk(accel,1),
                     self.set_jerk(accel,2) )
        
        else:
            self.tty.write('{0:}JK{1:};{0:}JK?{2:}'.format(axis,accel,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])           
      
    def move_tracker_abs(self,amnt,axis=None,waitFlg=True):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        if axis==None:
            return ( self.move_tracker_abs(amnt,1),
                     self.move_tracker_abs(amnt,2) )
        
        else:
            if waitFlg:
                self.tty.write('{0:}PA{1:};{0:}WS;TE?{2:}'.format(axis,amnt,self.rt))
                return self.listen(self.ctlFile['ESPreadTO'])
            else:
                self.tty.write('{0:}PA{1:}{2:}'.format(axis,amnt,self.rt))
                return True
            
    def move_dual_tracker_abs(self,azPos,azAxis,elPos,elAxis):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''
        self.tty.write("{0:}PA{1:};{2:}PA{3:}{4:}".format(azPos,azAxis,elPos,elAxis,self.rt))  

    def move_indefinite(self,azAxis,azDir,elAxis,elDir):
        ''' This moves each axis in + or - direction indefinitely '''
        
        self.tty.write("{0:}MV{1:};{2:}MV{3:}{4:}".format(azAxis,azDir,elAxis,elDir,self.rt))

    def move_tracker_rel(self,amnt,axis=None):
        ''' This does not take into account if the tracker coordinate
            system if flipped '''        
        if axis==None:
            return ( self.move_rel(amnt,1),
                     self.move_rel(amnt,2) )
        
        else:
            self.tty.write('{0:}PR{1:};{0:}WS;TE?{2:}'.format(axis,amnt,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])

    def zero_position(self,axis=None):
        if axis==None:
            return ( self.zero_position(1),
                     self.zero_position(2) )
        else:
            self.tty.write('{0:}OR;{0:}WS;TE?{1:}'.format(axis,self.rt))
            return self.listen(self.ctlFile['ESPreadTO'])      
        
    def set_travelSoftLims(self,amnt,axis=None):
        if axis==None:
            return ( self.set_travelSoftLims(amnt,1),
                     self.set_travelSoftLims(amnt,2) )
        else:
            self.tty.write('{0:}SL-{1:};{0:}SL?{2:}'.format(axis,amnt,self.rt))
            rtn1 = self.listen(self.ctlFile['ESPreadTO'])
            self.tty.write('{0:}SR{1:};{0:}SR?{2:}'.format(axis,amnt,self.rt))
            rtn2 = self.listen(self.ctlFile['ESPreadTO'])            
            return (rtn1,rtn2)        

    def get_travelSoftLims(self,amnt,axis=None):
        if axis==None:
            return ( self.get_travelSoftLims(amnt,1),
                     self.get_travelSoftLims(amnt,2) )
        else:
            self.tty.write('{0:}SL?{1:}'.format(axis,self.rt))
            rtn1 = self.listen(self.ctlFile['ESPreadTO'])
            self.tty.write('{0:}SR?{1:}'.format(axis,self.rt))
            rtn2 = self.listen(self.ctlFile['ESPreadTO'])            
            return (rtn1,rtn2)

    def set_home(self,axis=None):
        if axis==None:
            return ( self.set_home(1),
                     self.set_home(2) )
        else:
            self.tty.write('{0:}DH{1:}'.format(axis,self.rt))           
            return self.read_rtn()        

    def stop_motion(self,axis=None):
        if axis==None:
            return ( self.stop_motion(1),
                     self.stop_motion(2) )
        else:
            self.tty.write('{0:}ST{1:}'.format(axis,self.rt))           
            return 1          

    def abs_to_tracker_Az(self,angle):
        '''Converts from absolute coordinate system (0 to 360 Az) 
           to tracker coordinate (0 to +/-180 Az)'''

        #--------------------------
        # Find Az in tracker coords
        #--------------------------
        if self.cordFlp: 
            newAngle = 180.0 - angle
            
        else: 
            #--------------
            # 0 <= X <= 180
            #--------------
            if (angle >= 0.0) and (angle <= 180.0): newAngle = -angle
        
            #--------------
            # 180 < X < 360
            #--------------        
            else: newAngle = 360.0 - angle        
            
        return newAngle
    
    def abs_to_tracker_velEl(self,vel):
        ''' Converts absolute solar velocities (Epheme) to tracker coordinates for Elevation'''
        if self.cordFlp:
            newVel = vel
        
        else:
            newVel = -vel 
        
        return self.determine_velDir(newVel)
    
    def abs_to_tracker_velAz(self,vel):
        ''' Converts absolute solar velocities (Epheme) to tracker coordinates for Azimuth'''
        newVel = -vel
        
        return self.determine_velDir(newVel)    
    
    def determine_velDir(self,vel):
        
        vSign = np.sign(vel)
        
        return(abs(vel),vSign)

    def abs_to_tracker_El(self,angle):
        '''This converts from absolute coordinate system (0 to 90 El)
           to tracker coordinate (0 to -90 El)'''        

        if self.cordFlp:
            newAngle = angle - 180.0
        else:
            newAngle = - angle
        
        return newAngle
    
    def tracker_to_abs_Az(self,angle):
        ''' This takes the position of the tracker given by get_tracker_position. It handles a coordinate
            flip.'''

        if self.cordFlp: 
            newAngle = 180.0 - angle

        else: 
            #--------------
            # 0 <= X <= -180
            #--------------
            if (angle <= 0.0) and (angle >= -180.0): newAngle = -angle

            #--------------
            # 0 < X < 180
            #--------------        
            else: newAngle = 360.0 - angle            

        return newAngle

    def tracker_to_abs_El(self,angle):
        ''' This takes the position of the tracker given by get_tracker_position. It handles a coordinate
            flip.'''        

        if self.cordFlp:
            newAngle = angle + 180.0
        else:
            newAngle = - angle

        return newAngle    

    
    def determine_flip(self,setState=True):
        ''' Determine if coordinate flip is necessary
            This is based off angular distance (in Azimuth) to 
            the software limits.
              --If setState == True then the flag to flip coordinate
                is set, if == False then the coordFlip state is returned
                but the flag is not set
              --If rtnChng == True then a boolean is returned indicating 
                whether the new state is different than previous'''
        #-------------------------------------
        # Test condition to determine if 
        # coordinate system should be reversed
        #-----------------------------------------------
        # Find current date time and time x minutes out
        # as specified in ctl file. This is used to test
        # whether to flip coordinate system
        #-----------------------------------------------
        #crntDateTime   = dt.datetime.utcnow()
        #crntDateTime10 = crntDateTime + dt.timedelta(minutes=self.ctlFile['timeDeltaEp'])
    
        #-----------------------------------------------------------
        # Get current ephemris data and ephemris data 10 minutes out
        #-----------------------------------------------------------
        #(sunAz,sunEl)     = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'], dateT=crntDateTime,   surfT=self.ctlFile["tempDefault"], surfP=self.ctlFile["presDefault"])            
        #(sunAz10,sunEl10) = sunAzEl(self.ctlFile['lat'], self.ctlFile['lon'], self.ctlFile['elevation'], dateT=crntDateTime10, surfT=self.ctlFile["tempDefault"], surfP=self.ctlFile["presDefault"])
        #deltaAz           = sunAz10 - sunAz        
        
        #-----------------------------
        # Get tracker current Az angle
        #-----------------------------        
        azTracker1 = self.get_tracker_position(axis=self.ctlFile['AzAxis'])
        
        #azTracker2 = azTracker1 + deltaAz
        
        #-------------------------------
        # Determine if flip is necessary
        #-------------------------------
        #if any([azTracker1 <= -self.ctlFile['AzSoftTravelLim'],azTracker1 >= self.ctlFile['AzSoftTravelLim'],
                #azTracker2 <= -self.ctlFile['AzSoftTravelLim'],azTracker2 >= self.ctlFile['AzSoftTravelLim'] ]):
                
        if abs(azTracker1) > (abs(self.ctlFile['AzSoftTravelLim']) - abs(self.ctlFile["AzDeltaEp"])):
            if setState: self.cordFlp = not self.cordFlp
            else:        return not self.cordFlp
                
        return self.cordFlp

#-----------------------------------------------------------------------------------------------------------------------------------------------#    
    #-------------------------------
    # Level 2 procedures for tracker
    #-------------------------------------
    # Shutdown Procedure:
    # 1) Stop all motion
    # 2) Return Az and El to home position
    # 3) Disable motors
    # 4) Set shutdown flag to true
    #-------------------------------------
    def shutdown(self):
        self.read_rtn()
        self.stop_motion()
        self.move_home()
        self.axis_off()
        self.disconnect()
        self.cordFlp  = False
        self.shutdown = True
        
        return 1

    #-----------------------------
    # Initialization procedure:
    # 1) Check tty connection 
    # 2) Create new tty connection
    # 3) Reset motion controller
    # 4) Set software limits
    # 5) Find home position
    #-----------------------------
    def motorInit(self):
        self.cordFlp = False
        rtn          = self.connect()
        
        #-----------------------------------
        # If unable to connect to controller
        #-----------------------------------
        if not rtn: return -1
        
        self.reset_esp()
        
        self.set_travelSoftLims(self.ctlFile['AzSoftTravelLim'], axis=self.ctlFile['AzAxis'])
        
        self.axis_on()
        
        self.zero_position()
        
        return 1
      
    #---------------------------------------------------------
    # Move suntracker. Takes into account:
    # 1) Location of Azimuth motor limits
    # 2) Specified offsets (callibration and constant)
    # Incoming Az and El angles are in absolute coordinate
    # system (S = 0 deg, W = 90 deg, N = 180 deg, E = 270 deg)
    # Need to convert to tracker coordinate system (
    # S = 0 deg, W = -90 deg, N = +/- 180 deg, E = 90 deg)
    #
    # -- Input angles assumed to be in absolute coordinates!!!
    #---------------------------------------------------------
    def pointTracker(self,AzAngle,ElAngle,ElOffset=0.0,AzOffset=0.0,waitFlg=True):
        
        #-----------------------------------------------------------
        # Add offsets. Azimuth angle should be between 0-360 degrees 
        # If offset brings angle < 0 must convert back to 0-360
        #-----------------------------------------------------------
        AzAngle  += AzOffset
        if (AzAngle < 0):  AzAngle  += 360.0
        
        ElAngle  += ElOffset
        
        #----------------------------------------------
        # Determine if need a flip in coordinate system
        #----------------------------------------------
        self.determine_flip(setState=True)
        
        #----------------------------------------------------------------
        # Convert Absolute coordinate system to tracker coordinate system
        #----------------------------------------------------------------
        AzTracker  = self.abs_to_tracker_Az(AzAngle)
        ElTracker  = self.abs_to_tracker_El(ElAngle)
        
        #------------------------------------------
        # Move Tracker in tracker coordinate system
        #------------------------------------------
        if waitFlg:
            rtn1 = self.move_tracker_abs(AzTracker, axis=self.ctlFile['AzAxis'])
            rtn2 = self.move_tracker_abs(ElTracker, axis=self.ctlFile['ElAxis'])
            return (rtn1,rtn2)
        else:
            rtn = self.move_dual_tracker_abs(AzTracker,self.ctlFile['AzAxis'],ElTracker,self.ctlFile['ElAxis'])
        

    #--------------------------------------------------
    # Error Codes:
    #  1: Not able to connect to ESP controller
    #-------------------------------------------------- 

    #---------------------------------
    # Check if Camera Error log exists
    #---------------------------------
    #if not ckFile(dataDir):
        #with open(self.baseDataDir+"ContrErr.log",'w') as fopen:
            #fopen.write("{0:20s} {1:20s} \n".format("Error Code","Time Stamp"))

    #else:
        #with open(self.baseDataDir+"ContrErr.log",'a') as fopen:
            #fopen.write("{0:20s} {1:20s} \n".format(splitVals[1],splitVals[2]))

    ##---------------------------------------
    ## If this is a critical error send email
    ##---------------------------------------
    #if splitVals[1] == "99":
        #smtpEmail("Unable to connect to ESP Controller at {} UTC".format(splitVals[2]), 
                  #"TAB1", ["ebaumer@ucar.edu","jamesw@ucar.edu"],"Critical Error at Thule")

    ##------------------------
    ## Return status to client
    ##------------------------
    #sock.send("Write Successfull")  