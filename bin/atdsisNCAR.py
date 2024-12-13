##! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        atdsisNCAR.py
#
# Purpose:
#       - Program for the Azimuthal Tracking Direct Solar Intensity Sensor (ATDSIS)
#       - Send data to TCP
#
# Notes:
#     
#--------------------------------
#       FOR LINUX TRY >> $ dmesg | grep tty
#       ALTERNATIVELY: setserial -g /dev/ttyS[0123]
#        FOR LINUX: /dev/ttyS0
#--------------------------------
# Created:
#       Ivan Ortega 2023 
#----------------------------------------------------------------------------------------

import serial
import time
from remoteData       import FTIRdataClient
import os
import sys
import socket
import select
import smtplib
import datetime       as     dt
from email.mime.text  import MIMEText
from trackerUtils     import *
#from ModUtils     import *
import mc5005 as mc
import struct
from time       import sleep

import matplotlib.dates as md
from matplotlib.dates import DateFormatter, MonthLocator, YearLocator
from matplotlib.ticker import FormatStrFormatter, MultipleLocator,AutoMinorLocator,ScalarFormatter
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm 
import numpy as np

import matplotlib.cm as mplcm
from matplotlib.backends.backend_pdf import PdfPages #to save multiple pages in 1 pdf...
import matplotlib.gridspec as gridspec
import matplotlib.colorbar as colorbar
import matplotlib.colors as colors
from matplotlib.dates import DateFormatter, MonthLocator, YearLocator, DayLocator, WeekdayLocator, MONDAY
#from scipy import linspace, polyval, polyfit, sqrt, stats, randn
from matplotlib.ticker import MaxNLocator

import schedule
import getopt

import math

#RefOffset = 2048  #Faulhaber motor steps per 1mm using certain incremental encoder TTL signal for position (IE resolution?)
#RefOffset = 1.0

def usage():
    ''' Prints to screen standard program usage'''
    print ( '\natdsisNCAR.py -c -?\n\n'
            '  -c                         : Optional Flag calibration \n'
            '  -?                         : Show all flags\n')


def deg2counts(deg, res=4096.):
    
    cnts = float(deg) *(res/360.)
    return cnts

def counts2deg(cnts, res=4096.):
    
    deg = float(cnts) *(360./res)
    return float(deg)

def getDTstr(crntTime):

    #--------------------------
    # Get current date and time
    #--------------------------

    yrstr    = "{0:04d}".format(crntTime.year)
    mnthstr  = "{0:02d}".format(crntTime.month)
    daystr   = "{0:02d}".format(crntTime.day)
    hourstr  =  "{0:02d}".format(crntTime.hour)
    minstr   =  "{0:02d}".format(crntTime.minute)
    secstr   =  "{0:02d}".format(crntTime.second)

    datestr  = yrstr + mnthstr + daystr
    timestr  = hourstr+':'+ minstr+':'+ secstr

    return datestr, timestr




class atdsisClass(mc.Controller, FTIRdataClient):

    def __init__(self, ctlFvars, TCPflg=False):

        self.ctlFvars        = mainInputParse(ctlFile)
        self.TCPflg          = TCPflg
        self.atdsis          = {}
        self.DataDir         = self.ctlFvars['Dir_WinData']

        if not ( self.DataDir.endswith('\\') ): self.DataDir         = self.DataDir + '\\'
        
        #self.controller =  mc.Controller.__init__(self, ctlFvars)
        #motor      =  mc.Motor.__init__(self, self.controller, node = b'\x01')

        mc.Controller.__init__(self, self.ctlFvars)
        FTIRdataClient.__init__(self,TCP_IP=self.ctlFvars['FTS_DataServ_IP'],TCP_Port=self.ctlFvars['FTS_DataServ_PORT'],BufferSize=self.ctlFvars['FTS_DATASERV_BSIZE'])
        
    
    def initialize(self):

        try:

            print("\n"+"="*20+"\nDevice Info\n"+"="*20)
            print("Device Type: ", self.getCastedRegister(0x1000))
            print("Serial Number: ", self.getCastedRegister(0x1018, subindex = 4))
            print("Status: ", self.getCastedRegister(0x6041))
            print("Modes of Operation: ", self.getCastedRegister(0x6060))
            print("Modes of Operation Display: ", self.getCastedRegister(0x6061))
            print("Producer Heartbeat Time: ", self.getCastedRegister(0x1017))
            print("Actual Program Position: ", self.getCastedRegister(0x3001, subindex = 3))
            print("Actual Program State: ", self.getCastedRegister(0x3001, subindex = 4))
            print("Error State: ", self.getCastedRegister(0x3001, subindex = 8))
            print("Error code: ", self.getCastedRegister(0x3001, subindex = 9))
            print("Motor Type: ", self.getCastedRegister(0x2329, subindex = 0x0b))
            print("Encoder Increments: ", self.getCastedRegister(0x608f, subindex = 1))
            print("Serial Number: ", self.getCastedRegister(0x1018, subindex = 4))
            print("Feed Constant: ", self.getCastedRegister(0x6092, subindex = 1))
            
            self.printStatus()        
            self.motor = mc.Motor(self, node = b'\x01')   

            print("Position Limit 1: ",self.motor.getPositionLim(subindex=1), " (p-unit)")
            print("Position Limit 2: ", self.motor.getPositionLim(subindex=2), " (p-unit)")
            print("Motor Shaft Revolutions: ",self.motor.getGearRatio(subindex=1))
            print("Driving Shaft Revolutions: ",self.motor.getGearRatio(subindex=2))
            print("Motor Nominal Velocity: ",self.motor.getNominalSpeed())

            print("\n"+"="*20+"\nPreparing Device.\n" + "="*20)

            print('Setting Position Mode...')
            self.motor.setPositionMode()

            print('\nSetting Nominal Speed...')
            self.motor.setNominalSpeed(value=int(self.ctlFvars['ATDSIS_NOMINALVEL1']))
            print("Motor Nominal Velocity: ",self.motor.getNominalSpeed())

            print('\nSetting Azimuth Limits...')
            lim1 = deg2counts(self.ctlFvars['ATDSIS_AZSOFTLIM1'])
            
            off  = deg2counts(self.ctlFvars['ATDSIS_AZOFFSET'])
            lim1 = round(lim1 - off)
            self.motor.setPositionLimit(value=lim1, subindex=1)

            lim2 = deg2counts(self.ctlFvars['ATDSIS_AZSOFTLIM2'])
            lim2 = round(lim2 - off)
            self.motor.setPositionLimit(value=lim2, subindex=2)

            print("Position Limit 1: ",self.motor.getPositionLim(subindex=1), " (p-unit)")
            print("Position Limit 2: ", self.motor.getPositionLim(subindex=2), " (p-unit)")

            print('\nSetting Gear Ratio...')
            self.motor.setGearRatio(value=int(self.ctlFvars['ATDSIS_GEARRATIO']), subindex=1)
            print("Motor Shaft Revolutions: ",self.motor.getGearRatio(subindex=1))

            print("\n"+"="*20+"\n\n" + "="*20)

            print('\n')
            self.printStatus()

            print("Restarting Devices.")
            self.motor.enable_1()

            print("Restart Complete.")
            self.printStatus()

            print("\nReading Motor position [deg]....")
            xt  = counts2deg(self.motor.getPosition(), res=float(self.ctlFvars['ATDSIS_ENCODERSTEP']))
            self.xt  = xt + float(self.ctlFvars['ATDSIS_AZOFFSET'])
            print("Initial Motor Position [deg]:", self.xt) 

            self.atdsis['ATDSIS_STATUS'] = 'INITIALIZING'

        except:

            print('\nError while Initializing ATDSIS')
            print('ATDSIS_STATUS = NOT_OK')
            self.atdsis['ATDSIS_STATUS'] = 'NOT_OK'


    def MoveAbsWait(self,Pos_X, Zero_X=0):

        res     = float(self.ctlFvars['ATDSIS_ENCODERSTEP'])
        zero_x  = float(Zero_X)
        pos_x   = float(Pos_X)

        try:

            #print(zero_x)
            xt_punit = self.motor.getPosition()
            xt_deg   =  counts2deg(xt_punit, res=res)
            #print(xt_punit)
            #print(xt_deg)
            #print('\nInitial position [cnts] = ',xt)
            self.xt  = xt_deg + zero_x
            print("Motor Position [deg]:", self.xt)
            
        
            pos_x_deg = pos_x-zero_x

            print('\nTarget position [deg]    = ',pos_x)
            pos_x_punit  = round(deg2counts(pos_x_deg, res=res))
            print('Target position [p-unit]   = ', pos_x_punit)
            
            print('\nMoving...')
        
            self.motor.positionAbsolute(pos_x_punit)

            xt_punit = self.motor.getPosition() 
            xt_deg   = counts2deg(xt_punit, res=res)
            self.xt  = xt_deg + zero_x
       
            while abs(pos_x_punit-xt_punit)>=5:# or abs(y_pos-yt)>=5:
                sleep(0.5)
                xt_punit = self.motor.getPosition()

            xt_deg   = counts2deg(xt_punit, res=res)
            self.xt  = xt_deg + zero_x
            
            #print('\nFinal position [cnts] = ',xt) 
            print('Final position [deg]  = ',self.xt)

            self.atdsis['ATDSIS_MOTAZI']  = self.xt

        except:
            print('\nError in MoveAbsWait at {}, pass!'.format(dt.datetime.now(dt.timezone.utc)))


        #if self.TCPflg:

    def homeATDSIS(self):
        ''' Send Tracker to park position '''

        print("\nSend ATDSIS to park (home) position [deg]: {}".format(self.ctlFvars['ATDSIS_AZHOME']))

        self.MoveAbsWait(self.ctlFvars['ATDSIS_AZHOME'], Zero_X=self.ctlFvars['ATDSIS_AZOFFSET'])


    def trackATDSIS(self):

        crntdate     = dt.datetime.now(dt.timezone.utc)

        sunAz,sunEl  = sunAzEl(float(self.ctlFvars['ATDSIS_LAT']), float(self.ctlFvars['ATDSIS_LON']), float(self.ctlFvars['ATDSIS_ELEVATION']), dateT=crntdate,surfP=None,surfT=None,vecFlg=False)
        sza          = 90. - sunEl

        print('{:15s}:{:.2f}'.format('\nephSZA', sza))
        print('{:15s}:{:.2f}'.format('ephSAA', sunAz))

        self.atdsis['ATDSIS_EPHAZI']    = sunAz
        self.atdsis['ATDSIS_EPHSZA']    = sza
        self.atdsis['ATDSIS_CRNTDATE']  = crntdate

        if sza <= float(self.ctlFvars['ATDSIS_SZAMAX']):

            if (sunAz >= float(self.ctlFvars['ATDSIS_AZSOFTLIM1'])) & (sunAz <= float(self.ctlFvars['ATDSIS_AZSOFTLIM2'])):

                print('\nSZA and SAA within allowable ranges, Moving atdsis...')
                if self.TCPflg: self.atdsis['ATDSIS_STATUS']  = 'TRACKING'
                
                self.MoveAbsWait(sunAz, Zero_X=self.ctlFvars['ATDSIS_AZOFFSET'])

            else:

                print('\nSZA within allowable range but SAA is not!')
                diffAngle = abs(self.xt - float(self.ctlFvars['ATDSIS_AZHOME']))
                #print('Difference in current and home position:', diffAngle)

                if diffAngle <= 0.25: 
                    print('ATDSIS Parked in Home position...')

                else:
                    self.homeATDSIS()

                if self.TCPflg: 
                    self.atdsis['ATDSIS_STATUS']  = 'PARKED'

        else:
            print('\nSZA is not within allowable range!')
            
            if self.TCPflg: self.atdsis['ATDSIS_STATUS']  = 'PARKED'
            
            diffAngle = abs(self.xt - float(self.ctlFvars['ATDSIS_AZHOME']))
            #print('Difference in current and home position:', diffAngle)

            if diffAngle <= 0.25: 
                print('\nATDSIS Parked in Home position...')
                
            else:
                self.homeATDSIS()

    def calATDSIS(self):

        if self.TCPflg: 
            self.atdsis['ATDSIS_STATUS']  = 'ALIGNING'

        cal_offsets = np.arange(-25.,30.,2.5)
        
        cal_anin1   = []

        print('\nStarting Calibration...')
        for cal_ in cal_offsets:

            print('\n***********Calibration offset: {:.2f}****************\n'.format(cal_))

            crntdate     = dt.datetime.now(dt.timezone.utc)
            sunAz,sunEl  = sunAzEl(float(self.ctlFvars['ATDSIS_LAT']), float(self.ctlFvars['ATDSIS_LON']), float(self.ctlFvars['ATDSIS_ELEVATION']), dateT=crntdate,surfP=None,surfT=None,vecFlg=False)
            
            sza          = 90. - sunEl

            self.atdsis['ATDSIS_EPHAZI']    = sunAz
            self.atdsis['ATDSIS_EPHSZA']    = sza
            self.atdsis['ATDSIS_CRNTDATE']  = crntdate

            offset       = float(self.ctlFvars['ATDSIS_AZOFFSET']) + cal_
            
            self.MoveAbsWait(sunAz, Zero_X=offset)

            self.readSensor()
            sleep(2)
            cal_anin1.append(float(self.atdsis['ATDSIS_ANIN1(0X2314.07)']))

            sleep(1)
        
        cal_anin1   = np.asarray(cal_anin1)
        cal_offsets = np.asarray(cal_offsets) 

        inds_max  = np.where(cal_anin1 == np.max(cal_anin1))[0]
        
        fig, ax = plt.subplots(figsize=(6, 7))

        ax.plot(cal_offsets, cal_anin1, markersize=4, color='k', linewidth=1)            
        ax.scatter(cal_offsets, cal_anin1, facecolors='white',  s=50, color='black', zorder=2,  marker='o')
        #ax.errorbar(diff_mean, fts_alt_2, xerr=ac_prf_e_temp,  marker='o',  ms=0, ls='none', color='k', zorder=2)

        ax.axvline(x=0,color='gray', linestyle='--')
        
        ax.tick_params(labelsize=14)
        ax.grid(True)
        ax.set_xlabel('Rel. Offset [deg]', fontsize = 16)
        ax.set_ylabel('AnIn_1 [a.u]', fontsize = 16)
        #ax.set_xlim(-10,10)
        ax.text(0.05, 0.95, 'Offset  = {:.2f} (deg)'.format(cal_offsets[inds_max[0]]), va='center',transform=ax.transAxes,fontsize=10)
        
        fig.subplots_adjust(left=0.15)

        datestr, timestr = getDTstr(crntdate)

        ckDirMk(self.DataDir + datestr)
        plt.savefig(self.DataDir + datestr+'\\ATDSIS_Cal_{}.png'.format(crntdate.strftime('%Y%m%d_%H%M%S')), bbox_inches='tight', pad_inches=0.04)
        #plt.show(block=False)


        print('\n***********Final Calibration ****************\n'.format(cal_))
        print('\nOffset: {:.2f} (deg)\n'.format(cal_offsets[inds_max[0]]))
        #print('Figure: {}'.format(self.DataDir + datestr+'\\ATDSIS_Cal_{}.png'.format(crntdate.strftime('%Y%m%d_%H%M%S'))))
        print('\nFigure: {}\\ATDSIS_Cal_{}.png'.format(self.DataDir + datestr, crntdate.strftime('%Y%m%d_%H%M%S')))
        print('\n********************************************')



    def readSensor(self):

        sza_rad = math.radians(self.atdsis['ATDSIS_EPHSZA'])

        try:
            AnIn_1 = self.ReadAnalogIn(address=0x2313, subindex=0x04, node = b'\x01')
            print('\nAnalog Input 1 (0X2313x04): {}'.format(AnIn_1))
            self.atdsis['ATDSIS_ANIN1(0X2313.04)'] = float(AnIn_1)/1000. *-1 
            self.atdsis['ATDSIS_ANIN1(0X2313.04)_SCALED'] = float(AnIn_1)/1000./np.cos(sza_rad) *-1
        except: 
            print('Error 1')
            pass
            #print(struct.unpack('<f', AnIn_1) )
            #print(struct.unpack('>f', AnIn_1) )


        try:
            AnIn_2 = self.ReadAnalogIn(address=0x2313, subindex=0x14, node = b'\x01')
            print('\nAnalog Input 2 (0X2313.14): {}'.format(AnIn_2))
            self.atdsis['ATDSIS_ANIN2(0X2313.14)'] = float(AnIn_2)/1000. *-1
            self.atdsis['ATDSIS_ANIN2(0X2313.14)_SCALED'] = float(AnIn_2)/1000./np.cos(sza_rad) *-1
           #print(struct.unpack('<f', AnIn_2) )
           #print(struct.unpack('>f', AnIn_2) )
        except: 
            print('Error 2')
            pass


        #------------
        try:
            AnIn_1 = self.ReadAnalogIn(address=0x2314, subindex=0x07, node = b'\x01')
            print('\nAnalog Input 1 (0X2314.07): {}'.format(AnIn_1))
            self.atdsis['ATDSIS_ANIN1(0X2314.07)'] = float(AnIn_1)/1000. *-1
            self.atdsis['ATDSIS_ANIN1(0X2314.07)_SCALED'] = float(AnIn_1)/1000./np.cos(sza_rad) *-1
           #print(struct.unpack('<f', AnIn_1) )
           #print(struct.unpack('>f', AnIn_1) )
        except:
            print('Error 3')
            pass

        try:
            AnIn_2 = self.ReadAnalogIn(address=0x2314, subindex=0x08, node = b'\x01')
            print('\nAnalog Input 2 (0X2314.08): {}'.format(AnIn_2))
            self.atdsis['ATDSIS_ANIN2(0X2314.08)'] = float(AnIn_2)/1000. *-1
            self.atdsis['ATDSIS_ANIN2(0X2314.08)_SCALED'] = float(AnIn_2)/1000./np.cos(sza_rad) *-1
           #print(struct.unpack('<f', AnIn_2) )
           #print(struct.unpack('>f', AnIn_2) )
        except:
            print('Error 4')
            pass

    def logATDSIS(self):
        #----------------------------------
        # data[1] = Time Stamp
        # data[2] = Ephemeris Elevation Angle
        # data[3] = Elevation Angle Offset
        # data[4] = Ephemeris Azimuth Angle
        # data[5] = Azimuth Angle Offset
        #----------------------------------

        datestr, timestr = getDTstr(self.atdsis['ATDSIS_CRNTDATE'] )

        ckDirMk(self.DataDir + datestr)
        
        logFile        = self.DataDir + datestr + "/atdsis.log"
       
        #----------------------------------------------------
        # Convert tracker coordinates to absolute coordinates
        # Add offsets Tracker is not correctly aligned
        #----------------------------------------------------
        #trackerAz = self.tracker_to_abs_Az(trackerAz+self.ctlFile["AzOffSet"])

        #-----------------------------------------
        # Check if Measurement summary file exists
        #-----------------------------------------
        if ckDir(self.DataDir + datestr):
            if not ckFile(logFile):
                with open(logFile,'w') as fopen:
                    fopen.write("{0:<10s} {1:>10s} {2:>15s} {3:>15s} {4:>15s} {5:>15s} {6:>15s} {7:>15s} {8:>15s} {9:>15s} {10:>15s} {11:>15s} \n".format("ATDSIS_DATE","ATDSIS_TIME", "ATDSIS_EPHSZA","ATDSIS_EPHAZI", "ATDSIS_MOTAZI", "ATDSIS_ANIN1(0X2314.07)", "ATDSIS_ANIN2(0X2314.08)", "ATDSIS_ANIN1(0X2313.04)", "ATDSIS_ANIN2(0X2313.14)", "SZA_MAX", "AZOFFLIM1", "AZOFFLIM2" ))
                    fopen.write("{0:<10s} {1:>10s} {2:>14s} {3:>15s} {4:>15s} {5:>15s} {6:>15s} {7:>15s} {8:>15s} {9:>15s} {10:>15s} {11:>15s} \n".format(datestr,timestr, str(round(self.atdsis['ATDSIS_EPHSZA'],3)),  str(round(self.atdsis['ATDSIS_EPHAZI'],3)), str(round(self.atdsis['ATDSIS_MOTAZI'],3)), str(round(self.atdsis['ATDSIS_ANIN1(0X2314.07)'],3)),  str(self.atdsis['ATDSIS_ANIN2(0X2314.08)']), str(round(self.atdsis['ATDSIS_ANIN1(0X2313.04)'],3)),  str(self.atdsis['ATDSIS_ANIN2(0X2313.14)']), str(self.ctlFvars['ATDSIS_SZAMAX']), str(self.ctlFvars['ATDSIS_AZSOFTLIM1']), str(self.ctlFvars['ATDSIS_AZSOFTLIM2'])  ))
            else:   
                with open(logFile,'a') as fopen:
                    fopen.write("{0:<10s} {1:>10s} {2:>14s} {3:>15s} {4:>15s} {5:>15s} {6:>15s} {7:>15s} {8:>15s} {9:>15s} {10:>15s} {11:>15s}\n".format(datestr,timestr, str(round(self.atdsis['ATDSIS_EPHSZA'],3)),  str(round(self.atdsis['ATDSIS_EPHAZI'],3)), str(round(self.atdsis['ATDSIS_MOTAZI'],3)), str(round(self.atdsis['ATDSIS_ANIN1(0X2314.07)'],3)),  str(round(self.atdsis['ATDSIS_ANIN2(0X2314.08)'],3)), str(round(self.atdsis['ATDSIS_ANIN1(0X2313.04)'],3)),  str(self.atdsis['ATDSIS_ANIN2(0X2313.14)']), str(self.ctlFvars['ATDSIS_SZAMAX']), str(self.ctlFvars['ATDSIS_AZSOFTLIM1']), str(self.ctlFvars['ATDSIS_AZSOFTLIM2'])  ))
                
        #---------------------------------------------
        # Temprorary Store last instance in dictionary
        #---------------------------------------------
        #if self.TCPflg:
        #    mssg = "TRACKER_ELEVATION {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20}\n".format(crntT,trackerEl,ephemEl,np.abs(trackerEl-ephemEl)/ephemEl)
        #    msg2 = "TRACKER_AZIMUTH {0:%Y%m%d.%H%M%S} {1:20} {2:20} {3:20}\n".format(crntT,trackerAz,ephemAz,np.abs(trackerAz-ephemAz)/ephemAz)

        #    self.setParam(mssg)
        #    self.setParam(msg2)

    def sendData(self):
        #--------------------------
        # Write data to data server
        #--------------------------
        if not self.atdsis:
            print("No data to send to TCP from atdsisNCAR...")
            return False

        for key in self.atdsis:
            message = key + " " + str(self.atdsis[key])
            self.setParam(message)

        #---------------------------------------------
        # Send time stamp of connection to data server
        #---------------------------------------------
        crntDateTime = dt.datetime.now(dt.timezone.utc)
        
    

if __name__ == "__main__":



	#--------------------------------
	# Retrieve command line arguments
	#--------------------------------
    #try:
    #    ctlFile  = sys.argv[1]
    #except:
    #    ctlFile  = "C:/bin/ops/FL0_Defaults.input"

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    # Edit here only
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    TCPflg  = True
    logFlg  = False
    calFlg  = False

    # #----------------------------
    # # Check existance of ctl file
    # #----------------------------
    ckFile(ctlFile,exitFlg=True)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cC?')
        argsFlg    = True

    except getopt.GetoptError as err: pass

    if argsFlg:
        for opt, arg in opts:
            # Check input file flag and path
            if opt.lower() == '-c':
                calFlg = True

            elif opt.lower() == '-?':
                usage()
                exit()  
            else:
                print ('Unhandled option: ' + opt)
                print (' Continuing....')


    # #-------------------------
    # # Import ctlFile variables
    # #-------------------------
    ctlFvars = mainInputParse(ctlFile)

    print("\nLocal input parameters:")
    for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']

	#----------------------------
	# Check existance of ctl file
	#----------------------------
    ckFile(ctlFile,exitFlg=True)

    #-------------------------
    # Import ctlFile variables
    #-------------------------
    ctlFvars  = mainInputParse(ctlFile)

    #-----------------------------
    # Initialize Controller Class
    #-----------------------------
    atdsis    = atdsisClass(ctlFvars, TCPflg=TCPflg)
    
    #-----------------------------
    # Initialize Controller/Motor
    #-----------------------------
    atdsis.initialize()

    atdsis.homeATDSIS()

    if calFlg: 
        print(20*'-')
        print('Performing Calibration')
        atdsis.calATDSIS()
        exit()

    catTime     = dt.time(hour=16, minute=0) 
    
    #def cal_job():
    #    schedule.every().day.at(str(catTime)).do(atdsis.calATDSIS())

    #cal_job()

    #-----------------------------
    # 
    #-----------------------------
    while True:

        #schedule.run_pending()

        print("\n"+"="*20+"\nTracking at {}\n".format(dt.datetime.now(dt.timezone.utc))+"="*20)
        atdsis.trackATDSIS()

        atdsis.readSensor()

        if TCPflg: atdsis.sendData()

        if logFlg: atdsis.logATDSIS()

        sleep(int(ctlFvars['ATDSIS_UPDATEINT']))

    atdsis.close()    #this command closes the port, make sure you do it before shutting down


       