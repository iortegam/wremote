from schedule import every, repeat, run_pending
import time
import datetime as dt
import subprocess
from ModUtils     import *
from ckpy import ckscripts
from remoteData       import FTIRdataClient
from ckpy import get_Pypid, startPy, killPy 
from ModUtils import *

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

ctlFvars      = mainInputParse(ctlFile)

#----------------------------------
# Initiate remote data client class (To check specific times when updates are happening)
#----------------------------------
remoteDataCl = FTIRdataClient(TCP_IP=dataServer_IP,TCP_Port=portNum,BufferSize=4024)


log_fpath = os.path.dirname(os.path.abspath(ctlFile)) 

if not( log_fpath.endswith('/') ): log_fpath = log_fpath + '\\'

log_fname = log_fpath + 'ckpyReset.log'

if ckFile(log_fname): mode = 'a+'
else: mode = 'w'

logFile = logging.getLogger('1')
logFile.setLevel(logging.INFO)
hdlr1   = logging.FileHandler(log_fname,mode=mode)
fmt1    = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%a, %d %b %Y %H:%M:%S')
hdlr1.setFormatter(fmt1)
logFile.addHandler(hdlr1) 
logFile.info('**************** Starting ckpyReset.py ***********************')

#-------------------------
#
#-------------------------
print('\nckscripts every {} Minutes...'.format(CheckTime))
print('... and detecting if ATDSIS is hanging\n')
time.sleep(CheckTime*60)

@repeat(every(CheckTime).minutes)
def job():

    print ("\nLaunching ckscripts... sleeping for {} minutes".format(CheckTime))
    #subprocess.call([r"C:\bin\ln2.bat","-fs"], shell=True)
    ckscripts(ctlFile, ln2ResFlg= False)
    #print(ctlFile)


ews_n = 0

while True:
    #-------------------------
    # Start the job
    #-------------------------
    run_pending()

    #-------------------------
    # The following is included to check specific times when updates are happening
    # If times are large scripts are killed
    # For now only checking ATDSIS
    #-------------------------

    allParms = remoteDataCl.writeTCP("LISTALL")
    allParms = allParms.strip().split(";")

    allET    = remoteDataCl.writeTCP("LISTALLET")
    allET    = allET.strip().split(";")

    #-----------------------
    # Put data in dictionary
    #-----------------------
    data = {}
    for val in allParms:
        val = val.strip().split("=")
        data[val[0].strip()] = val[1].strip()

    ET = {}
    for val in allET:
        val = val.strip().split("=")
        ET[val[0].strip()] = val[1].strip()


    #-----------------------
    # checking atdsis
    #----------------------- 
    try:
        ET_   = float(ET['ATDSIS_ANIN1(0X2314.07)'])
        #print('\nATDSIS ET (min): {}'.format(ET_))    

        if ET_ > 10.:  # Minutes
            logFile.info('atdsisNCAR.py hanging...')
            logFile.info('killing atdsisNCAR.py')

            killPy('atdsisNCAR')  

    except:
        logFile.info('TCP RemoteData for ATDSIS not found')
        pass

    #-----------------------
    # checking ews
    #----------------------- 
    try:
        ET_   = float(ET['BRUKER_INSTRUMENT_STATUS']) 

        if ET_ > 10.:  # Minutes

            if ews_n == 0:
                logFile.info('Bruker EWS is not responding')

                msg = ("---------------------------EWS IS NOT RESPONDING-------------------\n\n" +
                       "Cycle power of Bruker via PDU!!"          +
                       "---------------------------------------------------------------------".format(ctlFvars['LN2_PRESSURE_MIN']))

                Subject = "Bruker EWS is not responding at {0:} LT".format(dt.datetime.now(dt.timezone.utc))

                sendEmail(msg, Subject, ctlFvars)

                ews_n+=1 
        else:
            ews_n = 0

    except:
        logFile.info('TCP RemoteData for EWS not found')
        pass



    time.sleep(20)