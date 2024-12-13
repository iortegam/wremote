#! /usr/bin/python
#----------------------------------------------------------------------------------------
# Name:
#        remoteDataClient.py
#
# Purpose:
#       This is a stand-a-lone version of the remote data client.
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
import socket

 
class FTIRdataClient(object):
    
    def __init__(self,TCP_IP="192.168.1.100",TCP_Port=5555,BufferSize=1024):
    
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
            sock.sendall("set "+message)
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart
            
            sock.close()    
        except:
            print "Unable to connect to data server!!"           
            incommingTotal = False   
            
        return incommingTotal
    
    def getParam(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall("get "+message)
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart
            
            sock.close()    
        except:
            print "Unable to connect to data server!!"           
            incommingTotal = False      
            
        return incommingTotal

    def getParamN(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall("getN "+message)
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart
            
            sock.close()    
        except:
            print "Unable to connect to data server!!"           
            incommingTotal = False    
            
        return incommingTotal


    def writeTCP(self,message):
        
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall(message)
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart
            
            sock.close()    
        except:
            print "Unable to connect to data server!!"           
            incommingTotal = False        
            
        return incommingTotal
        

    def writeSpectra(self,message):

        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    
            sock.connect((self.TCP_IP,self.TCP_Port))
            sock.sendall("WRITE_OPUS "+message)
            
            #-------------------------
            # Loop to recieve all data
            #-------------------------
            incommingTotal = ""
            while True:
                incommingPart = sock.recv(self.RECV_BUFFER)
                if not incommingPart: break
                incommingTotal += incommingPart
            
            sock.close()    
        except:
            print "Unable to connect to data server!!"           
            incommingTotal = False   
            
        return incommingTotal