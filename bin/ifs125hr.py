#
# $Id: ifs125hr.py 71 2010-07-27 06:40:00Z dfeist $
#

#
# Exit codes for programs
#
CONFIG_ERR = 1      # Wrong or missing configuration parameter
GEN_EXCEPT = 2      # General exception caught - check logfiles for details
FTIR_BUSY = 3       # FTIR instrument not idle when it should be
DIAG_NOT_OK = 4     # Not all flags on diagnostics page have status 'OK'
FILE_ERR = 5        # Problem with file or directory
USER_BRK = 6        # Program interrupted by user
MYSQL_ERR = 7       # Problems connecting to MySQL server
SYS_EXIT = 8        # Program was stopped by external signal or premature exit command

#
# Useful functions for communication with Bruker IFS125HR
#

#
# Check if status is idle
#
def check_idle(stat):
    # stat: FTIR status flags
    #if not stat.has_key('MSTCO'):
    #print(stat)
    if not 'MSTCO' in stat:
        return None
    return stat['MSTCO'] == 'IDL'


#
# Extract key/value pairs from HTML tables with regular expressions
#
# Returns a dictionary of the form { key: value } for the whole table
# Used by functions that parse the status, diagnostics etc. pages
#
def exctract_keyval(html, key_re, key_col, val_re, val_col):
    # html: HTML data stream containing a table
    # key_re: regular expression that identifies key in group('key')
    # key_col: column index for key (starts with 0)
    # val_re: regular expression that identifies value in group('val')
    # val_col: column index for value (starts with 0)

    # Initialize key/value dictionary
    keyval = {}

    # Parse HTML table rows
    rows = get_table_rows(html)
    for row in rows:
        # Extract columns
        cols = get_table_cols(row)

        try:
            # Extract key and val using the submitted regular expressions
            key = key_re.match(cols[key_col]).group('key')
            val = val_re.match(cols[val_col]).group('val')
        except:
            continue

        # Check if key already exists
        #if keyval.has_key(key):
        if key in keyval:
            # Append values for this key to a list
            if type(keyval[key]) is list:
                # Append value to existing list
                keyval[key].append(val)
            else:
                # Make a list of values
                keyval[key] = [ keyval[key], val ]
        else:
            # New key: just save value
            keyval[key] = val

    # Return keyval dictionary
    return keyval


#
# Read Opus links page to find spectrometer control URLs
#
def get_opuslinks(host):
    # host: host name/IP of the spectrometer

    # Open URL and save output in string
    opuslinks_url = 'http://%s/opuslinks.htm' % host
    html, header = get_url(opuslinks_url)

    # These regular expressions identify clear text columns and links
    import re
    key_re = re.compile('<TD.*>(?P<key>\S*)</TD>', re.IGNORECASE | re.DOTALL )
    val_re = re.compile('<TD.*>(?P<val>\S*)</TD>', re.IGNORECASE | re.DOTALL )
    #
    # NOTE: the EwsOpusCommunication_2_1.pdf claims that one should use tags
    # called HTG_*_PAGE to identify the correct pages. However, these tags
    # do not exist on opuslinks.htm in our EWS15 1.480 May 23 2007. The tags
    # on that page have different names. Therfore, this routine reads the clear
    # text description in the first column of the table to identify the links.
    #

    # Extract key/value pairs from html
    opuslinks = exctract_keyval(html, key_re, 0, val_re, 1)

    # Return link list
    return opuslinks


#
# Read status page and return output in a dictionary
#
def get_stat(stat_url):
    # stat_url: URL of spectrometer status page

    # Open URL and save output in string
    html, header = get_url(stat_url)

    # Regular expression that parses HTML table column into fields 'key', 'value'
    # 'key' is content of tag 'id', value is table column value
    # ignores case, may cross lines
    import re
    pattern = re.compile('<TD.*\sID="?(?P<key>\w*)"?.*>(?P<value>\S*)</TD>', re.IGNORECASE | re.DOTALL )

    # These regular expressions identify clear text columns and links
    import re
    key_re = re.compile('<TD.*\sID="?(?P<key>\w*)"?.*?>', re.IGNORECASE | re.DOTALL )
    val_re = re.compile('<TD.*>(?P<val>\S*)</TD>', re.IGNORECASE | re.DOTALL )

    # Extract key and value from 2nd column, ignore 1st
    stat = exctract_keyval(html, key_re, 1, val_re, 1)

    # Return status flags
    return stat

#
# Read diagnostics page and return output in a dictionary
#
def get_diag(diag_url):
    # diag_url: URL of spectrometer diagnostics page

    # Open URL and save output in string
    html, header = get_url(diag_url)

    # Regular expression that parses HTML table column into fields 'key', 'value'
    # 'key' is content of tag 'id', value is table column value of 2nd column
    # ignores case, may cross lines
    import re
    key_re = re.compile('<TD.*\sID="?(?P<key>\w*)"?.*?>', re.IGNORECASE | re.DOTALL )
    val_re = re.compile('<TD.*?>(?P<val>\S*)</TD>', re.IGNORECASE | re.DOTALL )

    # Extract key from 1st column, value from 2nd
    diag = exctract_keyval(html, key_re, 0, val_re, 1)

    # Return diagnostic flags
    return diag


#
# Check if all FTIR diagnostics flags are 'OK'
#
def check_diag_ok(diag):
    # diag: FTIR diagnostic flags

    for key in diag.keys():
        #if (diag[key] != 'OK') or (diag[key] != 'WARNING'):
        #    return False

        if (diag[key] == 'ERROR'):
            return False

    return True


#
# Extract table rows from a HTML data stream
#
def get_table_rows(html):
    # html: string containing HTML data

    # Find shortest substrings enclosed by '<TR' and '/TR>'
    # ignore case, may cross lines
    import re
    pattern = re.compile('<TR.*?>.*?</TR>', re.IGNORECASE | re.DOTALL)
    rows = pattern.findall(html)

    # return list of rows
    return rows


#
# Extract table columns from a HTML table row
#
def get_table_cols(row):
    # row: string containing a single HTML table row

    import re
    # Find shortest substrings enclosed by '<TD' and '/TD>'
    # ignore case, may cross lines
    pattern = re.compile('<TD.*?>.*?</TD>', re.IGNORECASE | re.DOTALL)
    cols = pattern.findall(row)

    # return list of cols
    return cols


#
# Download file from spectrometer and save it locally
#
def download_url(url, file):
    # url:  URL of file on spectrometer
    # file: local file name including full path

    # Open URL and save output in string
    #import urllib
    #(filename, header) = urllib.urlretrieve(url, file)

    # Have to use wget because of broken HTTP header from EWS
    import os
    cmd = 'wget -q -O %s %s' % (file, url)
    os.popen(cmd)
    try:
        filesize = os.stat(file).st_size
    except:
        filesize = None

    # return size of downloaded file
    return filesize


#
# Get file from spectrometer, return content as string
#
def get_url(url):
    # url:  URL of file on spectrometer

    # Open URL and save output in string
    import urllib
    #import urllib.request
    from urllib.request import urlopen

    with urlopen(url) as url_:
        #u        = url_.read()
        #print(u)
        #u=u.decode()
        header   = url_.info()
        content  = url_.read().decode('utf-8')

    #u = urllib.urlopen(url)
    #header = u.info()
    #content = u.read()
    url_.close()

    #print(content.decode('utf-8'))#, header.decode('utf-8'))

    #content=content.decode()
    #header=header.decode()

    # Return file content and HTTP header
    return content, header


# def get_url(url):
#     # url:  URL of file on spectrometer

#     # Open URL and save output in string
#     import urllib
#     u = urllib.urlopen(url)
#     header = u.info()
#     content = u.read()
#     u.close()

#     # Return file content and HTTP header
#     return content, header


#
# Read parameters from a section in a config file
# and return parameters as list or dictionary
#
def parse_section(file, section, listflag = True):
    # file:     name of config file
    # section:  name of section
    # listflag: True: return parameters as list, False: return as dictionary

    curr_section = None # Current section
    if listflag:
        params = [] # Parameters list
    else:
        params = {} # Parameter dictionary

    import re
    # Regular expression to parse "key = value" lines
    re_keyval = re.compile('(?P<key>.*?)\s*=\s*(?P<value>.*)')
    # Regular expression to parse "[section]" lines
    re_section = re.compile('\[(?P<section>.*)\]')

    # Read file
    f = open(file)
    try:
        for line in f:
            # remove comments and whitespace
            line = line.partition('#')[0].strip()

            # Check if line contains a section header
            match = re_section.match(line)
            if match:
                curr_section = match.group('section')

            # Skip the rest if we are in the wrong section
            if curr_section != section:
                continue

            # Process lines that contain key/value pairs
            match = re_keyval.match(line)
            if match:
                key = match.group('key')
                value = match.group('value')

                # Apply %? code replacements in config parameters

                # strftime() replacements
                import time
                #print(value)
                value = time.strftime(value)

                # Replace %$ with current process id
                import os
                value = value.replace('%$', '%d' % os.getpid())

                # Return as list or dictionary
                if type(params) is list: # Return as list
                    params.append((key, value))
                if type(params) is dict: # Return as dictionary
                    params[key] = value
    finally:
        f.close()

    # Return parameter list
    return params


#
# Send command to spectrometer
#
def send_cmd(cmd_url, params):
    # cmd_url: URL of spectrometer command page
    # params: list of parameters
    # cmd:    file name on spectrometer for sending commands

    # Build and send command URI
    import urllib
    #cmd_uri = '%s?%s' % (cmd_url, urllib.urlencode(params))
    cmd_uri = '%s?%s' % (cmd_url, urllib.parse.urlencode(params))

    # Send command
    print('Sending command: {}'.format(cmd_uri))
    content, header = get_url(cmd_uri)

  
    # return complete escaped URI, output and HTTP header
    return cmd_uri, content, header
