#
# $Id: ftirlib.py 71 2010-07-27 06:40:00Z dfeist $
#

#
# Useful functions for all FTIR scripts
#

#
# Catch external signals
#
def sighandler_TERM(signum, frame):
    print("Received SIGTERM signal... exiting!")
    exit()

def sighandler_INT(signum, frame):
    print("Received SIGINT signal... exiting!")
    exit()


#
# Convert a decimal or hex number from string to int
#
def str2int(S):

    S = S.strip()
    # Check for hex number
    try:
        S.index('0x', 0, 2)
    except ValueError:
        base = 10
    else:
        base = 16

    return int(S, base)


#
# Open a socket to the remote host
#
def open_socket(Host, Port, Timeout = 5):
    # Host:     Remote host IP address or name
    # Port:     TCP/IP port
    # Timeout:  Socket timeout

    import socket
    for res in socket.getaddrinfo(Host, Port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as error:
            s = None
            continue
        try:
            # Set timeout and try to connect to socket
            s.settimeout(Timeout)
            s.connect(sa)
        except KeyError:
            s.close()
            s = None
            continue
        break

    # Return socket object or None
    return s


#
# Send a command string to a socket/daemon
#
def send_socket(host, port, string, timeout = 5):
    # host:     Remote host IP address or name
    # port:     TCP/IP port
    # string:   String to send to socket
    # timeout:  Socket timeout [s]
    s = open_socket(host, port, timeout)
    if s:
        # Send command and close socket
        s.send(string)
        s.close()


#
# Send MySQL query, send warnings and errors to syslog
#
def mysql_query(db, mysqlcmd, maxrows = 0, how = 1):

    import _mysql
    from syslog import syslog, LOG_DEBUG, LOG_INFO, LOG_NOTICE, LOG_WARNING

    # Initialize return values
    rows = ()
    warnings = 0
    error = None

    if db and mysqlcmd:
        # Send MySQL query and retrieve result
        try:
            db.query(mysqlcmd)
            res = db.store_result()
            if res != None:
                rows = res.fetch_row(maxrows, how)
            warnings = db.warning_count()

        # Handle MySQL exceptions
        except _mysql.MySQLError as error:
            # stop running SQL commands if we have lost the server connection
            if error[0] == 2006 or error[0] == 2013:
                syslog(LOG_NOTICE, 'connection to database server lost: %s' % error)
                db = None

        # Log warnings or errors to syslog
        if warnings or error:
            syslog(LOG_DEBUG, 'MySQL query: "%s"' % mysqlcmd)
        if warnings:
            syslog(LOG_INFO, 'MySQL warnings: %d' % warnings)
        if error:
            syslog(LOG_WARNING, 'MySQL error %d: %s' % (error[0], error[1]))

    return db, rows
