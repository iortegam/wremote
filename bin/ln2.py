#! C:\Users\bruker\AppData\Local\Programs\Python\Python310\python3.exe
"""
File:                       ln2.py

Note: shebang works but you have to use >py ln2.py "flags""


Purpose:                   fill LN2 

Library Call Demonstrated:  mcculw.ul.a_in_scan() in Background mode with scan
                            option mcculw.enums.ScanOptions.BACKGROUND and, if
                            supported, mcculw.enums.ScanOptions.SCALEDATA

Purpose:                    Scans a range of A/D Input Channels and stores
                            the sample data in an array.

Demonstration:              Displays the analog input on up to four channels.

Other Library Calls:        mcculw.ul.win_buf_alloc()
                                or mcculw.ul.win_buf_alloc_32()
                                or mcculw.ul.scaled_win_buf_alloc()
                            mcculw.ul.win_buf_free()
                            mcculw.ul.get_status()
                            mcculw.ul.stop_background()
                            mcculw.ul.release_daq_device()

Special Requirements:       Device must have an A/D converter.
                            Analog signals on up to four input channels.
"""
from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from time import sleep
from ctypes import cast, POINTER, c_double, c_ushort, c_ulong

from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw.device_info import DaqDeviceInfo

from mcculw.enums import DigitalIODirection

try:
    from console_examples_util import config_first_detected_device
except ImportError:
    from .console_examples_util import config_first_detected_device

#---------------
# Import modules
#---------------
import sys
#import urllib2
import os
import socket
import select
import datetime       as     dt
from time             import sleep
from trackerUtils     import *
from remoteData       import FTIRdataClient
import numpy          as     np
import getopt
import time

from threading import Timer
from threading import Thread
import subprocess
import datetime as dt

import fl0d    
from ckpy import get_Pypid, startPy, killPy 

#---------------

def usage():
    ''' Prints to screen standard program usage'''
    print ( '\nln2.py -i <Ctlfile> -f <f,s, or q> -t <int> -?\n\n'
            '  -i <Ctlfile>                           : Optional Flag to specify ctl input file (Default is C:/bin/ops/FL0_Defaults.input\n'
            '  -f <f, s, or q>                        : Optional Flag for main command: f (fill), s (stop), q (quit)\n'
            '  -t <int or float>                      : Optional time in minutes to fill\n'
            '  -?                                     : Show all flags\n')

def tryopen(fname):
    ''' Try to open a file and read contents'''
    try:
        with open(fname, 'r' ) as fopen:
            return fopen.readlines()
    except IOError as errmsg:
        print (errmsg)
        return False

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


def getTS(crntTime):
        
    return "{0:%Y%m%d.%H%M%S}".format(crntTime)


# #'----------------------------------'
# # Get Python PIDs
# #'----------------------------------'
# def get_Pypid():

#     pids = {}

#     for proc in psutil.process_iter():
        
#         try:
#             _name = proc.name()
           
#             if _name in ['python.exe', 'python3.exe', 'Python.exe', 'Python3.exe']:
#                 try:
#                     cmd = proc.cmdline()
#                 except psutil.AccessDenied:
#                     continue
             
#                 if cmd[1].endswith('.py'):
#                     since = dt.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
#                     pids[proc.pid] = {'since': since, 'pid': proc.pid, 'name':cmd[1]}
       
#         except psutil.AccessDenied:
#             continue        
    
#     return pids


# #'----------------------------------'
# # Start a python script via .bat 
# #'----------------------------------'
# def startPy(pyScript, args=False):
#     #----------------------------------
#     # Get python PIDs
#     #----------------------------------
    
#     pids = get_Pypid()
  
#     #----------------------------------
#     # Get specific opusIO PID
#     #----------------------------------
    
#     for p in pids:
#         name = pids[p]['name']        
#         if name.strip().split('\\')[-1] == pyScript+'.py':
#             print(pyScript+'.py is already running... exiting')
#             exit()
 
#     print ("\nNo instances of {}.py found running!!".format(pyScript))

#     #--------------------------------------------
#     # Start remoteData.py
#     #--------------------------------------------
#     try:
#         print ('Starting {}.py...at {}'.format(pyScript, datetime.datetime.utcnow()))
#         if args: subprocess.call([r"C:\bin\{}.bat".format(pyScript),args], shell=True)
#         else:    subprocess.call([r"C:\bin\{}.bat".format(pyScript)], shell=True)
#         sleep(5)
#     except:
#         print ('Unable to re-start {}.py...at {}'.format(pyScript,datetime.datetime.utcnow()))


# def killPy(pyScript):

#     pids = get_Pypid()

#     for p in pids:
#         name = pids[p]['name']

#         if name.strip().split('\\')[-1] == pyScript+'.py':
#             print (pyScript+'.py is currently running ...at {}\n'.format(dt.datetime.utcnow()))
#             print('Killing current running {}.py program'.format(pyScript))
#             os.system("taskkill /F /T /PID {}".format(pids[p]['pid']))





class ln2Class(FTIRdataClient):

    def __init__(self,ctlFvars, TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=1024):

        self.TCPserverIP = TCP_IP_in
        self.ctlFvars    = ctlFvars
       

        FTIRdataClient.__init__(self,TCP_IP=TCP_IP_in,TCP_Port=TCP_Port_in,BufferSize=BufferSize_in)

        #---------------
        # Reading ctl file(s) (analog & digital)
        #---------------
        self.digitalgctl = fl0d.read_daqctl(ctlFvars['File_DigitalInput'])
       
        #---------------
        # Standard from DAQ python examples
        #---------------
        self.use_device_detection = True
        self.dev_id_list          = []
        self.board_num            = 0
        self.memhandle            = None
        
        if self.memhandle:
               # Free the buffer in a finally block to prevent a memory leak.
            ul.win_buf_free(self.memhandle)
        if self.use_device_detection:
            ul.release_daq_device(self.board_num)

        #ul.stop_background(self.board_num, FunctionType.AIFUNCTION)
        
        
        #try:
        if self.use_device_detection:
            config_first_detected_device(self.board_num, self.dev_id_list)

        self.daq_dev_info = DaqDeviceInfo(self.board_num)

        if not self.daq_dev_info.supports_digital_io:
            raise Exception('Error: The DAQ device does not support '
                            'digital I/O')


        print('\nActive DAQ device: ', self.daq_dev_info.product_name, ' (',
              self.daq_dev_info.unique_id, ')\n', sep='')

        #---------------
        # DIO info
        #---------------
        self.dio_info = self.daq_dev_info.get_dio_info()

        self.port = next((port for port in self.dio_info.port_info if port.supports_output),
                    None)

        if not self.port:
            raise Exception('Error: The DAQ device does not support '
                            'digital output')


        #if self.port.is_port_configurable:
        #    ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)
    
            
        #except Exception as e:
        #    print('\n', e)
        #finally:
        #    if self.use_device_detection:
        #        ul.release_daq_device(self.board_num)

    def power(self):
        print(30*'-')
        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)

        port_value = 0xFF
        #port_value = 1

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        #print('\nSeeker powering off at {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch          = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'LQDN2' ][0]
        
        #inds_logic  = [ci for ci, c in enumerate(self.digitalgctl[ch]) if c == cmd.upper()  ][0]
       
        #if inds_logic == 2:
        #    bit_value_1 = 1
        #    bit_value_2 = 0
        #elif inds_logic    == 3:
        
        bit_value_1 = 0
        bit_value_2 = 1

        bit_num   = int(self.digitalgctl[ch][0])
        #bit_value = 0
        #--------------------
        # Momentarily set digital output to high (0) to toggle relay state
        #--------------------
        print('\nSetting Momentarily power', self.port.type.name, 'bit', bit_num, 'to', bit_value_1)
        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_1)

        sleep(2)
        print('Switching Momentarily power', self.port.type.name, 'bit', bit_num, 'to', bit_value_2)
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_2)

        #msg = self.digitalgctl[ch][5] +' OFF'
        #self.setParam(msg)

        sleep(3)

    def ckpowerDIO(self):
        print(30*'-')
        #if self.port.is_port_configurable:
        #    ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.IN)

        # Get a value from the digital port
        #port_value = ul.d_in(self.board_num, self.port.type)

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\nChecking status of ln2 power dio (LQSN2) at {} UT...'.format(getDTstr(crntTime)[1]))

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'LQSN2' ][0]

        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = ul.d_bit_in(self.board_num, self.port.type, bit_num)

        # Display the port value
        #print(self.port.type.name, 'Value:', port_value)
        # Display the bit value
        print('Channel {} (LQSN2) Bit Value: {}'.format(bit_num, bit_value))

        #self.ckpowerDIO = bit_value

        sleep(1)

        if int(bit_value) == 0:
            return str('ON')
        elif int(bit_value) == 1:
            return str('OFF')

    def poweron(self):
        print(30*'-')
        port_value = 0xFF
        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\npower on: opening LN2 valve at {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'LQDN2' ][0]

        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = 0
       #print('Setting', self.port.type.name, 'bit', bit_num, 'to', bit_value)

        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value)

        msg = self.digitalgctl[ch][5] +' ON'
        self.setParam(msg)

        sleep(2)

    def poweroff(self):
        print(30*'-')
        port_value = 0xFF
        #port_value = 1

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\npower off: closing LN2 valve at {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'LQDN2' ][0]

        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = 1
        #print('Setting', self.port.type.name, 'bit', bit_num, 'to', bit_value)

        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value)

        msg = self.digitalgctl[ch][5] +' OFF'
        self.setParam(msg)

        sleep(2)

    def status(self):
        print(30*'-')
        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'LQDN2' ][0]

        dtc_status = self.getParam("BRUKER_DETECTORS")
        print('BRUKER_DETECTOR: {}'.format(dtc_status))
        dtc_status = self.getParam("BRUKER_MESSAGE")
        print('BRUKER_MESSAGE: {}'.format(dtc_status))
        dtc_status = self.getParam("BRUKER_INSTRUMENT_READY")
        print('BRUKER_INSTRUMENT_READY: {}'.format(dtc_status))
        dtc_status = self.getParam(self.digitalgctl[ch][5].upper())
        print(self.digitalgctl[ch][5].upper()+': {}'.format(dtc_status))

        crntTime   = dt.datetime.now(dt.timezone.utc)
        dtc_status = self.getParam('LN2_DEWAR_PRESSURE')
        print('LN2_DEWAR_PRESSURE: {} at {} UT'.format(dtc_status, getDTstr(crntTime)[1]))
    

def main():

    #--------------------------------
    # INPUTS
    #--------------------------------
    #ctlFile       = "C:/bin/ops/FL0_Defaults.input"

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    # Edit here only
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    # #----------------------------
    # # Check existance of ctl file
    # #----------------------------
    ckFile(ctlFile,exitFlg=True)

    # #-------------------------
    # # Import ctlFile variables
    # #-------------------------
    ctlFvars = mainInputParse(ctlFile)

    #print("\nLocal input parameters:")
    #for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']

    argsFlg      = False
    ln2durFlg    = False
    cmdFlg       = False
    MaxDur       = 10.       # Maximun number of minutes (Safety)


    #--------------------------------
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:t:s?')
        if len(opts) >=1: argsFlg    = True

    except getopt.GetoptError as err: pass

    if argsFlg:
        for opt, arg in opts:
            # Check input file flag and path

            if opt.lower() == '-f':
                if not arg or arg.startswith('-'):
                    usage()
                    exit()  
                cmd    = arg

                #if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q' or cmd.upper() =='R': pass
                if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q': pass
                else:
                    usage()
                    exit()

                cmdFlg = True

            elif opt.lower() == '-t':
                if not arg or arg.startswith('-'):
                    usage()
                    exit()  

                try: 
                    ln2dur     = float(arg) 
                    ln2durFlg  = True
                except ValueError:
                    print ("\nValueError! Duration of filling is not a float!.... exiting")
                    exit()

            elif opt.lower() == '-?':
                usage()
                exit()  
                
    else:
        if not cmdFlg:    
            #cmd    = raw_input("\nChoose F, S, R, or Q (FILL, STOP, CHECK OR QUIT):")
            cmd    = input("\nChoose F, S, or Q (FILL, STOP, OR QUIT):")

            #if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q' or cmd.upper() =='R': pass
            if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q': pass
            else:
                usage()
                exit()

            cmdFlg = True

            if cmd.upper() == 'Q': exit()

        if cmd.upper() == 'F':
            if not ln2durFlg: 
                ln2dur = raw_input("\nMinutes of Filling or Enter to skip and quit whenever:")
                if ln2dur: 
                    ln2dur     = float(ln2dur)
                    ln2durFlg  = True
                else:ln2durFlg = False


    if not cmdFlg:    
        #cmd    = raw_input("\nChoose F, S, R, or Q (FILL, STOP, CHECK OR QUIT):")
        cmd    = raw_input("\nChoose F, S, or Q (FILL, STOP, OR QUIT):")

        #if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q' or cmd.upper() =='R': pass
        if cmd.upper() == 'F' or cmd.upper() == 'S' or cmd.upper() =='Q': pass
        else:
            usage()
            exit()

    if cmd.upper() == 'Q': exit()

    
    
    # timeout = 10
    # t = Timer(timeout, print, ['Sorry, times up'])
    # t.start()
    # prompt = "You have %d seconds to choose the correct answer...\n" % timeout
    # answer = input(prompt)
    # t.cancel()

    # print(answer)

    # if not ln2durFlg: 
    #     ln2dur = raw_input('\nInput duration of filling in minutes:')
    #     if ln2dur: 
    #         try: 
    #             ln2dur     = float(ln2dur) 
    #             ln2durFlg  = True
    #         except ValueError:
    #             print ("\nValueError! Duration of filling is not a float!.... exiting")
    #             exit()
    #     else:
    #         ln2dur = raw_input("\nInput duration of filling in minutes::")
    #         try: 
    #             ln2dur     = float(ln2dur) 
    #             ln2durFlg  = True
    #         except ValueError:
    #             print ("\nValueError! Duration of filling is not a float!.... exiting")
    #             exit()


    if ln2durFlg:
        if ln2dur > MaxDur:
            print('\nDuration of filling is greater than current hardcoded maximum duration of {} min, exiting!'.format(MaxDur))
            exit()
    
    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile, exitFlg=True)

    ctlFvars      = mainInputParse(ctlFile)

    if cmd.upper() == 'F':
        print('\n'+60*'-')
        print('Command: Filling with LN2')
        if ln2durFlg:
            print('Time: {} Minutes'.format(ln2dur))
        else:
            print('Time of filling is not Included, Must be stopped Manually')
            print('For safety, if not stopped the system will stopped after the maximum number of {} minutes'.format(MaxDur))
        print(60*'-'+'\n')

    if cmd.upper() == 'S':
        print('\n'+60*'-')
        print('Command: Stop LN2 filling')
        print(60*'-'+'\n')

    #-----------------------------
    # Initialize ln2 class
    #-----------------------------
    ln2              = ln2Class(ctlFvars, TCP_IP_in=ctlFvars["FTS_DataServ_IP"], TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))
    
    ln2powerStatus   = ln2.ckpowerDIO() 
  
   
    if cmd.upper() == 'S': 
        if ln2powerStatus == 'OFF':
            print('\nLN2 power already OFF, exiting...')
            exit()
        else:
            print('\nLN2 power is ON,  Powering OFF & exiting......')
            ln2.power()
            exit()
    #elif cmd.upper() =='R':
    #    ln2.status()
    #    exit()

    # subprocess.call([r"C:\bin\ln2stop.bat",'5'], shell=True)

    #-----------------------------
    # kill ln2_scheduleStop.py
    #-----------------------------
    killPy('ln2Reset')

    while True:

        ln2powerStatus   = ln2.ckpowerDIO() 

        if cmd.upper() == 'F':

            if ln2powerStatus == 'OFF':
                print('\nLN2 power is OFF, Powering ON...')
                ln2.power()

                if ln2durFlg: 
                    print('\nFilling for {} minutes... then LN2 valve will close'.format(str(ln2dur)))
                    sleep(ln2dur*60.)
                    print('\nLN2 power is ON, Powering OFF & exiting...')
                    ln2.power()

                    startPy('ln2Reset')
                    exit()

                else:
                    print('\nFilling and waiting for command...')

                    startPy('ln2stop', args=MaxDur)
                    #print ("\nLaunching ln2stop.py in case an overtime of {} minutes".format(MaxDur))
                    #subprocess.call([r"C:\bin\ln2stop.bat",MaxDur], shell=True)

                    #cmd    = raw_input("\nChoose F, S, R, or Q (FILL, STOP, CHECK OR QUIT):")
                    cmd    = raw_input("\nChoose F, S, or Q (FILL, STOP, OR QUIT):")
                    
                    ln2powerStatus   = ln2.ckpowerDIO() 
                    
                    if cmd.upper() == 'S': 

                        if ln2powerStatus == 'OFF':
                            print('\nLN2 power already OFF...')
                            
                        else:
                            print('\nLN2 power is ON,  Powering OFF......')
                            ln2.power()
                              

                    elif cmd.upper() =='Q': exit()

                    killPy('ln2stop')
                    startPy('ln2Reset')

                    exit()

            else:
                print('\nLN2 power is already ON...')

                if ln2durFlg: 
                    print('\nFilling for {} minutes... then LN2 valve will close'.format(str(ln2dur)))
                    sleep(ln2dur*60.)
                    print('\nLN2 power is ON, Powering OFF & exiting...')
                    ln2.power()
                    startPy('ln2Reset')
                    exit()

                else:
                    print('\nFilling and waiting for command...')
                    #cmd    = raw_input("\nChoose F, S, R, or Q (FILL, STOP, CHECK OR QUIT):")
                    #print ("\nLaunching ln2stop.py in case an overtime of {} minutes".format(MaxDur))
                    #subprocess.call([r"C:\bin\ln2stop.bat",MaxDur], shell=True)

                    startPy('ln2stop', args=MaxDur)

                    cmd    = raw_input("\nChoose F, S, or Q (FILL, STOP, OR QUIT):")
                    ln2powerStatus   = ln2.ckpowerDIO() 
                    
                    if cmd.upper() == 'S': 

                        if ln2powerStatus == 'OFF':
                            print('\nLN2 power already OFF...')
                            
                        else:
                            print('\nLN2 power is ON,  Powering OFF......')
                            ln2.power()

                    elif cmd.upper() =='Q': exit()

                    killPy('ln2stop')
                    startPy('ln2Reset')

                    exit()

        else: 
            print('\nexiting....')
            exit()

        # else: 
        #     cmd  = raw_input("\nChoose F, S, R, or Q (FILL, STOP, CHECK OR QUIT):")
        #     if cmd.upper() == 'S':
        #         ln2.poweroff()
        #     elif cmd.upper() == 'Q':
        #         ln2.poweroff()
        #         exit()
        #     elif cmd.upper() == 'R':
        #         ln2.status()






if __name__ == "__main__":
    #main(sys.argv[1:])
    main()

     