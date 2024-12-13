"""
File:                       pydaq.py

Library Call Demonstrated:  mcculw.ul.d_out() and mcculw.d_bit_out()

Purpose:                    class for the usb-201 daq 


"""
from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from mcculw import ul
from mcculw.enums import DigitalIODirection
from mcculw.device_info import DaqDeviceInfo

try:
    from console_examples_util import config_first_detected_device
except ImportError:
    from .console_examples_util import config_first_detected_device



class DAQdevice():
    
    def __init__(self, board_num=0):

        use_device_detection = True
        dev_id_list          = []
        self.board_num       = board_num

        try:
            if use_device_detection:
                config_first_detected_device(board_num, dev_id_list)

            self.daq_dev_info = DaqDeviceInfo(board_num)
            if not self.daq_dev_info.supports_digital_io:
                raise Exception('\nError: The DAQ device does not support '
                                'digital I/O')

            print('\nActive DAQ device: ', self.daq_dev_info.product_name, ' (',
                  self.daq_dev_info.unique_id, ')\n', sep='')

            self.dio_info = self.daq_dev_info.get_dio_info()


        except Exception as e:
            print('\n', e)
        finally:
            if use_device_detection:
                ul.release_daq_device(board_num)
           

    def digital_out(self,channel=0):
        print ("\nTurning digital channel %d ON..." % channel),
  
        port = next((port for port in self.dio_info.port_info if port.supports_output),
                    None)
        if not port:
            raise Exception('Error: The DAQ device does not support '
                            'digital output')

        # If the port is configurable, configure it for output.
        if port.is_port_configurable:
            ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)

        port_value = 0xFF
        #port_value = 0

        print('Setting', port.type.name, 'to', port_value)

        # Output the value to the port
        ul.d_out(self.board_num, port.type, port_value)

        bit_num   = channel
        bit_value = 0
        print('Setting', port.type.name, 'bit', bit_num, 'to', bit_value)

        # Output the value to the bit
        ul.d_bit_out(board_num, port.type, bit_num, bit_value)
    
    def digital_in(self,channel=0):
        print ("\nTurning digital channel %d OFF..." % channel),

        port = next((port for port in dio_info.port_info if port.supports_input),
                    None)
        if not port:
            raise Exception('Error: The DAQ device does not support '
                            'digital input')

        # If the port is configurable, configure it for input.
        if port.is_port_configurable:
            ul.d_config_port(board_num, port.type, DigitalIODirection.IN)

        # Get a value from the digital port
        port_value = ul.d_in(board_num, port.type)

        # Get a value from the first digital bit
        bit_num = channel
        bit_value = ul.d_bit_in(board_num, port.type, bit_num)

        # Display the port value
        print(port.type.name, 'Value:', port_value)
        # Display the bit value
        print('Bit', bit_num, 'Value:', bit_value)