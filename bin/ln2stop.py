"""
File:                       ln2stop.py


Purpose:                   stop ln2 filling ifovertime 

"""

#---------------
# Import modules
#---------------
import sys
import urllib2
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

import fl0d     


#'----------------------------------'
# Get Python PIDs
#'----------------------------------'
def get_Pypid():

    pids = {}

    for proc in psutil.process_iter():
        
        try:
            _name = proc.name()
           
            if _name in ['python.exe', 'python3.exe', 'Python.exe', 'Python3.exe']:
                try:
                    cmd = proc.cmdline()
                except psutil.AccessDenied:
                    continue
             
                if cmd[1].endswith('.py'):
                    since = dt.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                    pids[proc.pid] = {'since': since, 'pid': proc.pid, 'name':cmd[1]}
       
        except psutil.AccessDenied:
            continue        
    
    return pids

#---------------

def usage():
    ''' Prints to screen standard program usage'''
    print ( '\nln2stop.py <overtime>\n'
            '<overtime>                           : overtime in minutes')


if __name__ == "__main__":
    
    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    try:
        timeout  = float(sys.argv[1])
    except:
        timeout  = 20.

    # Timer starts
    starttime = time.time()

    print(60*'-')
    print('checking overtime of {} minutes for ln2 filling'.format(timeout))
    print(60*'-')

    while True:
        
        # Total time elapsed since the timer started
        totaltime = round((time.time() - starttime), 2) / 60.

        print("Total Time: {:.2} Minutes".format(totaltime))


        if totaltime >= timeout:

            print('exit')
            exit()

            pids = get_Pypid()

            for p in pids:
                name = pids[p]['name']

                if name.strip().split('\\')[-1] == 'ln2.py':
                    print ('ln2.py is currently running ...at {}\n'.format(dt.datetime.utcnow()))
                    print('Killing current running ln2.py program')
                    os.system("taskkill /F /T /PID {}".format(p['pid']))

            print ("\nAttemping to stop filling of LN2...")
            subprocess.call("python ln2.py -fs", shell=False)

            exit()

        sleep(5)
