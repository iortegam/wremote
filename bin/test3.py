#! /usr/bin/python


import os
import win32pipe, win32file
from Queue import Queue,Empty



opusPIPE =  r"\\.\pipe\OPUS"
q        = Queue()

def writePIPE(fid,msg):
	
	win32file.SetFilePointer(fid,0,win32file.FILE_BEGIN)
	win32file.WriteFile(fid,msg,None)
	win32file.FlushFileBuffers(fid)
	
	return 1

def readPIPE(fid,queue,TO):
	
	win32file.SetFilePointer(fid,0,win32file.FILE_BEGIN)
	queue.put(win32file.ReadFile(fid,1024,None))
	#queue.put( lambda: win32file.ReadFile(fid,1024,None) )
	win32file.FlushFileBuffers(fid)

	try: 
		data = queue.get(timeout=TO)[1]
	except: 
		data = ""

	return data


def main():


	opusHndl = win32file.CreateFile(opusPIPE,win32file.GENERIC_READ | win32file.GENERIC_WRITE,\
	                                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,   \
	                                None, win32file.OPEN_EXISTING, 0 , None)
	
	msg = "START_MACRO C:\\bin\\testPIPE 1\n"
	rtn = writePIPE(opusHndl,msg)
	rtn1 = readPIPE(opusHndl,q,5)
	print repr(rtn1)
	msg = "3\n"
	rtn = writePIPE(opusHndl,msg)
	rtn2 = readPIPE(opusHndl,q,5)
	print repr(rtn2)
	
	

if __name__ == "__main__":
	main()