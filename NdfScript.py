import urllib2
import cookielib
import base64
import os.path
import datetime
import json

# Load the config file
with open('NdfConfig.json') as config_file:    
    config = json.load(config_file)
# Load your username from the config file
user = config['user']
# Load your password from the config file
password = config['password']
# Filenames
# Filename of the cookies file. Directory will be loaded from config file 
cookieFile = config['files']['cookiesFilePath'] + '/cookies.txt'
# Filename of the logs file, Directory will be loaded from config file 
# (this format is day_month_year)
# Format details can be found at https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
logFile = config['files']['logsFilePath'] + '/%s-datafeed.json' % datetime.datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')
# Request Uri
uri = config['uri'].lower()

# Encode the username/password for HTTP Basic Authentication
base64string = base64.b64encode('%s:%s' % (user, password))

# Function that checks if a cookie exists by name in the cookie jar
# Takes the name of the cookie and the cookie jar object 
def cookieExists(name, cookies) :
    for cookie in cookies :
        if cookie.name == name :
            return True
    return False
            
# Create a cookie container
cookies = cookielib.LWPCookieJar()
# Load cookies from file if file exists
if os.path.isfile(cookieFile) :
    cookies.load(cookieFile, ignore_discard=True)
    # Check if we have the cursor for the feed we are calling
    if ('all' in uri and cookieExists('ALL', cookies) is False) or ('malware' in uri and cookieExists('MALWARE', cookies) is False) :
        # Since we do not have a cursor use the reset uri
        uri = config['resetUri']
# If cookie file is not on disk and you are not
# calling the test feed use the reset call to obtain cookie
elif 'test' not in uri:
    uri = config['resetUri']

# Create HTTP handlers
handlers = [
    urllib2.HTTPHandler(),
    urllib2.HTTPSHandler(),
    urllib2.HTTPCookieProcessor(cookies)
    ]
# Build URL opener object and pass handelers
opener = urllib2.build_opener(*handlers)

# Function that makes the request to API
def fetch(uri):
    req = urllib2.Request(uri)
    req.add_header('Authorization', 'Basic %s' % base64string)
    req.add_header('Accept', 'application/json')
    return opener.open(req)

# Function that saves the response to a file and saves cookies to file
def saveFiles(response, cookieFile, logFile):
    # Create a filename if no path is included it will save to the same directory the script is located
    # (this format is day_month_year-24hour_minute_second_Microsecond)
    # Format details can be found at https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    filename = logFile
    # Save the Json response as a variable
    filecontent = response.read()
    # Create a file
    fileIo = open(filename,'w')
    # Write json to file
    fileIo.write(filecontent)
    # Close the file 
    fileIo.close()
    # You may want to set permissions on the file here 
    # Details https://docs.python.org/2/library/os.html#os.chmod
    # Save cookies to a seperate file
    cookies.save(cookieFile,ignore_discard=True)

try:
    # Make the request
    res = fetch(uri)
    # Save the response/cookies
    saveFiles(res, cookieFile, logFile)

    # Keep making requests if 206 - partial content response is returned
    while res.getcode() == 206:
        logFile = config['files']['logsFilePath'] + '/%s-datafeed.json' % datetime.datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')
        res = None
        res = fetch(uri)
        saveFiles(res, cookieFile, logFile)
# Catch http errors and write them to the log file. Response errors will be in json format
except urllib2.HTTPError, ex:
    errorResponse = ex.read()
    fileIo = open(logFile,'w')
    fileIo.write(errorResponse)
    fileIo.close()
# Catch url errors and write them to the log file. Fails before response so create json formatted error
except urllib2.URLError, ex:
    errorResponse = '{"error": "%s"}' % ex.reason
    fileIo = open(logFile,'w')
    fileIo.write(errorResponse)
    fileIo.close() 