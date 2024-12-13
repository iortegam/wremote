"""
File:                       seeker.py


Purpose:                   start/sto Tracker at FL0 

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


import fl0d    

from ckpy import get_Pypid, startPy, killPy  

#---------------

def usage():
    ''' Prints to screen standard program usage'''
    print ( '\nseeker.py -i <Ctlfile> -f <ON,OFF> -?\n\n'
            '  -i <Ctlfile>                           : Optional Flag to specify ctl input file (Default is C:/bin/ops/FL0_Defaults.input\n'
            '  -f <ON, OFF>                           : Optional Flag for main command: -f <ON, OFF>\n'
            '  -c                                     : Optional Flag to check if tracker is open or close (-k is needed if power needs to be off at the end of checking)\n'
            '  -k                                     : Optional Flag to kill power if power is ON\n'
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

class seekerClass():

    def __init__(self,ctlFvars):

        #self.TCPserverIP = TCP_IP_in
        self.ctlFvars    = ctlFvars
       

        #FTIRdataClient.__init__(self,TCP_IP=TCP_IP_in,TCP_Port=TCP_Port_in,BufferSize=BufferSize_in)

        #---------------
        # Reading ctl file(s) (analog & digital)
        #---------------
        self.digitalgctl = fl0d.read_daqctl(ctlFvars['File_DigitalInput'])
        self.analogctl   = fl0d.read_daqctl(ctlFvars['File_AnalogInput'])
       
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

        #---------------
        # AI info
        #---------------
        self.ai_info  = self.daq_dev_info.get_ai_info()
        self.ai_range = self.ai_info.supported_ranges[0]


            #ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.IN)
    
            
        #except Exception as e:
        #    print('\n', e)
        #finally:
        #    if self.use_device_detection:
        #        ul.release_daq_device(self.board_num)

    def poweron(self):


        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)

        port_value = 0xFF
        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\npower on {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'SK28V' ][0]

        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = 1
       #print('Setting', self.port.type.name, 'bit', bit_num, 'to', bit_value)

        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value)

        msg = self.digitalgctl[ch][5] +' ON'
        self.setParam(msg)

        sleep(2)


    def power(self):
        print(30*'-')

        

        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)

        port_value = 0xFF
        #port_value = 1

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\nTracker power relay at {} UT...'.format(getDTstr(crntTime)[1]))
        #print('\nSeeker powering off at {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch          = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'SK28V' ][0]
        
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
        print('Setting Momentarily power', self.port.type.name, 'bit', bit_num, 'to', bit_value_1)
        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_1)

        sleep(2)
        print('Switching Momentarily power', self.port.type.name, 'bit', bit_num, 'to', bit_value_2)
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_2)

        #msg = self.digitalgctl[ch][5] +' OFF'
        #self.setParam(msg)

        sleep(3)


    def ckpower(self):
        print(30*'-')

        port_value = 0xFF
        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime  = dt.datetime.now(dt.timezone.utc)
        print('\nChecking Seeker Power Status at {} UT...'.format(getDTstr(crntTime)[1]))

        ch        = [c for ci, c in enumerate(self.analogctl) if self.analogctl[c][8] == 'SK28V' ][0]
        channel   = int(self.digitalgctl[ch][0])

        #print('Channel = {}'.format(channel))

        if self.ai_info.resolution <= 16:
            # Use the v_in method for devices with a resolution <= 16
            # (optional parameter omitted)
            value = ul.v_in(self.board_num, channel, self.ai_range)
        else:
            # Use the v_in_32 method for devices with a resolution > 16
            # (optional parameter omitted)
            value = ul.v_in_32(self.board_num, channel, self.ai_range)

        # Display the value
        print('Voltage Value: {0:.2f} [V] --> [Channel = {1:}] (SK28V)'.format(value, channel ))

        sleep(1)

        if  int(value) <= 0.5:
            print('Seeker Power is OFF..') 
            return 'OFF'
        elif int(value) >=3: 
            print('Seeker Power is ON..') 
            return 'ON'
        else: return 'NAN'


    

        

        

        # if self.port.is_port_configurable:
        #     ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.IN)

        # # Get a value from the digital port
        # port_value = ul.d_in(self.board_num, self.port.type)

        # #print('Setting', self.port.type.name, 'to', port_value)
        # crntTime = dt.datetime.utcnow()
        # print('\nChecking status of power for tracker at {} UT...'.format(getDTstr(crntTime)[1]))

        # ch = [c for ci, c in enumerate(self.analogctl) if self.analogctl[c][4] == 'SK28V' ][0]
        
        # bit_num   = int(self.analogctl[ch][0])
        # bit_value = ul.d_bit_in(board_num, port.type, bit_num)

        # # Display the port value
        # print(self.port.type.name, 'Value:', self.port_value)
        # # Display the bit value
        # print('Bit', bit_num, 'Value:', bit_value)

    def ckpowerDIO(self):
        print(30*'-')

        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.IN)

        # Get a value from the digital port
        port_value = ul.d_in(self.board_num, self.port.type)

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\nChecking status of tracker power dio (SK28V) at {} UT...'.format(getDTstr(crntTime)[1]))

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'SK28V' ][0]
        
        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = ul.d_bit_in(self.board_num, self.port.type, bit_num)

        # Display the port value
        #print(self.port.type.name, 'Value:', port_value)
        # Display the bit value
        print('Channel {} (SK28V) Bit Value: {}'.format(bit_num, bit_value))

        self.ckpowerDIO = bit_value

        sleep(1)


    def ckseekerDIO(self):
        print(30*'-')

        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.IN)

        # Get a value from the digital port
        port_value = ul.d_in(self.board_num, self.port.type)

        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\nChecking status of tracker hatch dio (HTCHR) at {} UT...'.format(getDTstr(crntTime)[1]))

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'HTCHR' ][0]
        
        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = ul.d_bit_in(self.board_num, self.port.type, bit_num)

        # Display the port value
        #print(self.port.type.name, 'Value:', port_value)
        # Display the bit value
        print('Channel {} (HTCHR) Bit Value: {}'.format(bit_num, bit_value))

        self.ckseekerDIO = bit_value

        sleep(1)

        # if   int(bit_value) == 1:
        #     print('\nHatch is closed..') 
        #     return 'OFF'
        # elif int(bit_value) == 0: 
        #     print('\nHatch is open..') 
        #     return 'ON'
        # else: return 'NAN'


    def hatch(self):
        print(30*'-')

        if self.port.is_port_configurable:
            ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)

        port_value = 0xFF
        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime = dt.datetime.now(dt.timezone.utc)
        print('\nHatch relay at {} UT...'.format(getDTstr(crntTime)[1]))

        # Output the value to the port
        ul.d_out(self.board_num, self.port.type, port_value)

        ch = [c for ci, c in enumerate(self.digitalgctl) if self.digitalgctl[c][4] == 'HTCHR' ][0]

        bit_num   = int(self.digitalgctl[ch][0])
        bit_value = 0
       #print('Setting', self.port.type.name, 'bit', bit_num, 'to', bit_value)

        # Output the value to the bit
        #ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value)
        #sleep(2)

        #bit_value = 1
        #ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value)

        bit_value_1 = 0
        bit_value_2 = 1
        #--------------------
        # Momentarily set digital output to high (0) to toggle relay state
        #--------------------
        print('Setting Momentarily Hatch', self.port.type.name, 'bit', bit_num, 'to', bit_value_1)
        # Output the value to the bit
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_1)

        sleep(6)
        
        print('Switching Momentarily Hatch', self.port.type.name, 'bit', bit_num, 'to', bit_value_2)
        ul.d_bit_out(self.board_num, self.port.type, bit_num, bit_value_2)

        sleep(60)

    def ckhatch(self):
        print(30*'-')

        port_value = 0xFF
        #print('Setting', self.port.type.name, 'to', port_value)
        crntTime  = dt.datetime.now(dt.timezone.utc)
        print('\nChecking Seeker hatch Status at {} UT...'.format(getDTstr(crntTime)[1]))

        ch        = [c for ci, c in enumerate(self.analogctl) if self.analogctl[c][8] == 'HTC5V' ][0]
        channel   = int(self.digitalgctl[ch][0])

        #print('Channel = {}'.format(channel))

        if self.ai_info.resolution <= 16:
            # Use the v_in method for devices with a resolution <= 16
            # (optional parameter omitted)
            value = ul.v_in(self.board_num, channel, self.ai_range)
        else:
            # Use the v_in_32 method for devices with a resolution > 16
            # (optional parameter omitted)
            value = ul.v_in_32(self.board_num, channel, self.ai_range)

        # Display the value
        print('Voltage Value: {0:.2f} [V] --> [Channel = {1:}] (HTC5V)'.format(value, channel ))

        sleep(2)

        if  int(value) <= 0.5:
            print('Seeker Hatch is ON (OPEN)..') 
            return 'ON'
        elif int(value) >=3.0: 
            print('Seeker Hatch is OFF (CLOSE)..') 
            return 'OFF'
        else: return 'NAN'


def main():

    #--------------------------------
    # 
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
    cmdFlg       = False
    killFlg      = False
    checkFlg     = False


    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:f:kc?')
        if len(opts) >=1: argsFlg    = True

    except getopt.GetoptError as err: pass

    if argsFlg:
        for opt, arg in opts:
            # Check input file flag and path
            if opt == '-i':
                ctlFile       = arg

            elif opt.lower() == '-f':
                if not arg or arg.startswith('-'):
                    usage()
                    exit()  
                cmd    = arg
                cmdFlg = True

                if cmd.upper() == 'ON' or cmd.upper() == 'OFF': pass
                else:
                    usage()
                    exit()
            elif opt.lower() == '-k':
                killFlg  = True

            elif opt.lower() == '-c':
                checkFlg  = True

            elif opt.lower() == '-?':
                usage()
                exit()  
                
    else:
        if not cmdFlg:    
            cmd    = input("\nChoose ON or OFF (OPEN or CLOSE TRACKER):")

            if cmd.upper() == 'ON' or cmd.upper() == 'OFF': pass
            else:
                usage()
                exit()

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile, exitFlg=True)

    ctlFvars        = mainInputParse(ctlFile)

    #----------------------------------
    # Initiate remote data client class
    #----------------------------------
    dataServer = FTIRdataClient(TCP_IP=ctlFvars["FTS_DataServ_IP"], TCP_Port=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize=int(ctlFvars["FTS_DATASERV_BSIZE"]))

    #-----------------------------
    # Initialize seeker class
    #-----------------------------
    sk              = seekerClass(ctlFvars)
    skpowerStatus   = sk.ckpower() 

    if checkFlg:
        if skpowerStatus == 'ON':   
            
            hatchStatus     = sk.ckhatch()

            if hatchStatus == 'ON': rtnFlg = True
            else:                   rtnFlg = False

        else:
            sk.power()
            sleep(2)
            skpowerStatus   = sk.ckpower()
            hatchStatus     = sk.ckhatch()
            sleep(2)

            if hatchStatus == 'ON': rtnFlg = True
            else:                   rtnFlg = False

        if killFlg:
            sk.power()
            skpowerStatus   = sk.ckpower()

        #-----------------------
        # Compose command string
        #-----------------------
        try:
            cmd = "TRACKER_STATUS "+hatchStatus    
            dataServer.setParam(cmd)
            cmd = "TRACKER_POWER "+skpowerStatus    
            dataServer.setParam(cmd)
        except: pass

        return rtnFlg


    if killFlg:
        if skpowerStatus == 'ON':
            print('\nSeeker Power is ON, Powering OFF...')          
            sk.power()
            skpowerStatus   = sk.ckpower()
        else:
            print('\nSeeker Power is already OFF...')

        exit()
    

    if cmd.upper() =='ON':    

        dataServer.setParam("TRACKER_CMND OPEN")

        if skpowerStatus == 'ON':
            print('\nSeeker Power is ON...')
            hatchStatus     = sk.ckhatch()

            if hatchStatus == 'ON':
                print('\nSeeker Hatch is already ON...')
            else:
                sk.hatch()
                
                hatchStatus     = sk.ckhatch()

                if hatchStatus == 'ON': 
                    print('\nSeeker Hatch is ON...')
                else:
                    print('\nSeeker Hatch is OFF... Check the tracker!!')

        else: 
            print('\nSeeker Power is OFF, Powering ON...')
            sk.power()
            skpowerStatus   = sk.ckpower()

            hatchStatus     = sk.ckhatch()

            if hatchStatus == 'ON':
                print('\nSeeker Hatch is already ON...')
            else:
                sk.hatch()
                
                hatchStatus     = sk.ckhatch()

                if hatchStatus == 'ON': 
                    print('\nSeeker Hatch is ON...')
                else:
                    print('\nSeeker Hatch is OFF... Check the tracker!')

        if hatchStatus == 'ON': rtnFlg = True
        else:                   rtnFlg = False

        #-----------------------
        # Compose command string
        #-----------------------
        try:
            cmd = "TRACKER_STATUS "+hatchStatus    
            dataServer.setParam(cmd)
            cmd = "TRACKER_POWER "+skpowerStatus    
            dataServer.setParam(cmd)
        except: pass

        return rtnFlg


    elif cmd.upper() =='OFF':

        if skpowerStatus.upper() == 'ON':

            print('\nSeeker Power is ON...')

            hatchStatus     = sk.ckhatch()

            if hatchStatus == 'ON':
                print('\nSeeker Hatch is ON... attemping to Close Hatch!')
                sk.hatch()
                
                hatchStatus     = sk.ckhatch()

                if hatchStatus == 'OFF': 
                    print('\nSeeker Hatch is OFF...')
                    print('\nSeeker Power is ON, Powering OFF...')
                    sk.power()
                    skpowerStatus   = sk.ckpower()
                    #print('\nExiting...')
                else:
                    print('\nSeeker Hatch is still ON... attemping to Close Hatch!')
                    sk.hatch()

                    hatchStatus     = sk.ckhatch()

                    if hatchStatus == 'OFF': 
                        print('\nSeeker Hatch is OFF...')
                        print('\nSeeker Power is ON, Powering OFF...')
                        sk.power()
                        skpowerStatus   = sk.ckpower()
                        #print('\nExiting...')

                    else: 
                        print('\nSeeker Hatch is still ON... check the tracker!')

            else: 

                print('\nSeeker Hatch is OFF...')
                print('\nSeeker Power is ON, Powering OFF...')
                sk.power()
                skpowerStatus   = sk.ckpower()


            dataServer.setParam("TRACKER_CMND CLOSE")




        else:

            dataServer.setParam("TRACKER_CMND CLOSE")

            print('\nSeeker Power is OFF, Powering ON...')
            sk.power()
            skpowerStatus   = sk.ckpower()

            if skpowerStatus.upper() == 'ON':

                hatchStatus     = sk.ckhatch()
                
                if hatchStatus == 'ON':
                    print('\nSeeker Hatch is ON... attemping to Close Hatch!')
                    sk.hatch()
                    
                    hatchStatus     = sk.ckhatch()

                    if hatchStatus == 'OFF': 
                        print('\nSeeker Hatch is OFF...')
                        #print('\nSeeker Power is ON, Powering OFF...')
                        #sk.power()
                        #skpowerStatus   = sk.ckpower()
                        #print('\nExiting...')
                        
                    else:
                        print('\nSeeker Hatch is still ON... attemping to Close Hatch!')
                        sk.hatch()

                        hatchStatus     = sk.ckhatch()

                        if hatchStatus == 'OFF': 
                            print('\nSeeker Hatch is OFF...')
                            #print('\nSeeker Power is ON, Powering OFF...')
                            #sk.power()
                            #skpowerStatus   = sk.ckpower()
                            #print('\nExiting...')
                            

                        else: 
                            print('\nSeeker Hatch is still ON... check the tracker!')


                else: 
                    print('\nSeeker Hatch is OFF...')
                    #print('\nSeeker Power is ON, Powering OFF...')
                    #sk.power()
                    #skpowerStatus   = sk.ckpower()

                

                print('\nSeeker Power is ON, Powering OFF...')
                sk.power()
                skpowerStatus   = sk.ckpower()
                #print('\nExiting...')


            else:
                print('\nSeeker Power is still OFF, Check power...')



        if hatchStatus == 'ON': rtnFlg = True
        else:                   rtnFlg = False

        try:
            cmd = "TRACKER_STATUS "+hatchStatus    
            dataServer.setParam(cmd)
            cmd = "TRACKER_POWER "+skpowerStatus    
            dataServer.setParam(cmd)
        except: pass


        return rtnFlg


if __name__ == "__main__":
    #main(sys.argv[1:])
    main()

     