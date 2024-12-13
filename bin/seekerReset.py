from schedule import every, repeat, run_pending
import time
import datetime as dt
import subprocess
from ModUtils     import *
from remoteData       import FTIRdataClient


#--------------------------------
#
#--------------------------------
# Edit here only
user    = 'bldopus'
ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

CheckTime = 1   # Minutes

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

#----------------------------------
# Initiate remote data client class
#----------------------------------
dataServer = FTIRdataClient(TCP_IP=dataServer_IP,TCP_Port=portNum,BufferSize=4024)

#----------------------------
# Check existance of ctl file
#----------------------------
ckFile(ctlFile,exitFlg=True)

#-------------------------
# Import ctlFile variables
#-------------------------
ctlFvars  = mainInputParse(ctlFile)

#-------------------------
#
#-------------------------
print('\nSeeker Checker every {} Minutes...\n'.format(CheckTime))
    
while True:

    tracker_cmnd   = dataServer.getParam("TRACKER_CMND")
    hatchFlg       = dataServer.getParam("TRACKER_STATUS")
    skpowerFlg     = dataServer.getParam("TRACKER_POWER")

    Wind_status   = dataServer.getParam("ATM_WIND_SPEED")
    Wind_gust     = dataServer.getParam("ATM_WIND_GUST")


    print('\nTIME              = {}'.format(dt.datetime.now()))
    print('TRACKER_CMND        = {0:>15}'.format(tracker_cmnd))
    print("TRACKER_STATUS      = {0:>15}".format(hatchFlg))
    print("TRACKER_POWER       = {0:>15}".format(skpowerFlg))


    print('\nSleeping for {} Minutes'.format(CheckTime))
    time.sleep(CheckTime*60)

    if float(Wind_status[0:3]) > float(ctlFvars['HIGH_WIND_SPEED_LIMIT']):
        dataServer.setParam("TRACKER_CMND CLOSE")

        print('\nHigh Wind Speed Detected!!!\n')
        print("ATM_WIND_SPEED      = {0:>15}".format(Wind_status))
        print("ATM_WIND_GUST       = {0:>15}".format(Wind_gust))
        print("HIGH_WIND_SPEED_LIMIT = {0:>15}".format(ctlFvars['HIGH_WIND_SPEED_LIMIT']))
        time.sleep(5)

 
    
    if tracker_cmnd.upper() == 'CLOSE':

        if (hatchFlg == 'OFF') & (skpowerFlg == 'OFF'): continue
        
        print('TRACKER_CMND == CLOSE')
        print ("Launching seeker.py -f off")
        #subprocess.call([r"C:\bin\seeker.bat","-f off"], shell=True)
        subprocess.call("python {}seeker.py -f off".format(bin_Path), shell=False)
    
    #time.sleep(5)