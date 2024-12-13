"""
File:                       fl0d.py


Purpose:                   Analog and digital outputs

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

#---------------

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

def read_daqctl(fname):

    ctl         = {}
    lines       = tryopen(fname)

    lines[:]    = [row for row in lines if not '#' in row]

    npoints     = len(lines)

    for l_i, l in enumerate(lines):

            ctl['CH'+str(l_i)] = l.strip().split()

    return ctl


class daqClass(FTIRdataClient):

    def __init__(self,ctlFvars, TCP_IP_in="192.168.50.198",TCP_Port_in=5555,BufferSize_in=1024):

        self.TCPserverIP = TCP_IP_in
        self.ctlFvars    = ctlFvars
        self.fl0d        = {}

        FTIRdataClient.__init__(self,TCP_IP=TCP_IP_in,TCP_Port=TCP_Port_in,BufferSize=BufferSize_in)

        #---------------
        # Reading ctl file(s) (analog & digital)
        #---------------
        self.analogctl   = read_daqctl(ctlFvars['File_AnalogInput'])
        self.digitalgctl = read_daqctl(ctlFvars['File_DigitalInput'])
       
        #---------------
        # Standard from DAQ python examples
        #---------------
        self.use_device_detection = True
        self.dev_id_list          = []
        self.board_num            = 0
        self.rate                 = 5000
        self.points_per_channel   = 100
        self.memhandle            = None
        self.low_chan             = 0

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
        
        if not self.daq_dev_info.supports_analog_input:
            raise Exception('Error: The DAQ device does not support '
                            'analog input')

        if not self.daq_dev_info.supports_digital_io:
            raise Exception('Error: The DAQ device does not support '
                            'digital I/O')

        print('\nActive DAQ device: ', self.daq_dev_info.product_name, ' (',
              self.daq_dev_info.unique_id, ')\n', sep='')

        #---------------
        # analog info
        #---------------
        self.ai_info  = self.daq_dev_info.get_ai_info()
        self.ai_range = self.ai_info.supported_ranges[0]



        #------
        # Commented out 10/14/2024
        #------
        #---------------
        # DIO info
        #---------------
        # self.dio_info = self.daq_dev_info.get_dio_info()

        # self.port = next((port for port in self.dio_info.port_info if port.supports_output),
        #             None)

        # if not self.port:
        #     raise Exception('Error: The DAQ device does not support '
        #                     'digital output')

        
        # if self.port.is_port_configurable:
        #     ul.d_config_port(self.board_num, self.port.type, DigitalIODirection.OUT)

        #---------------
        # analog add info
        #---------------
        self.high_chan    = min(7, self.ai_info.num_chans - 1)
        self.num_chans    = self.high_chan - self.low_chan + 1

        self.total_count  = self.points_per_channel * self.num_chans
        self.scan_options = ScanOptions.BACKGROUND

        if ScanOptions.SCALEDATA in self.ai_info.supported_scan_options:
            # If the hardware supports the SCALEDATA option, it is easiest to
            # use it.
            self.scan_options |= ScanOptions.SCALEDATA

            self.memhandle = ul.scaled_win_buf_alloc(self.total_count)
            # Convert the memhandle to a ctypes array.
            self.ctypes_array = cast(self.memhandle, POINTER(c_double))
        elif self.ai_info.resolution <= 16:
            # Use the win_buf_alloc method for devices with a resolution <= 16
            self.memhandle = ul.win_buf_alloc(self.total_count)
            # Convert the memhandle to a ctypes array.
            self.ctypes_array = cast(self.memhandle, POINTER(c_ushort))
        else:
            # Use the win_buf_alloc_32 method for devices with a resolution > 16
            self.memhandle = ul.win_buf_alloc_32(self.total_count)
            # Convert the memhandle to a ctypes array.
            self.ctypes_array = cast(self.memhandle, POINTER(c_ulong))

        # Note: the ctypes array will no longer be valid after win_buf_free is
        # called.
        # A copy of the buffer can be created using win_buf_to_array or
        # win_buf_to_array_32 before the memory is freed. The copy can be used
        # at any time.

        # Check if the buffer was successfully allocated
        if not self.memhandle:
            raise Exception('Error: Failed to allocate memory')
    
       
        # Create a format string that aligns the data in columns
        self.row_format = '{:<12}' * self.num_chans

        # Print the channel name headers
        self.labels       = []
        self.labels_units = []
        for ch_num in range(self.low_chan, self.high_chan + 1):
            self.labels.append('CH' + str(ch_num))
            self.labels_units.append('CH' + str(ch_num)+'_units')  
            
        #except Exception as e:
        #    print('\n', e)
        #finally:
        #    if self.use_device_detection:
        #        ul.release_daq_device(self.board_num)
    



    def analog_in(self):
        # By default, the example detects and displays all available devices and
        # selects the first device listed. Use the dev_id_list variable to filter
        # detected devices by device ID (see UL documentation for device IDs).
        # If use_device_detection is set to False, the board_num variable needs to
        # match the desired board number configured with Instacal.
   

        #try:

        ul.a_in_scan(
            self.board_num, self.low_chan, self.high_chan, self.total_count,
            self.rate, self.ai_range, self.memhandle, self.scan_options)

        
        # Start updating the displayed values
        status, curr_count, curr_index = ul.get_status(
            self.board_num, FunctionType.AIFUNCTION)

        


        self.Data_a_in = []
       
        # Make sure a data point is available for display.
        #if curr_count > 0:
        #if status != status.IDLE:
        while status != Status.IDLE:

            if curr_count > 0:
                # curr_index points to the start of the last completed
                # channel scan that was transferred between the board and
                # the data buffer. Display the latest value for each
                # channel.
                data = []
                for data_index in range(curr_index, curr_index + self.num_chans):
                    #print(data_index)
                    if ScanOptions.SCALEDATA in self.scan_options:
                        # If the SCALEDATA ScanOption was used, the values
                        # in the array are already in engineering units.
                        eng_value = self.ctypes_array[data_index]
                    else:
                        # If the SCALEDATA ScanOption was NOT used, the
                        # values in the array must be converted to
                        # engineering units using ul.to_eng_units().
                        eng_value = ul.to_eng_units(self.board_num, self.ai_range,
                                                    self.ctypes_array[data_index])
                    #print(eng_value)
                    data.append('{:.3f}'.format(eng_value))

                self.Data_a_in = data

            status, curr_count, curr_index = ul.get_status(
                self.board_num, FunctionType.AIFUNCTION)

        # Stop the background operation (this is required even if the
        # scan completes successfully)

        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)

        print('\n')
        print("fl0d at {}\n".format(dt.datetime.now(dt.timezone.utc)))
        print(self.row_format.format(*self.labels))
        print(self.row_format.format(*self.Data_a_in))
        

        #if self.memhandle:
                # Free the buffer in a finally block to prevent a memory leak.
        #    ul.win_buf_free(self.memhandle)
        #if self.use_device_detection:
        #    ul.release_daq_device(self.board_num)

    #except Exception as e:
        #    print('\n', e)
        #finally:
        #    if self.memhandle:
        #        # Free the buffer in a finally block to prevent a memory leak.
        #        ul.win_buf_free(self.memhandle)
        #    if self.use_device_detection:
        #        ul.release_daq_device(self.board_num)

    def eng2units(self):        

        #for ch in range(int(self.ctlFvars['Daq_analog_Channels'])+1):
        for ch in range(self.low_chan, self.high_chan + 1):
            if 'CH'+str(ch) in self.analogctl:
                if int(self.analogctl['CH'+str(ch)][1]) == 1:
                    
                    b = float(self.analogctl['CH'+str(ch)][2])
                    m = float(self.analogctl['CH'+str(ch)][3])
                    c = float(self.analogctl['CH'+str(ch)][4])
                    x = float(self.Data_a_in[ch])

                    units = b + m*x + c*x**2

                    self.fl0d['FL0D_'+self.analogctl['CH'+str(ch)][9] + '_' + self.analogctl['CH'+str(ch)][7] ] = units

                else:

                    self.fl0d['FL0D_'+self.analogctl['CH'+str(ch)][9] + '_' + self.analogctl['CH'+str(ch)][7] ] = -9999

        tempKeys = self.fl0d.keys()
        #tempKeys.sort()
        sorted(tempKeys)

        print('\n')
        for k_i, k in enumerate(self.fl0d):
            print('{0:<35}: {1:.2f}'.format(k.upper(), self.fl0d[k]))

    
    def printlog(self):

        crntTime  = dt.datetime.now(dt.timezone.utc)

        datestr, timestr = getDTstr(crntTime)

        if not ( self.ctlFvars['Dir_WinData'].endswith('\\') ): self.ctlFvars['Dir_WinData']=self.ctlFvars['Dir_WinData'] + '\\'

        self.crntDataDir = self.ctlFvars['Dir_WinData']  + datestr + '\\'

        ckDirMk(self.crntDataDir)

        fname = self.crntDataDir  + "house.log"

        tempKeys = self.fl0d.keys()
        #tempKeys.sort()
        sorted(tempKeys)

        
        strformat =  ['{'+str(i)+':<25}' for i in range(2, len(tempKeys)+2)]
        strformat = '{0:<10} {1:<10} '+''.join(strformat).lstrip().rstrip() + '\n'  
       

        tempKeys.insert(0, 'date')
        tempKeys.insert(1, 'time')

    
        if ckFile(fname): mode = 'a'
        else:             mode = 'w'


        with open(fname ,mode) as fopen:
            if mode == 'w': fopen.write(strformat.format(*tempKeys))
            d2print  = [self.fl0d[k] for k in tempKeys[2:]]
            d2print.insert(0, datestr)
            d2print.insert(1, timestr)
            fopen.write(strformat.format(*d2print))


    def sendData(self):
        #--------------------------
        # Write data to data server
        #--------------------------
        if not self.fl0d:
            print("No data to write from fl0d...")
            return False

        for key in self.fl0d:
            message = key + " " + str(self.fl0d[key])
            self.setParam(message)

        #---------------------------------------------
        # Send time stamp of connection to data server
        #---------------------------------------------
        crntDateTime = dt.datetime.now(dt.timezone.utc)

      

if __name__ == '__main__':

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    #try:
    #    ctlFile  = sys.argv[1]
    #except:
    #    ctlFile       = "C:/bin/ops/FL0_Defaults.input"

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

    print("\nLocal input parameters:")
    for k in ctlFvars: print('{:20}: {:}'.format(k, ctlFvars[k]))

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    portNum        = ctlFvars['FTS_DATASERV_PORT']
    bin_Path       = ctlFvars['DIR_WINBIN']
    ctlFile        = ctlFvars['CTL_FILE']

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile, exitFlg=True)

    ctlFvars      = mainInputParse(ctlFile)

    #-----------------------------
    # Initialize 
    #-----------------------------
    daqData = daqClass(ctlFvars, TCP_IP_in=ctlFvars["FTS_DataServ_IP"], TCP_Port_in=int(ctlFvars["FTS_DataServ_PORT"]),BufferSize_in=int(ctlFvars["FTS_DATASERV_BSIZE"]))
    
    #daqData.analog_in()
    #daqData.eng2units()
    #exit()

    while True:
        try:
            daqData.analog_in()
            daqData.eng2units()

            #daqData.printlog()

            daqData.sendData()
    
        except: continue

        sleep(int(ctlFvars['Daq_Update']))


            
     