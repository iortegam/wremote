#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        dispatch.py
#
# Purpose:
#       Autonomous control for FTS observation at FL0.
#    
#
#
# Notes:
#       Adapted FOR FL0 (Updated FTS 120/125).
#       Aug, 2021
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
#-----------------------------------------------------------------------------------------


#---------------
# Import modules
#---------------	
from time       import sleep
import datetime as dt
import sys
import socket
from trackerUtils     import *
import timeit
from ckpy import ckscripts
import smtplib
from email.mime.text  import MIMEText
import getopt
import psutil
import subprocess
import ephem as ep

#import ln2

from remoteData       import FTIRdataClient
from ckpy import get_Pypid, startPy, killPy 

import time
import schedule
from dateutil import tz
import math
#import pydaq

def usage():
    ''' Prints to screen standard program usage'''
    print ( '\ndispatch.py -s  -?\n\n'
            '  -f <f, s, r or q>                      : Optional Flag for main command: f (fill), s (stop), r (check), q (quit)\n'
            '  -t <int>                               : Optional time in minutes to fill\n'
            '  -?                                     : Show all flags\n')

def sendEmail(body_msg, subj_msg, ctlFvars ):

    msg            = MIMEText(body_msg)
    msg['From']    = ctlFvars['Email_from']
    msg['Subject'] = subj_msg

    s = smtplib.SMTP(ctlFvars['Local_Server'], int(ctlFvars['Local_port']))    

    toemails   = [onemail for onemail in ctlFvars["Email_to"].strip().split(",")]

    msg['To']     = ctlFvars['Email_to']

    s.sendmail(ctlFvars['Email_from'], toemails, msg.as_string())
    s.quit() 

def ln2Filling(bin_path, duration, logFile=False):

    print ("\nAttemping to fill LN2 for {} minutes".format(duration))
    #subprocess.call("python3 {}ln2.py -ff -t{}".format(bin_path,duration), shell=False)
    if logFile:
        logFile.info('Filling LN2 for {} minutes'.format(duration))


def main(argv):
    
    # Edit here only
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    ckscriptsFlg = False
    argsFlg      = False
    iterFlg      = False
    cmdFlg       = False
    emailFlg     = True
    iters        = False
 
    ln2Flg       = False   # fill ln2
    seekerFlg    = False   # close hatch after set
    waitFlg      = False   # wait N seconds/minutes to start obs
    logFile      = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:sl?')
        argsFlg    = True

    except getopt.GetoptError as err: pass

    if argsFlg:
        for opt, arg in opts:
            # Check input file flag and path
            if opt.lower() == '-s':
                ckscriptsFlg = True

            elif opt.lower() == '-f':
               
                cmd    = arg
                cmdFlg = True

                if cmd.upper() == 'OBS' or cmd.upper() == 'NOBS': pass
                else:
                    usage()
                    exit()

            elif opt.lower() == '-?':
                usage()
                exit() 

            elif opt.lower() == '-l':
                logFile  = True
                 

            else:
                print ('Unhandled option: ' + opt)
                print (' Continuing....')

    # #----------------------------
    # # Check existance of ctl file
    # #----------------------------
    ckFile(ctlFile,exitFlg=True)

     # #-------------------------
    # # Import ctlFile variables
    # #-------------------------
    ctlFvars = mainInputParse(ctlFile)

    print("\nLocal input parameters:")
    for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))
    print('\n')

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']

    #ctlFile       = "C:/bin/ops/FL0_Defaults.input"
    ctlFvars      = mainInputParse(ctlFile)

    if ckscriptsFlg:
        ckscripts(ctlFile, ln2ResFlg= True)
        exit()

    if logFile:
        log_fpath = os.path.dirname(os.path.abspath(ctlFile)) 

        if not( log_fpath.endswith('/') ): log_fpath = log_fpath + '\\'

        log_fname = log_fpath + 'dispatch.log'

        if ckFile(log_fname): mode = 'a+'
        else: mode = 'w'

        logFile = logging.getLogger('1')
        logFile.setLevel(logging.INFO)
        hdlr1   = logging.FileHandler(log_fname,mode=mode)
        fmt1    = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%a, %d %b %Y %H:%M:%S')
        hdlr1.setFormatter(fmt1)
        logFile.addHandler(hdlr1)  

    
    #-------------------
    # Defaults from ctl file
    #-------------------
    if not ( ctlFvars['Dir_xpm'].endswith('\\') ): ctlFvars['Dir_xpm']         = ctlFvars['Dir_xpm'] + '\\'
    if not ( ctlFvars['Dir_WinData'].endswith('\\') ): ctlFvars['Dir_WinData'] = ctlFvars['Dir_WinData'] + '\\'

    if not cmdFlg:
        #-------------------
        # Get filters to run
        #-------------------
        fltrs = input("Choose filter(s) to run (1,2,3,b,4,5,6,9,3,0,a) or press Enter for all filters: ")

        if not fltrs: fltrs = ["1","2","3","b","4","5","6","9","3","0","a"]
        else:  fltrs  = [i for i in fltrs.strip().split(",")]  
            
        iters   = input("Enter number of sets to do: ")
        try:
            iters = int(iters)
        except: 
            print('Error, try again:')
            iters = input("Enter number of sets to do:")
            iters = int(iters)
        
        iterFlg = True

        LN2ID    = input("LN2 Filling? press Enter for False or choose y=yes:")
        if LN2ID: ln2Flg = True

        seekerID = input("Close hatch and power down tracker after set(s)? press Enter for False or choose y=yes: ")
        if seekerID: seekerFlg = True

        emaiID = input("Send email when done? press Enter for False or choose y=yes:")
        if emaiID: emailFlg = True
        else:      emailFlg = False

        waitID = input("Wait N minutes before start observations: press Enter for False or choose minutes:")
        if waitID:  waitFlg = int(waitID)

        if waitID: 
            print('\nwaiting...')
            sleep(waitFlg*60)

    else:

        fltrs    = [i for i in ctlFvars['Opus_fltrs'].strip().split(",")] 

    if logFile: 
        logFile.info('**************** Starting Dispatch.py ***********************')
        logFile.info('CMD: {}'.format(cmd.upper()))
    
    #-------------------
    # Defaults from ctl file
    #-------------------
    macroInSb     = ctlFvars['macroInSb']
    macroMCT      = ctlFvars['macroMCT']
    xpmPath       = ctlFvars['Dir_xpm']
    dataPath      = ctlFvars['Dir_WinData']
    gainFlg       = ctlFvars['GainFlg']
    timeoutFlg    = ctlFvars['Opus_timeout']
    dataServer_IP = ctlFvars['FTS_DataServ_IP']
    portNum       = ctlFvars['FTS_DataServ_PORT']
    BufferSize    = ctlFvars['FTS_DATASERV_BSIZE']

    #----------------------------------
    # Check if opusIO and remoteData are running, if not start them
    #----------------------------------
    #ckscripts(ctlFile)
    if ckscriptsFlg: exit()
    
    #----------------------------------
    # Initiate remote data client class
    #----------------------------------
    dataServer = FTIRdataClient(TCP_IP=dataServer_IP,TCP_Port=portNum,BufferSize=BufferSize)

    if not cmdFlg:

        if ln2Flg:
            print ("\nAttemping to fill LN2 for {} minutes".format(ctlFvars['LN2_FILL_DUR']))
            subprocess.call("python3 {}ln2.py -ff -t{}".format(bin_Path,ctlFvars['LN2_FILL_DUR']), shell=False)
            
            print ("\nWaiting a bit so DTC are stable with the recent LN2 filling")
            sleep(180)

        print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
        subprocess.call("python3 {}seeker.py -c".format(bin_Path), shell=False)

        hatchFlg   = dataServer.getParam("TRACKER_STATUS")
        skpowerFlg = dataServer.getParam("TRACKER_POWER")

        if (hatchFlg == 'OFF') or (skpowerFlg == 'OFF'):
            print("\nAttempting to open Seeker at FL0 at {0:} LT".format(dt.datetime.now()))
            subprocess.call("python3 {}seeker.py -f ON".format(bin_Path), shell=False)

            hatchFlg   = dataServer.getParam("TRACKER_STATUS")
            skpowerFlg = dataServer.getParam("TRACKER_POWER")
        else:
            print("\nSeeker hatch is open at FL0 at {0:} LT".format(dt.datetime.now()))


        print("\nSending email with dispatch set info at {0:} LT".format(dt.datetime.now()))

        strFltrs = ' '.join(str(s) for s in fltrs)
        
        msg = ("----------------------------Measurement DATA------------------------\n\n" +  
                       "FILTERS             = {0:>15}\n".format(strFltrs)                   +                 
                       "ITERATIONS          = {0:>15}\n".format(iters)                       +
                       "TRACKER_STATUS      = {0:>15}\n".format(hatchFlg)                    +
                       "TRACKER_POWER       = {0:>15}\n".format(skpowerFlg)                  +
               "---------------------------------------------------------------------\n")
        
        Subject = "Dispatch set starting at FL0 at {0:} LT".format(dt.datetime.now())

        sendEmail(msg, Subject, ctlFvars)

   
    from_zone = tz.tzutc()
    to_zone   = tz.gettz('America/Denver')

    if cmdFlg:
        if cmd.upper() == 'OBS':

            crntdate    = dt.datetime.utcnow()
            utc         = crntdate.replace(tzinfo=from_zone)

            # Convert time zone
            crntdate_lt = utc.astimezone(to_zone)
            #print(crntdate_lt.utcoffset())

            utc         = utc.replace(tzinfo=None)
            crntdate_lt = crntdate_lt.replace(tzinfo=None)
            offset      = int((utc - crntdate_lt).total_seconds() / 60 /60)
            # Set the time for the function to run
            ln2Time     = dt.time(hour=6+offset, minute=0) 

            def ln2_job():
                schedule.every().day.at(str(ln2Time)).do(ln2Filling, bin_Path,ctlFvars['LN2_FILL_DUR'], logFile=logFile)
            
            # Schedule the job        
            ln2_job()
    
    # Initialize a variable to store the previous day
    previous_day   = dt.datetime.now().day
    NewDayFlg      = False
    N_iter         = 0

    ln2_N          = 0
    

    solar_lasttime = None
    solar_N        = 0
    solar          = []

    
    #------------------------------------
    # Loop through iterations and filters
    #------------------------------------
    while True:
       
        if cmd.upper() == 'OBS':
            schedule.run_pending()

        for fltr in fltrs:

            #-------------------------
            # Determine data directory
            #-------------------------
            crntdate     = dt.datetime.utcnow()
            crntdateStr  = "{0:4}{1:02}{2:02}".format(crntdate.year,crntdate.month,crntdate.day)
            datadir      = dataPath + "\\" + crntdateStr
            #NextDay_Date = crntdate + dt.timedelta(days=1)

            ckDirMk(datadir)

            current_day  = crntdate.day

            if current_day != previous_day:
                print("\nIt's a new day!")
                previous_day = current_day
                if logFile: logFile.info('************NEW DAY*****************')
            
            tic          = timeit.default_timer()

            sunAz,sunEl = sunAzEl(float(ctlFvars['ATDSIS_LAT']), float(ctlFvars['ATDSIS_LON']), float(ctlFvars['ATDSIS_ELEVATION']), dateT=crntdate,surfP=None,surfT=None,vecFlg=False)
            sza         = 90. - sunEl

            if sza >= 85.:
                print('\nzenith angle > 85 deg... waiting')
                sleep(20)
                continue

            print('\nAttempting taking spectra for filter {} at {}'.format(fltr, crntdate))


            #---------------------------
            # Determine if taking a scan
            #---------------------------
            # while True:

            #     opus_status = dataServer.getParam("OPUS_STATUS")
            #     #print ('\nOPUS STATUS         = ', opus_status)
               
            #     if opus_status.upper().replace(" ", "") == "SCANNING":
            #         print ("Waiting for OPUS to finish")
            #         sleep(10)
            #         continue

            #     else:
            #         break

            #-------------------
            # Include solar conditions here
            #-------------------
            if cmd.upper() == 'OBS':

                solar_status = dataServer.getParam("ATDSIS_STATUS")

                if solar_status == 'TRACKING':

                    while True:

                        crntdate     = dt.datetime.utcnow()

                        sunAz,sunEl = sunAzEl(float(ctlFvars['ATDSIS_LAT']), float(ctlFvars['ATDSIS_LON']), float(ctlFvars['ATDSIS_ELEVATION']), dateT=crntdate,surfP=None,surfT=None,vecFlg=False)
                        sza         = 90. - sunEl

                        if sza >= 85.:
                            print('\nzenith angle > 85 deg... waiting')
                            break

                        sza_rad = math.radians(sza)
                        
                        if solar_lasttime is None:
                            solar_lasttime = crntdate

                        solar_anin1 = float(dataServer.getParam("ATDSIS_ANIN1(0X2314.07)"))*-1 / np.cos(sza_rad)
                        solar.append(solar_anin1)

                        print('\nSolar Input 1                     : {:.2f}'.format(float(dataServer.getParam("ATDSIS_ANIN1(0X2314.07)"))*-1 ))
                        print('Solar Input 1 (scaled by cos(sza)): {:.2f}'.format(solar_anin1))
                        print('solar_N: ',solar_N)

                        if solar_N == 0:

                            print('Waiting for Good solar conditions within {} minutes'.format(ctlFvars['EXTERN_SOLAR_DELAY']))
                            sleep(5)
                           
                            if (crntdate - solar_lasttime) > dt.timedelta(minutes=int(ctlFvars['EXTERN_SOLAR_DELAY'])):
                                print('\n')
                                solar      = np.asarray(solar)
                                solar_mean = np.nanmean(solar)
                                solar_std  = np.nanstd(solar)

                                print('Solar Values from {} to {}'.format(solar_lasttime, crntdate))
                                print('Solar mean: {:.2f}'.format(solar_mean))
                                print('Solar std:  {:.2f}'.format(solar_std))

                                solar_lasttime = crntdate
                                solar          = []

                                if solar_mean >= float(ctlFvars['EXTERN_SOLAR_FRONT_MIN']):

                                    solar_N += 1
                                    if logFile: 
                                        logFile.info('Initial solar Conditions OK: {:.2f} a.u (scaled by cos(sza))'.format(solar_mean))
                                        logFile.info('sza (deg): {:.2f}, saa (deg): {:.2f}'.format(sza, sunAz))
                                    break

                        else:
                            solar          = []

                            if solar_anin1 >= solar_mean*0.95: 
                                print('\nGood solar conditions...')
                                break
                            else:
                                logFile.info('Solar Conditions not ok: {:.2f} a.u (scaled by cos(sza))'.format(solar_anin1))
                                solar_N  = 0

                else:
                    print('SOLAR_STATUS NOT OK')


            print('\nAfter Solar Conditions: OK')
            sleep(5)
            #exit()

            #---------------------------
            # Check Bruker DTC
            #---------------------------
        #     detector_status = dataServer.getParam("BRUKER_DETECTORS")
        #     #print 'BRUKER DETECTORS    = ', detector_status
        #     if detector_status.upper().replace(" ", "") != "OK":

        #         if ln2_N == 0:
                
        #             print ("\nBruker DTC error")
        #             print ("\nAttemping to fill LN2 for {} minutes".format(ctlFvars['LN2_FILL_DUR']))
        #             subprocess.call("python3 {}ln2.py -ff -t{}".format(bin_Path, ctlFvars['LN2_FILL_DUR']), shell=False)
        #             ln2_N += 1

        #     detector_status = dataServer.getParam("BRUKER_DETECTORS")

        #     if detector_status.upper().replace(" ", "") != "OK":
        #         print ("\nStill Bruker DTC error")
        #         print ("\nAttempting to close tracker")
                
        #         if not cmdFlg:

        #             subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)

        #             hatchFlg   = dataServer.getParam("TRACKER_STATUS")
        #             skpowerFlg = dataServer.getParam("TRACKER_POWER")
        #             dataServer.setParam("TRACKER_CMND CLOSE")

        #             sleep(2)

        #             msg = ("----------------------------Measurement Update-------------------\n\n" +
        #                    "Currenly FTIR is trying to Measure\n"                                  +
        #                    "BRUKER DETECTORS    = {0:}\n".format(detector_status)                  +
        #                    "TRACKER_STATUS      = {0:}\n".format(hatchFlg)                         +
        #                    "TRACKER_POWER       = {0:}\n".format(skpowerFlg)                       +
        #                    "---------------------------------------------------------------------\n")

        #             Subject = "Bruker DTC Error at FL0 at {0:} LT".format(dt.datetime.now())

        #             sendEmail(msg, Subject, ctlFvars)
        #             exit()

        #         if cmdFlg: continue

        #     #---------------------------
        #     # Check Wind
        #     #---------------------------
        #     Wind_status = dataServer.getParam("ATM_WIND_SPEED")

        #     if float(Wind_status[0:3]) > float(ctlFvars['HIGH_WIND_SPEED_LIMIT']):

        #         print('\nHigh Wind Speed Detected!!!\n')

        #         subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)
                
        #         hatchFlg   = dataServer.getParam("TRACKER_STATUS")
        #         skpowerFlg = dataServer.getParam("TRACKER_POWER")
        #         dataServer.setParam("TRACKER_CMND CLOSE")

        #         if not cmdFlg:

        #             msg = ("----------------------------Measurement Update------------------------\n" +
        #                   "FTIR (FL0) is currently measuring...\n"                                    +  
        #                   "High Wind Speed detected --> Attempting to close the hatch....\n"          +             
        #                   "WIND_SPEED          = {0:}\n".format(Wind_status)                          +          
        #                   "TRACKER_STATUS      = {0:}\n".format(hatchFlg)                             +
        #                   "TRACKER_POWER       = {0:}\n".format(skpowerFlg)                           +
        #                   "---------------------------------------------------------------------\n")

        #             Subject = "High Wind Speed at FL0 at {0:} LT".format(dt.datetime.now())

        #             sendEmail(msg, Subject, ctlFvars)

        #             exit()

        #         if cmdFlg: continue

        #     #-------------------
        #     # Include solar conditions here
        #     #-------------------
        #     # print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
        #     # subprocess.call("python3 {}seeker.py -c".format(bin_Path), shell=False)

        #     # hatchFlg   = dataServer.getParam("TRACKER_STATUS")
        #     # skpowerFlg = dataServer.getParam("TRACKER_POWER")


        #     # if (hatchFlg == 'OFF') or (skpowerFlg == 'OFF'):
        #     #     print("\nAttempting to open Seeker at FL0 at {0:} LT".format(dt.datetime.now()))
        #     #     subprocess.call("python3 {}seeker.py -f ON".format(bin_Path), shell=False)

        #     #     hatchFlg   = dataServer.getParam("TRACKER_STATUS")
        #     #     skpowerFlg = dataServer.getParam("TRACKER_POWER")
        #     # else:
        #     #     print("\nSeeker hatch is open at FL0 at {0:} LT".format(dt.datetime.now()))

    
        #     #-------------------
        #     # Determine xpm name
        #     #-------------------
        #     if fltr != "6":
        #         xpmName     = "s{}ifml1a.xpm".format(fltr)
        #         timeout     = timeoutFlg
        #         macroFname  = macroInSb
        #     else:
        #         xpmName     = "s6hfml1a.xpm"
        #         timeout     = r"650"
        #         macroFname  = macroMCT
                   
        #     xpmFname = xpmPath + "\\" + xpmName
            
        #     #-----------------------
        #     # Compose command string
        #     #-----------------------
        #     cmd = "OPUS_CMND TAKESCAN "+macroFname+" "+xpmFname+" "+datadir+" "+timeout+" "+gainFlg
            
        #     #----------------------------------
        #     # Send command and wait for results
        #     #----------------------------------
        #     print ("\nTaking scan for filter {} for set {}".format(fltr, fltrs))
        #     print ("Iteration Number {} out of {}".format(i+1, iters))

        #     dataServer.setParam(cmd)
            
        #     while True:
        #         doneFlg = dataServer.getParam("OPUS_CMND")
        #         if doneFlg != "FREE":
        #             sleep(10)
        #             continue
        #         else:
        #             sleep(2)
        #             scanRslts = dataServer.getParam("OPUS_LASTSCAN")
        #             print ("Results for filter {0:} = {1:}".format(fltr,scanRslts))
                    
        #             toc  = timeit.default_timer()
        #             fsec = toc - tic #elapsed time in seconds
        #             #print "Seconds waiting for filter {0:} = {1:.3f}".format(fltr,fsec)

        #             break
        
        # N_iter+= 1

        # if not cmdFlg:
        #     if N_iter >= iters: break


    # if not cmdFlg:
    #     print("\nSucessful Measurement set finished at FL0 at {0:} LT".format(dt.datetime.now()))

    #     if seekerFlg: 
    #         print("\nClosing Seeker at FL0 at {0:} LT".format(dt.datetime.now()))
    #         subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)
    #         sleep(2)

    #         print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
    #         subprocess.call("python3 {}seeker.py -c -k".format(bin_Path), shell=False)
    #         sleep(2)

    #     else:
    #         print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
    #         #subprocess.call("python3 C:\\bin\\seeker.py -c", shell=False)
    #         subprocess.call("python3 {}seeker.py -c".format(bin_Path), shell=False)
    #         sleep(2)

    #     hatchFlg   = dataServer.getParam("TRACKER_STATUS")
    #     skpowerFlg = dataServer.getParam("TRACKER_POWER")

    #     if emailFlg:
    #         print("\nSending email with summary at {0:} LT".format(dt.datetime.now()))
            
    #         msg = ("----------------------------Measurement DATA------------------------\n\n" +                           
    #                        "FILTERS             = {0:>12s}\n".format(strFltrs)                   +                 
    #                        "ITERATIONS          = {0:}\n".format(iters)                       +
    #                        "TRACKER_STATUS      = {0:}\n".format(hatchFlg)                    +
    #                        "TRACKER_POWER       = {0:}\n".format(skpowerFlg)                  +
    #                "---------------------------------------------------------------------\n")
            
    #         Subject = "Measurement set finished at FL0 at {0:} LT".format(dt.datetime.now())

    #         sendEmail(msg, Subject, ctlFvars)


      
if __name__ == "__main__":
    main(sys.argv[1:])
