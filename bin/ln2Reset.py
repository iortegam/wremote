from schedule import every, repeat, run_pending
import time
import datetime as dt
import subprocess
from ModUtils     import *

#--------------------------------
#
#--------------------------------
# Edit here only
user    = 'bldopus'
ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

CheckTime    = 5   # Minutes

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

#-------------------------
#
#-------------------------
print('LN2 Checker every {} Minutes...\n'.format(CheckTime))

time.sleep(10)

print ("\nLaunching ln2.py -s in case it is running... sleeping for {} minutes".format(CheckTime))
subprocess.call([r"{}ln2.bat".format(bin_Path),"-fs"], shell=True)


@repeat(every(CheckTime).minutes)
def job():
    #print("I am a scheduled job at 30 min {}".format(dt.datetime.utcnow()))
    print ("\nLaunching ln2.py -s in case it is running... sleeping for {} minutes".format(CheckTime))
    #subprocess.call([r"C:\bin\ln2.bat","-fs"], shell=True)
    subprocess.call([r"{}ln2.bat".format(bin_Path),"-fs"], shell=True)


#@repeat(every(10).seconds)
#def job2():
#    print("I am a scheduled job at 10s {}".format(dt.datetime.utcnow()))
    
while True:
    run_pending()
    time.sleep(5)