#! C:\Users\bruker\AppData\Local\Programs\Python\Python310\python3.exe
#----------------------------------------------------------------------------------------
# Name:
#        measureSet.py
#
# Purpose:
#       This does a set of measurements for filters 1,2,3,4,5,6,9.
#    
#
#
# Notes:
#       Adapted for xpm at FL0 (Updated FTS 120/125).
#       October, 2018
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
from ckpy_Onsala import ckscripts
import smtplib
from email.mime.text  import MIMEText
import getopt
import psutil
import subprocess
from remoteData       import FTIRdataClient

from ckpy_Onsala import get_Pypid, startPy, killPy 

#import pydaq



def sendEmail(body_msg, subj_msg, ctlFvars ):

    msg            = MIMEText(body_msg)
    msg['From']    = ctlFvars['Email_from']
    msg['Subject'] = subj_msg

    s = smtplib.SMTP(ctlFvars['Local_Server'], int(ctlFvars['Local_port']))    

    toemails   = [onemail for onemail in ctlFvars["Email_to"].strip().split(",")]

    msg['To']     = ctlFvars['Email_to']

    s.sendmail(ctlFvars['Email_from'], toemails, msg.as_string())
    s.quit() 

def main(argv):

    #--------------------------------
    # Edit here only
    #--------------------------------
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    ckscriptsFlg = False
    argsFlg      = False
    ln2Flg       = False
    waitTime     = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'sS')
        argsFlg    = True

    except getopt.GetoptError as err: pass

    if argsFlg:
        for opt, arg in opts:
            # Check input file flag and path
            if opt.lower() == '-s':
                ckscriptsFlg = True
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

    ctlFvars      = mainInputParse(ctlFile)

    if ckscriptsFlg:
        ckscripts(ctlFile, ln2ResFlg= True)
        exit()

    #-------------------
    # Defaults from ctl file
    #-------------------
    if not ( ctlFvars['Dir_xpm'].endswith('\\') ): ctlFvars['Dir_xpm']         = ctlFvars['Dir_xpm'] + '\\'
    if not ( ctlFvars['Dir_WinData'].endswith('\\') ): ctlFvars['Dir_WinData'] = ctlFvars['Dir_WinData'] + '\\'


    macroInSb     = ctlFvars['macroInSb']
    macroMCT      = ctlFvars['macroMCT']
    xpmPath       = ctlFvars['Dir_xpm']
    dataPath      = ctlFvars['Dir_WinData']
    gainFlg       = ctlFvars['GainFlg']
    timeoutFlg    = ctlFvars['Opus_timeout']
    dataServer_IP = ctlFvars['FTS_DataServ_IP']
    portNum       = ctlFvars['FTS_DataServ_PORT']
    BufferSize    = ctlFvars['FTS_DATASERV_BSIZE']

    
    #-------------------
    # Get Inputs: filters to run, iterations, ln2 filling, tracker info, send email?
    #-------------------
    #fltrs = raw_input("Choose filter(s) to run (1,2,3,b,4,5,6,9,3,0,a) or press Enter for all filters: ")
    fltrs = input("Choose filter(s) to run (3,2,1,b,4,5,6,9,3,0,a) or press Enter for all filters: ")

    #if not fltrs: fltrs = ["1","2","3","b","4","5","6","9","3","0","a"]
    if not fltrs: fltrs = ["3","2","1","b","4","5","6","9","3","0","a"]
    else:  fltrs  = [i.strip() for i in fltrs.strip().split(",")]  

        
    iters = input("Enter number of sets to do:")
    try:
        iters = int(iters)
    except: 
        print('Error, try again:')
        iters = input("Enter number of sets to do:")
        iters = int(iters)

    #-------------------
    # Ask if LN2 filling
    #-------------------
    #LN2ID    = input("LN2 Filling? press Enter for False or choose y=yes:")
    #if LN2ID: ln2Flg = True
    #else:     ln2Flg = False
    
    #-------------------
    # Ask if close tracker when done
    #-------------------
    #seekerID = input("Close hatch and power down tracker after set(s)? press Enter for False or choose y=yes: ")
    #if seekerID: seekerFlg = True
    #else:        seekerFlg = False

    #-------------------
    # Ask if send email when done
    #-------------------
    emaiID = input("Send email when done? press Enter for False or choose y=yes:")
    if emaiID: emailFlg = True
    else:      emailFlg = False

    #-------------------
    # Ask if wait N minutes before start
    #-------------------
    waitID = input("Wait N minutes before start observations: press Enter for False or choose minutes:")
    if waitID:  waitFlg = int(waitID)
    else:       waitFlg = False

    if waitID: 
        print('\nwaiting...')
        sleep(waitFlg*60)


    #----------------------------------
    # Check if opusIO and remoteData are running, if not start them
    #----------------------------------
    ckscripts(ctlFile)
    if ckscriptsFlg: exit()
    
    #----------------------------------
    # Initiate remote data client class
    #----------------------------------
    dataServer = FTIRdataClient(TCP_IP=dataServer_IP,TCP_Port=portNum,BufferSize=BufferSize)

    #----------------------------------
    # if LN2 filling
    #----------------------------------
    if ln2Flg:
        print ("\nAttemping to fill LN2 for {} minutes".format(ctlFvars['LN2_FILL_DUR']))
        subprocess.call("python3 {}ln2.py -ff -t{}".format(bin_Path,ctlFvars['LN2_FILL_DUR']), shell=False)
        #subprocess.call("python3 C:\\bin\\ln2.py -ff -t{}".format(ctlFvars['LN2_FILL_DUR']), shell=False)


    #----------------------------------
    # check tracker
    #----------------------------------
    #print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
    #subprocess.call("python3 {}seeker.py -c".format(bin_Path), shell=False)


    # hatchFlg   = dataServer.getParam("TRACKER_STATUS")
    # skpowerFlg = dataServer.getParam("TRACKER_POWER")

    # if (hatchFlg == 'OFF') or (skpowerFlg == 'OFF'):
    #     print("\nAttempting to open Seeker at FL0 at {0:} LT".format(dt.datetime.now()))
    #     #subprocess.call("python3 C:\\bin\\seeker.py -f ON", shell=False)
    #     subprocess.call("python3 {}seeker.py -f ON".format(bin_Path), shell=False)

    #     hatchFlg   = dataServer.getParam("TRACKER_STATUS")
    #     skpowerFlg = dataServer.getParam("TRACKER_POWER")
    # else:
    #     print("\nSeeker hatch is open at FL0 at {0:} LT".format(dt.datetime.now()))

    #----------------------------------
    # if LN2 filling wait a bit so DTC get stable
    #----------------------------------
    if ln2Flg: 
        print ("\nWaiting a couple of minutes so DTC are stable with the recent LN2 filling")
        sleep(120)
    else: sleep(2) 


    print("\nSending email with Measurement Set info at {0:} LT".format(dt.datetime.now()))

    strFltrs = ' '.join(str(s) for s in fltrs)
    
    msg = ("----------------------------Measurement DATA------------------------\n\n" +                           
                   "FILTERS             = {0:>15}\n".format(strFltrs)                   +                 
                   "ITERATIONS          = {0:>15}\n".format(iters)                       +
                   "TRACKER_STATUS      = {0:>15}\n".format(hatchFlg)                    +
                   "TRACKER_POWER       = {0:>15}\n".format(skpowerFlg)                  +
           "---------------------------------------------------------------------\n")
    
    Subject = "Measurement set starting at FL0 at {0:} LT".format(dt.datetime.now())

    sendEmail(msg, Subject, ctlFvars)

    #------------------------------------
    # Loop through iterations and filters
    #------------------------------------
    for i in range(iters):
        for fltr in fltrs:

            tic = timeit.default_timer()
            
            #---------------------------
            # Determine if taking a scan
            #---------------------------
            while True:

                opus_status = dataServer.getParam("OPUS_STATUS")
                #print ('\nOPUS STATUS         = ', opus_status)
               
                if opus_status.upper().replace(" ", "") == "SCANNING":
                    print ("Waiting for OPUS to finish")
                    sleep(10)
                    continue

                else:
                    break

            #---------------------------
            # Check Bruker DTC, if error fill with ln2
            #---------------------------
            detector_status = dataServer.getParam("BRUKER_DETECTORS")
            #print 'BRUKER DETECTORS    = ', detector_status
            if detector_status.upper().replace(" ", "") != "OK":
                print ("\nBruker DTC error")

                #print ("\nLN2 filling may be needed . Attemping to fill LN2 for {} minutes".format(ctlFvars['LN2_FILL_DUR']))
                #subprocess.call("python3 C:\\bin\\ln2.py -ff -t{}".format(ctlFvars['LN2_FILL_DUR']), shell=False)
                #subprocess.call("python3 {}ln2.py -ff -t{}".format(bin_Path, ctlFvars['LN2_FILL_DUR']), shell=False)

            #---------------------------
            # Check again Bruker DTC, if error close seeker
            #---------------------------
            detector_status = dataServer.getParam("BRUKER_DETECTORS")

            if detector_status.upper().replace(" ", "") != "OK":
                print ("\nStill Bruker DTC error")
                print ("\nAttempting to close tracker")

                #subprocess.call("python3 C:\\bin\\seeker.py -f off", shell=False)
                # subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)

                # hatchFlg   = dataServer.getParam("TRACKER_STATUS")
                # skpowerFlg = dataServer.getParam("TRACKER_POWER")
                # sleep(2)

                # msg = ("----------------------------Measurement Update-------------------\n\n" +
                #        "Currenly FTIR is trying to Measure\n"                                  +
                #        "BRUKER DETECTORS    = {0:}\n".format(detector_status)                  +
                #        "TRACKER_STATUS      = {0:}\n".format(hatchFlg)                         +
                #        "TRACKER_POWER       = {0:}\n".format(skpowerFlg)                       +
                #        "---------------------------------------------------------------------\n")

                # Subject = "Bruker DTC Error at FL0 at {0:} LT".format(dt.datetime.now())

                # sendEmail(msg, Subject, ctlFvars)
                # exit()

            
            #---------------------------
            # Check Wind
            #---------------------------
            # Wind_status = dataServer.getParam("ATM_WIND_SPEED")

            # if float(Wind_status[0:3]) > float(ctlFvars['HIGH_WIND_SPEED_LIMIT']):

            #     print('\nHigh Wind Speed Detected!!!\n')

            #     #subprocess.call("python3 C:\\bin\\seeker.py -f off", shell=False)
            #     subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)
            #     sleep(2)

            #     print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
            #     #subprocess.call("python3 C:\\bin\\seeker.py -c -k", shell=False)
            #     subprocess.call("python3 {}seeker.py -c -k".format(bin_Path), shell=False)
            #     sleep(2)

            #     hatchFlg   = dataServer.getParam("TRACKER_STATUS")
            #     skpowerFlg = dataServer.getParam("TRACKER_POWER")

            #     msg = ("----------------------------Measurement Update------------------------\n" +
            #           "FTIR (FL0) is currently measuring...\n"                                    +  
            #           "High Wind Speed detected --> Attempting to close the hatch....\n"          +             
            #           "WIND_SPEED          = {0:}\n".format(Wind_status)                          +          
            #           "TRACKER_STATUS      = {0:}\n".format(hatchFlg)                             +
            #           "TRACKER_POWER       = {0:}\n".format(skpowerFlg)                           +
            #           "---------------------------------------------------------------------\n")

            #     Subject = "High Wind Speed at FL0 at {0:} LT".format(dt.datetime.now())

            #     sendEmail(msg, Subject, ctlFvars)

            #     exit()

            #-------------------------
            # Determine data directory
            #-------------------------
            crntdate     = dt.datetime.utcnow()
            crntdateStr  = "{0:4}{1:02}{2:02}".format(crntdate.year,crntdate.month,crntdate.day)
            #datadir      = dataPath + "\\" + crntdateStr
            datadir      = dataPath + crntdateStr

            ckDirMk(datadir)
    
            #-------------------
            # Determine xpm name
            #-------------------
            if fltr != "6":
                xpmName     = "s{}ifml1a.xpm".format(fltr)
                timeout     = timeoutFlg
                macroFname  = macroInSb
            else:
                xpmName     = "s6hfml1a.xpm"
                timeout     = r"650"
                macroFname  = macroMCT
                   
            xpmFname = xpmPath + xpmName
            
            #-----------------------
            # Compose command string
            #-----------------------
            cmd = "OPUS_CMND TAKESCAN "+macroFname+" "+xpmFname+" "+datadir+" "+timeout+" "+gainFlg
            
            #----------------------------------
            # Send command and wait for results
            #----------------------------------
            print ("\nTaking scan for filter {} for set {}".format(fltr, fltrs))
            print ("Iteration Number {} out of {}".format(i+1, iters))

            dataServer.setParam(cmd)
            
            while True:
                doneFlg = dataServer.getParam("OPUS_CMND")
                if doneFlg != "FREE":
                    sleep(10)
                    continue
                else:
                    sleep(2)
                    scanRslts = dataServer.getParam("OPUS_LASTSCAN")
                    print ("Results for filter {0:} = {1:}".format(fltr,scanRslts))
                    
                    toc  = timeit.default_timer()
                    fsec = toc - tic #elapsed time in seconds
                    #print "Seconds waiting for filter {0:} = {1:.3f}".format(fltr,fsec)

                    break
        
        sleep(waitTime)

    print("\nSucessful Measurement set finished at FL0 at {0:} LT".format(dt.datetime.now()))

    # if seekerFlg: 
    #     print("\nClosing Seeker at FL0 at {0:} LT".format(dt.datetime.now()))
    #     #subprocess.call("python3 C:\\bin\\seeker.py -f off", shell=False)
    #     subprocess.call("python3 {}seeker.py -f off".format(bin_Path), shell=False)
    #     sleep(2)

    #     print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
    #     #subprocess.call("python3 C:\\bin\\seeker.py -c -k", shell=False)
    #     subprocess.call("python3 {}seeker.py -c -k".format(bin_Path), shell=False)
    #     sleep(2)

    # else:
    #     print("\nChecking Seeker status at FL0 at {0:} LT".format(dt.datetime.now()))
    #     #subprocess.call("python3 C:\\bin\\seeker.py -c", shell=False)
    #     subprocess.call("python3 {}seeker.py -c".format(bin_Path), shell=False)
    #     sleep(2)

    # hatchFlg   = dataServer.getParam("TRACKER_STATUS")
    # skpowerFlg = dataServer.getParam("TRACKER_POWER")

    if emailFlg:
        print("\nSending email with summary at {0:} LT".format(dt.datetime.now()))
        
        msg = ("----------------------------Measurement DATA------------------------\n\n" +                           
                       "FILTERS             = {0:>12s}\n".format(strFltrs)                   +                 
                       "ITERATIONS          = {0:}\n".format(iters)                       +
               "---------------------------------------------------------------------\n")
        
        Subject = "Measurement set finished at FL0 at {0:} LT".format(dt.datetime.now())

        sendEmail(msg, Subject, ctlFvars)

      
if __name__ == "__main__":
    main(sys.argv[1:])
