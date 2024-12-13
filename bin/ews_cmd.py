# Run automatic FTIR measurement
#
# $Id: ftir_measurement 72 2010-08-27 17:40:49Z dfeist $
#
# Import utility functions
import time, sys, os, os.path
import signal
import optparse
#import _mysql
#import mysql.connector

import configparser
from io import StringIO

#import pymysql
from ModUtils     import *
from ifs125hr import *
from ftirlib import *



def main():

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    #try:
    #    ctlFile  = sys.argv[1]
    #except:
    #    ctlFile  = "/home/tabftir/remote/ops/TAB_Defaults.input"

    #--------------------------------
    # Retrieve command line arguments
    #--------------------------------
    user    = 'bldopus'
    ctlFile = 'c:\\Users\\' + user + '\\wremote\\local.input'

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile,exitFlg=True)

    # #-------------------------
    # # Import ctlFile variables
    # #-------------------------
    ctlFvars        = mainInputParse(ctlFile)

    dataServer_IP  = ctlFvars['FTS_DATASERV_IP']
    ctlFile        = ctlFvars['CTL_FILE']

    #----------------------------
    # Check existance of ctl file
    #----------------------------
    ckFile(ctlFile, exitFlg=True)

    ctlFvars        = mainInputParse(ctlFile)

    BrukerIP       = ctlFvars['Bruker_IP']

    print('\n')
    #--------------------------------------------
    # Exit on TERM and HUP signals
    #--------------------------------------------       
    signal.signal(signal.SIGTERM, sighandler_TERM)
    #signal.signal(signal.SIGHUP, sighandler)  # only LINUX
    signal.signal(signal.SIGINT, sighandler_INT)

    #--------------------------------------------
    # Parse command line arguments
    #--------------------------------------------    
    parser          = optparse.OptionParser()
    parser.add_option('-c', '--config', help = 'read configuration from FILE [default: %default]', metavar = 'FILE', default = 'ifs125hr.conf')
    (options, args) = parser.parse_args()

    #--------------------------------------------
    # Read IFS125HR configuration file
    #--------------------------------------------  
    cf      = configparser.ConfigParser()
    #cf_file = cf.read(options.config)

    #--------------------------------------------
    # First argument must be ifm file
    #--------------------------------------------  
    try: ifm = args[0]
    except:
        print('arg may be missing... exiting!')
        raise SystemExit(CONFIG_ERR)
    
    #--------------------------------------------
    ## Get links of instrument control pages and add them to configuration options
    #-------------------------------------------- 
    opuslinks = get_opuslinks(BrukerIP)
    cf.add_section('ftir')
    for option in opuslinks.keys(): cf.set('ftir', option, 'http://%s/%s' % (BrukerIP, opuslinks[option]))

    #--------------------------------------------
    # Add parameters from setup section of ifm file to configuration parameters
    #--------------------------------------------  
    try:
        setup = parse_section(ifm, 'setup', listflag = False)
        cf.add_section('setup')
        for option in setup.keys():
            cf.set('setup', option, setup[option])
    except:
        pass

    # Check instrument status
    stat     = get_stat(cf.get('ftir', 'Status'))
    err_cnt  = int(stat['NERR'])   # Save error count

    if not check_idle(stat):
        print('FTIR instrument busy... exiting!')
        exit()

    # Check instrument diagnostics page
    diag = get_diag(cf.get('ftir', 'Diagnostics'))
    #print(diag)

    if not check_diag_ok(diag):
        print('FTIR DIAG_NOT_OK... exiting!')
        exit()
    
    #--------------------------------------------
    # Run commands from init section
    #--------------------------------------------
    cinit = parse_section(ifm, 'init')
    if cinit:
        # Send init section commands
        uri, content, header = send_cmd(cf.get('ftir', 'Command'), cinit)

        # Wait for instrument to get back to idle state
        while not check_idle(get_stat(cf.get('ftir', 'Status'))):
            time.sleep(1)

        # Check instrument diagnostics page again
        diag = get_diag(cf.get('ftir', 'Diagnostics'))

        if not check_diag_ok(diag):
            print('FTIR diagnostics check failed')
            exit()  

    #--------------------------------------------
    # Run commands from main section
    #--------------------------------------------
    cmain = parse_section(ifm, 'main')

    if cmain:
        # Send main section commands
        abort = True    # Abort necessary if program is interrupted
        uri, content, header = send_cmd(cf.get('ftir', 'Command'), cmain)

        # Loop until the instrument goes back to idle state
        fileno = 0  # File sequence counter
        while True:
            stat = get_stat(cf.get('ftir', 'Status'))

            # Finish loop when status goes back to idle
            #print(check_idle(stat))
            if check_idle(stat):
                break
            # Wait before repeating loop
            #print('Waiting for 5s...')
            time.sleep(5)
    
    #--------------------------------------------
    # Run commands from exit section
    #--------------------------------------------
    cexit = parse_section(ifm, 'exit')
    if cexit:
        # Send exit section commands
        uri, content, header = send_cmd(cf.get('ftir', 'Command'), cexit)
 

    # Wait for holdoff seconds
    if cf.has_option('setup', 'holdoff'):
        time.sleep(cf.getint('setup', 'holdoff'))

if __name__ == "__main__":
    #main(sys.argv[1:])
    main()