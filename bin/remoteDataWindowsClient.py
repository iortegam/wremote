#! c:\Python27\python
#----------------------------------------------------------------------------------------
# Name:
#        remoteData.py
#
# Purpose:
#       This is the data server for the remote FTIR instrument
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

    #-------------------------#
    # Import Standard modules #
    #-------------------------#
import sys
import socket

 
    
class FTIRdataClient(object):
    
    def __init__(self,TCP_IP="127.0.0.1",TCP_Port=5555,BufferSize=4024):
	
        #-----------------------------------
        # Configuration parameters of server
        #-----------------------------------
        self.TCP_IP          = TCP_IP
        self.TCP_Port        = int(TCP_Port)
        self.RECV_BUFFER     = int(BufferSize) 

    def setParam(self,message):
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.send("set "+message.encode())
            incomming = sock.recv(self.RECV_BUFFER)
            sock.close()    
        except:
            print "Unable to connect to data server: {}!!".format(self.TCP_IP)
            incomming = False
            
        return incomming
    
    def getParam(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.send("get "+message.encode())
            incomming = sock.recv(self.RECV_BUFFER)
            sock.close()    
        except:
            print "Unable to connect to data server: {}!!".format(self.TCP_IP)
            incomming = False
            
        return incomming        

    def writeTCP(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.send(message.encode())
            incomming = sock.recv(self.RECV_BUFFER)
            sock.close()   
        except:
            print "Unable to connect to data server: {}!!".format(self.TCP_IP)
            incomming = False
            
        return incomming         
        

    def writeSpectra(self,message):

        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.send("WRITE_OPUS "+message.encode())
            incomming = sock.recv(self.RECV_BUFFER)
            sock.close()    
        except:
            print "Unable to connect to data server: {}!!".format(self.TCP_IP)
            incomming = False
            
        return incomming    
                

