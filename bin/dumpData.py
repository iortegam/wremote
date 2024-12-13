#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        remoteDataObserver.py
#
# Purpose:
#       This program monitors TCP data server. Displays output to screen and log file.
#
#
#
# Notes:
#
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
#-----------------------------------------------------------------------------------------


#---------------
# Import modules
#---------------
import socket
from time       import sleep
from remoteData       import FTIRdataClient

# class FTIRdataClient():

#     def __init__(self,TCP_IP="127.0.0.1",TCP_Port=5555,BufferSize=4096):

#         #-----------------------------------
#         # Configuration parameters of server
#         #-----------------------------------
#         self.TCP_IP          = TCP_IP
#         self.TCP_Port        = int(TCP_Port)
#         self.RECV_BUFFER     = int(BufferSize)

#     def writeTCP(self,message):

#         try:
#             sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#             sock.connect((self.TCP_IP,self.TCP_Port))
#             sock.sendall(message.encode())

#             #-------------------------
#             # Loop to recieve all data
#             #-------------------------
#             incommingTotal = ""
#             while True:
#                 incommingPart = sock.recv(self.RECV_BUFFER)
#                 if not incommingPart: break
#                 incommingTotal += incommingPart.decode()

#             sock.close()
#         except:
#             print ("Unable to connect to data server!!")
#             incommingTotal = False

#         return incommingTotal


if __name__ == "__main__":

    #-------------------------------
    # Get user input for data server
    # IP address and port number
    #-------------------------------
    #dataServer_IP = raw_input("Enter Data Server IP address (or Enter 1 for FL0 Local): ")
    dataServer_IP = input("Enter Data Server IP address (or Enter 1 for FL0 Local): ")
    try:
        ipInd = int(dataServer_IP)
        if   ipInd == 1: dataServer_IP = "192.168.0.122" # old - "192.168.0.160"  # "127.0.0.1"  # FL0 
       
        else:
            print ("Unrecognized option")
            sys.exit()
    except: pass

    portNum = input("Enter port number for data server (Press Enter for Default 5555): ")
    if not portNum:
        portNum = 5555
    else:
        portNum = int(portNum)

    loopFlg = input("Enter 1 for single output or 2 for continuous output (Press Enter for Default 1): ")
    if not loopFlg: loopFlg = 1
    else:
        try:
            loopFlg = int(loopFlg)
        except:
            loopFlg = 1

    #----------------------------------
    # Initiate remote data client class
    #----------------------------------
    dataClass = FTIRdataClient(TCP_IP=dataServer_IP,TCP_Port=portNum,BufferSize=4024)
  

    while True:
        #--------------------------------
        # Ask database for all parameters
        #--------------------------------
        allParms = dataClass.writeTCP("LISTALL")
        allParms = allParms.strip().split(";")

        allTS    = dataClass.writeTCP("LISTALLTS")
        allTS    = allTS.strip().split(";")

        allET    = dataClass.writeTCP("LISTALLET")
        allET    = allET.strip().split(";")

        #-----------------------
        # Put data in dictionary
        #-----------------------
        data = {}
        
        for val in allParms:
            val = val.strip().split("=")
            data[val[0].strip()] = val[1].strip()

        TS = {}
        for val in allTS:
            print(val)
            val = val.strip().split("=")
            TS[val[0].strip()] = val[1].strip()

        ET = {}
        for val in allET:
            print(val)
            val = val.strip().split("=")
            ET[val[0].strip()] = val[1].strip()


        print(ET['ATDSIS_ANIN1(0X2314.07)'])
        print(data['ATDSIS_ANIN1(0X2314.07)'])


        #---------------------
        # Write data to screen
        #---------------------
        print ('\n')
        for key,val in sorted(data.items()):
            #TS_ = "{}-{}-{} {}:{}:{}".format(TS[key][0:4], TS[key][4:6], TS[key][6:8], TS[key][9:11], TS[key][11:13], TS[key][13:15]  )
            #print ("{0:25s} {1:35s} = {2:<60}".format(TS_, key,val))

            TS_ = "{}-{}-{} {}:{}:{}".format(TS[key][0:4], TS[key][4:6], TS[key][6:8], TS[key][9:11], TS[key][11:13], TS[key][13:15]  )
            print("{0:25s} {1:<10.2f} {2:<25} = {3:<60} ".format(TS_, float(ET[key]), key, val))

        if loopFlg == 1: break
        else:            sleep(5)
