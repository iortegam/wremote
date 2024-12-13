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

import pymysql


#sys.path.append('/home/data/iortega/python/FTIR_interface')
sys.path.append('C:\\Users\\bldopus\\wremote\\python\\FTIR_interface')
from ifs125hr import *
from ftirlib import *


print('\n')
#--------------------------------------------
# Exit on TERM and HUP signals
#--------------------------------------------       
signal.signal(signal.SIGTERM, sighandler_TERM)
#signal.signal(signal.SIGHUP, sighandler)  # only LINUX
signal.signal(signal.SIGINT, sighandler_INT)

#--------------------------------------------
# LOGGING
#--------------------------------------------    
# Start logging
#import syslog
#import pysyslogclient
#import logging
#from pysyslogclient import *
#from syslog import *

#openlog(os.path.basename(sys.argv[0]), 0, LOG_LOCAL0)

#--------------------------------------------
# Parse command line arguments
#--------------------------------------------    
parser          = optparse.OptionParser()
parser.add_option('-c', '--config', help = 'read configuration from FILE [default: %default]', metavar = 'FILE', default = 'ifs125hr.conf')
(options, args) = parser.parse_args()

# Any uncaught exception in the following part will exit the program
#
abort    = False   # Initialize abort flag
exitcode = 0    # Initialize exit status
#try:

#--------------------------------------------
# Read IFS125HR configuration file
#--------------------------------------------  
cf      = configparser.ConfigParser()
cf_file = cf.read(options.config)

#if cf_file:
#    syslog(LOG_DEBUG, 'configuration read from %s' % cf_file)
#else:
#    syslog(LOG_ERR, 'No IFS125HR configuration file found')
#    raise SystemExit(CONFIG_ERR)

#--------------------------------------------
# First argument must be ifm file
#--------------------------------------------  
try:
    ifm = args[0]
    #syslog(LOG_INFO, 'Running FTIR commands from %s' % ifm)
except:
    #syslog(LOG_ERR, 'No ifm file name supplied')
    raise SystemExit(CONFIG_ERR)

#--------------------------------------------
## Get links of instrument control pages and add them to configuration options
#-------------------------------------------- 
opuslinks = get_opuslinks(cf.get('ftir', 'host'))
for option in opuslinks.keys():
    cf.set('ftir', option, 'http://%s/%s' % (cf.get('ftir', 'host'), opuslinks[option]))

for k in cf['ftir']: print(k, cf['ftir'][k])
exit()
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

#--------------------------------------------
# Add parameters from strackd section of ifm file to the configuration options
#--------------------------------------------
try:
    setup = parse_section(ifm, 'strackd', listflag = False)
    cf.add_section('strackd')
    for option in setup.keys():
        cf.set('strackd', option, setup[option])
except:
    pass

#--------------------------------------------
# Create savepath if necessary
#--------------------------------------------
if cf.has_option('setup', 'savepath'):
    if not os.path.isdir(cf.get('setup', 'savepath')):
        try:
                os.makedirs(cf.get('setup', 'savepath'))
        except:
            #syslog(LOG_ERR, 'Error creating directory "%s"' % cf.get('setup', 'savepath'))
            raise SystemExit(FILE_ERR)
    #syslog(LOG_DEBUG, 'Created directory %s' % cf.get('setup', 'savepath'))

#--------------------------------------------
# Connect to MySQL data base server if config file contains [mysql] section
#--------------------------------------------
if cf.has_section('mysql'):
    
    #db = _mysql.connect(host = cf.get('mysql', 'host'), port = cf.getint('mysql', 'port'), user = cf.get('mysql', 'user'), passwd = cf.get('mysql', 'passwd'), db = cf.get('mysql', 'db'))
    #db = mysql.connector.connect(host = cf.get('mysql', 'host'), port = cf.getint('mysql', 'port'))
    db = pymysql.connect(host = cf.get('mysql', 'host'), port = cf.getint('mysql', 'port'), user = cf.get('mysql', 'user'), passwd = cf.get('mysql', 'passwd'), db = cf.get('mysql', 'db'))#, read_timeout=20)
    
    #syslog(LOG_INFO, 'connected to database server %s as user %s' % (cf.get('mysql', 'host'), cf.get('mysql', 'user')))
    # Create entry in measurement log and retrieve ID of this measurement
    sql = "INSERT INTO %s SET start_time=NOW(), savepath='%s', type='%s'" % (cf.get('mysql', 'meas_tbl'), cf.get('setup', 'savepath'), cf.get('setup', 'type'))
    db.query(sql)
    meas_id = db.insert_id()    # Measurement identifier
else:
    db = None
    meas_id = 0

# Change instrument status
if db:
    sql = "UPDATE %s SET ftir='measuring'" % cf.get('mysql', 'stat_tbl')
    db.query(sql)

# Check instrument status
stat     = get_stat(cf.get('ftir', 'Status'))
err_cnt  = int(stat['NERR'])   # Save error count

if not check_idle(stat):
    print('FTIR instrument busy... exiting!')
    #syslog(LOG_WARNING, 'FTIR instrument busy')
    #raise SystemExit(FTIR_BUSY)
    exit()

# Check instrument diagnostics page
diag = get_diag(cf.get('ftir', 'Diagnostics'))
#print(diag)

if not check_diag_ok(diag):
    #syslog(LOG_ERR, 'FTIR diagnostics check failed')
    print('FTIR DIAG_NOT_OK... exiting!')
#   raise SystemExit(DIAG_NOT_OK)
    exit()

#
# init section
#
# Update measurement status
if db:
    sql = "UPDATE %s SET status='init' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), meas_id)
    db.query(sql)


#Run commands from init section
cinit = parse_section(ifm, 'init')
if cinit:
    # Send init section commands
    uri, content, header = send_cmd(cf.get('ftir', 'Command'), cinit)

    # Log init section commands
    if db:
        sql = "UPDATE %s SET init_uri='%s' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), uri, meas_id)
        db.query(sql)

    # Wait for instrument to get back to idle state
    while not check_idle(get_stat(cf.get('ftir', 'Status'))):
        time.sleep(1)

    # Check instrument diagnostics page again
    diag = get_diag(cf.get('ftir', 'Diagnostics'))

    if not check_diag_ok(diag):
        print('FTIR diagnostics check failed')
        #syslog(LOG_ERR, 'FTIR diagnostics check failed')
        #raise SystemExit(DIAG_NOT_OK)
        exit()  
#
# main section
#

# Update measurement status
if db:
    sql = "UPDATE %s SET status='main' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), meas_id)
    db.query(sql)


# Run commands from main section
cmain = parse_section(ifm, 'main')

if cmain:
    # Send main section commands
    abort = True    # Abort necessary if program is interrupted
    uri, content, header = send_cmd(cf.get('ftir', 'Command'), cmain)

    # Log main section commands
    if db:
        sql = "UPDATE %s SET main_uri='%s' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), uri, meas_id)
        db.query(sql)

    # Loop until the instrument goes back to idle state
    fileno = 0  # File sequence counter
    while True:
        stat = get_stat(cf.get('ftir', 'Status'))

        ## Check for pending data files
        ##if stat.has_key('DAFI'):
        # if 'DAFI' in stat:
        #     if type(stat['DAFI']) is list:
        #         dfiles = stat['DAFI']
        #     else:
        #         dfiles = [ stat['DAFI'] ]

        #     # Download pending data files
        #     for dfile in dfiles:
        #         url = 'http://%s/%s' % (cf.get('ftir', 'host'), dfile)
        #         file = os.path.join(cf.get('setup', 'savepath'), dfile)

        #         # Download file
        #         filesize = download_url(url, file)

        #         # Log file in data file table
        #         fileno += 1
        #         if db:
        #             sql = "INSERT INTO %s SET timestamp=NOW(), measurement=%d, filename='%s', fileno=%d" % (cf.get('mysql', 'file_tbl'), meas_id, dfile, fileno)
        #             if filesize is not None:
        #                 sql += ', filesize=%d' % filesize
        #             db.query(sql)

        # Finish loop when status goes back to idle
        if check_idle(stat):
            break

        # Wait before repeating loop
        time.sleep(5)

# Main command finished, nothing to abort
abort = False

#
# exit section
#

# Update measurement status
if db:
    sql = "UPDATE %s SET status='exit' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), meas_id)
    db.query(sql)


# Run commands from exit section
cexit = parse_section(ifm, 'exit')
if cexit:
    # Send exit section commands
    uri, content, header = send_cmd(cf.get('ftir', 'Command'), cexit)

    # Log exit section commands
    if db:
        sql = "UPDATE %s SET exit_uri='%s' WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), uri, meas_id)
        db.query(sql)

# Log instrument status at the end of measurement
stat = get_stat(cf.get('ftir', 'Status'))
if db:
    sql = "UPDATE %s SET end_time=NOW(), errors=%d, pressure=%s WHERE ID=%d" % (cf.get('mysql', 'meas_tbl'), int(stat['NERR']) - err_cnt, stat['PRESIC'], meas_id)
    db.query(sql)


#except: exit()
        

# Wait for holdoff seconds
if cf.has_option('setup', 'holdoff'):
    time.sleep(cf.getint('setup', 'holdoff'))

# Exit
sys.exit(exitcode)
