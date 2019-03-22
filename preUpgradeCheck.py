# ## Libraries and functions
# import libraries
import subprocess
import re
import datetime
import time
import json
from binascii import hexlify

# function to parse lscpu command output
def lscpuParser(response):
    response = re.sub(' +',' ',response)
    responseList = response.split('\n')
    responseData = {}
    for each in responseList:
        if each != '':
            tempKey,tempVal = each.split(':')
            tempKey = tempKey.strip()
            tempVal = tempVal.strip()
            responseData[tempKey] = tempVal
        
    return(responseData)

# parse version data
def versionParser(config):
    config = config.replace('"','')
    config = config.replace("'",'')
    temp = config.split('=')
    temp0 = temp[0].rstrip()
    temp1 = temp[1].rstrip()
    return([temp0,temp1])

# the following function processes the response from df -Ph command run on
# exactly one path
def processDfOutput(response):
    # process response
    response = response.replace('Mounted on','Mounted_on').replace('\n',' ')
    # remove extra spaces
    temp = re.sub(' +',' ',response).split(' ')
    # split the lists
    labs = temp[0:6]
    vals = temp[6:]

    # create a dictionary
    dfOutput = dict(zip(labs,vals))
    
    return(dfOutput)

# create a function to execute bash commands
def bashCMD(command):
    
    """return the result bash command execution
    
    The *command* parameter is simply the bash command
    as a BYTESTRING."""
    
    # open a process
    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # execute command and capture result
    response, err = process.communicate(command)
    # return response
    response = response.decode('utf-8')
    return(response)

# a function defined to run alation shell "alation_conf" command
def alationConfQuery(configVal):
    # define command
    cmd = '''sudo chroot "/opt/alation/alation" /bin/su - alationadmin -c "alation_conf {}"'''.format(configVal).encode('utf-8')
    response = bashCMD(cmd)
    # parse out the response
    key,val = response.replace('\n','').split('=')
    key,val = key.strip(),val.strip()
    # return response
    return(key,val)
    
def colPrint(inStr,color):
    # create output templates
    if color == 'G':
        # all clear = green
        colPrintOut = '\x1b[6;30;42m' + inStr + '\x1b[0m'
    elif color == 'R':
        # warning = red
        colPrintOut = '\x1b[6;30;41m' + inStr + '\x1b[0m'
    elif color == 'O':
        # caution = orange
        colPrintOut = '\x1b[6;30;43m' + inStr + '\x1b[0m'
        
    return(colPrintOut)

# ## Version information check
def versionCheck():
    # run the version check
    # run bash command and get the response
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    cat /opt/alation/django/main/alation_version.py"""
    response = bashCMD(cmd)
    versionData = response.strip('\n').split('\n')
    versionFlag = False
    flag520 = False

    # find Alation major version number
    for each in versionData:
        if "ALATION_MAJOR_VERSION" in each:
            majorVersion = int(each.split(' = ')[1])
        elif "ALATION_MINOR_VERSION" in each:
            minorVersion = int(each.split(' = ')[1])
        elif "ALATION_PATCH_VERSION" in each:
            patchVersion = int(each.split(' = ')[1])
        elif "ALATION_BUILD_VERSION" in each:
            buildVersion = int(each.split(' = ')[1])

    version = str(majorVersion) + '.' + str(minorVersion) + '.' + str(patchVersion) + '.' + str(buildVersion)
    
    # check major version requirement
    if majorVersion > CRITICALVERSION:
        print('Version > {}.{} (current version = {}): '.format(CRITICALVERSION,CRITICALMINORVERSION,version) + colPrint('OK!','G'))
        versionFlag = True

    elif majorVersion == CRITICALVERSION:
        if minorVersion >= CRITICALMINORVERSION:
            print('Version > {}.{} (current version = {}): '.format(CRITICALVERSION,CRITICALMINORVERSION,version) + colPrint('OK!','G'))
            versionFlag = True

        else:
            print(colPrint('Cannot upgrade to V R4 from version {}. Please contact support.'.format(version),'R'))
            versionFlag = False
    # check additional version information
    elif majorVersion <= 4:
        if minorVersion <= 10:
            print('{} Be sure to follow 4.10.x or below version specific steps here: https://alationhelp.zendesk.com/hc/en-us/articles/360011041633-Release-Specific-Update-Pre-Checks'.format(colPrint('WARNING!','O')))

    # check additional version information
    else:
        flag520 = True
        print(colPrint('Cannot upgrade to V R4 from version {}. Please contact support.'.format(version),'R'))


        
    return(versionData,majorVersion,minorVersion,patchVersion,buildVersion,version,versionFlag,flag520)

# ## Replication mode check
def replicationCheck():
    # check replication
    # define commands
    cmd = b"curl -L --insecure http://localhost/monitor/replication/"
    # get response
    response = bashCMD(cmd)
    # process response
    replicationMode = response.split('{')[1].split('}')[0].split(': ')[1].replace('"','')

    # check replication criteria
    if replicationMode == 'standalone':
        print('Replication mode standalone: ' + colPrint('OK!','G'))
        replicationFlag = True
    else:
        print(colPrint('REPLICATION MODE NOT STANDALONE!','R'))
        replicationFlag = False
    
    return(replicationMode,replicationFlag)
    
# ## Minimum space requirement check
def minSpaceCheck():
    # check if a minimum of MINDISKSPACE GB space is free at /opt/alation/ by calling: df -h /opt/alation
    # define command
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    df -Ph /"""
    # run bash command and get response
    response = bashCMD(cmd)
    # get df readout
    installDfOutput = processDfOutput(response)
    # get remaining disk space
    availSize = float(re.sub("\D", "", installDfOutput['Avail']))
    # check if there is at least MINDISKSPACE GB space available
    if availSize > MINDISKSPACE:
        print('Minimum {}GB disk space (available in /opt/alation = {}GB): '.format(MINDISKSPACE,availSize) + colPrint('OK!','G'))
        diskFlag = True
    else:
        print('Minimum {}GB disk space (available in /opt/alation = {}GB): '.format(MINDISKSPACE,availSize) + colPrint('FAIL!','R'))
        diskFlag = False

    # check if disk is at least 90% full
    usage = float(re.sub("\D", "", installDfOutput['Use%']))
    if usage >= WARNINGATDISKUSE:
        print(colPrint('Caution! /opt/alation is {}% full'.format(usage),'O'))
        
    return(installDfOutput,availSize,usage,diskFlag)
    
# ## Data drive and backup drive space and mounting check
def dataAndBackupDriveCheck():
    # data and backup mount check
    # define bash command for data drive
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    df -Ph /data1/"""
    # run bash command and get response
    dataResponse = bashCMD(cmd)
    # get df readout
    dataDfOutput = processDfOutput(dataResponse)

    # define bash command for backup drive
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    df -Ph /data2/"""
    # run bash command and get response
    backupResponse = bashCMD(cmd)
    # get df readout
    backupDfOutput = processDfOutput(backupResponse)

    # ensure the mounting points are different for data and backup
    if dataDfOutput['Mounted_on'] != backupDfOutput['Mounted_on']:
        mountFlag = True
        print('Data and backup on different mount: {}'.format(colPrint('OK!','G')))
    else:
        print('Data and backup on different mount: {}'.format(colPrint('FAIL!','R')))
        mountFlag = False

    # ensure the storage devices are different for data and backup
    if dataDfOutput['Filesystem'] != backupDfOutput['Filesystem']:
        storageFlag = True
        print('Data and backup on different device: {}'.format(colPrint('OK!','G')))
    else:
        storageFlag = False
        print('Data and backup on different device: {}'.format(colPrint('FAIL!','R')))

    # compare backup disk size and data disk size
    backupToDataRatio = float(re.sub("\D", "", backupDfOutput['Size']))/float(re.sub("\D", "", dataDfOutput['Size']))

    # check if backup disk is at least MINBACKUPFACTOR the size of data disk
    if backupToDataRatio >= MINBACKUPFACTOR:
        print('Backup disk to data disk size ratio is at least {}: {}'.format(MINBACKUPFACTOR,colPrint('OK!','G')))
    else:
        print('Backup disk to data disk size ratio is {} which is lower than reccommended {}: {}'.format(backupToDataRatio,MINBACKUPFACTOR,colPrint('WARNING','O')))
    
    return(backupToDataRatio,backupDfOutput,storageFlag,mountFlag,dataDfOutput)

# ## Backup checks
def confirmBackups():
    # confirm backups
    # read in backup files
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    ls -lR --block-size=M /data2/backup/"""
    # run bash command and get response
    response = bashCMD(cmd)

    backupFilesTemp = response.split('\n')
    backupFiles = []
    fileDatMap = {}
    for each in backupFilesTemp:
        if "alation_backup.tar.gz" in each:
            # get date
            dtTemp = each.split(' ')[-1]
            # get filename
            backupFiles.append(dtTemp)
            # map filename to data
            fileDatMap[dtTemp.split('_')[0][:8]] = each
        

    # extract the date information
    backupDates = []
    backupDTs = []
    for each in backupFiles:
        temp = each.split('_')[0][:8]
        backupDates.append(temp)
        tempDt = datetime.datetime.strptime(temp,'%Y%m%d').date()
        backupDTs.append(tempDt)

    # compute age of backups
    today = datetime.date.today()

    tDiff = []
    diffRes = {}
    for each in backupDTs:
        diff = int((today - each).days)
        tDiff.append(diff)
        diffRes[diff] = each

    # get the newest backup file
    newestBackup = diffRes[min(tDiff)].strftime('%Y%m%d')
    # get backup filesize information
    response = fileDatMap[newestBackup]
    # process the response (fize size in MB)
    fileSize = float(response.split(' ')[4].replace('M',''))

    # check if the backup filesize is at least 10 MB
    if fileSize <= 10:
        print(colPrint('Backup file size {} less than 10 MB'.format(fileSize),'R'))

    # get the newest backup
    newestBackup = diffRes[min(tDiff)].strftime('%Y-%m-%d')
    # check age of the backup
    if len(backupDates) >= 1:
        if len(backupDates) == 1:
            if min(tDiff) <= MAXBACKUPAGE:
                print('Recent backup available (Last backup on: {}, filesize: {}MB): {}'.format(newestBackup,fileSize,colPrint('OK!','G')))
                print(colPrint('WARNING! Only one backup file found.','O'))
                backupFlag = True
            else:
                print('No recent backup available. (Last backup on: {}, age: {}): {}'.format(newestBackup,str(min(tDiff)),colPrint('FAIL!','R')))
                backupFlag = False

        elif len(backupDates) >= 2:
            if min(tDiff) <= MAXBACKUPAGE:
                print('Recent backup available (Last backup on: {}, filesize: {}MB): {}'.format(newestBackup,fileSize,colPrint('OK!','G')))
                backupFlag = True
            else:
                print('No recent backup available. (Last backup on: {}, age: {}): {}'.format(newestBackup,str(min(tDiff)),colPrint('FAIL!','R')))
                backupFlag = False
        else:
            print(colPrint('WARNING! No backup found!','R'))
            backupFlag = False
        
    return(backupFlag,backupFiles)

# ## CPU and memory info
def cpuMemData():
    # extract CPU information
    # define commands
    cmd = b"lscpu"
    # get response
    cpuResponse = bashCMD(cmd)
    # process response
    lscpuOutput = lscpuParser(cpuResponse)

    # get total memory information
    # define commands
    cmd = b"grep MemTotal /proc/meminfo"
    # get response
    memResponse = bashCMD(cmd)
    # process response
    memResponse = lscpuParser(memResponse)
    
    return(memResponse,lscpuOutput)

# ## Mongo Check
def mongoCheck(fullLog):
    # mongoDB check
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    du -k --max-depth=0 -BG /data1/mongo/"""
    # get response
    response = bashCMD(cmd)

    # parase the response
    mongoSize = float(re.sub("\D", "", response.split('\t')[0]))
    fullLog['mongoSize'] = response.split('\t')[0]

    # check if available disk space is at least MONGOx the size of mongoDB
    availDataSpace = float(re.sub("\D", "", fullLog['dataDirDf']['Size']))
    #print('Space available in data drive: {}GB'.format(availDataSpace))

    if availDataSpace/mongoSize > MONGOx:
        #print('Available space {}GB in /data1/ is at least {}x greater than mongoDB size {}GB: {}'.format(availDataSpace,MONGOx,mongoSize,colPrint('OK!','G')))
        mongoFlag = True
    else:
        #print('{} Not enough space available space in /data1/ to update to Alation V R2 or higher! Mongo size = {}GB, available size = {}GB.'.format(colPrint('FAIL!','R'),mongoSize,availDataSpace))
        mongoFlag = False
    
    return(mongoFlag,fullLog,availDataSpace,mongoSize)
    
# ## postgreSQL Check
def pgSQLCheck(fullLog):
    # postgreSQL check
    cmd = b"""sudo chroot "/opt/alation/alation" /bin/su - alation
    du -k --max-depth=0 -BG /data1/pgsql/"""
    # get response
    response = bashCMD(cmd)

    # get Alation Analytics status check
    aaFlag = alationAnalyticsCheck()

    # parase the response
    pgsqlSize = float(re.sub("\D", "", response.split('\t')[0]))
    fullLog['pgsqlSize'] = response.split('\t')[0]

    # see if check for Alation Analytics is needed
    if not aaFlag:
        # run the check
        if availDataSpace/pgsqlSize > PGSQLx:
            print('(For Alation Analytics) Available space in /data1/ {}GB is at least {}x greater than postgreSQL size {}GB: {}'.format(availDataSpace,PGSQLx,pgsqlSize,colPrint('OK!','G')))
            pgsqlFlag = True
        else:
            print('{} Not enough space available space in /data1/ to turn on analytics. postgreSQL size = {}, available size = {}.'.format(colPrint('WARNING','O'),pgsqlSize,availDataSpace))
            pgsqlFlag = False

        # ## combined space check
        fullSpaceNeeded = pgsqlSize*PGSQLx + mongoSize*MONGOx

        # check against available space
        if availDataSpace > fullSpaceNeeded:
            print('Available space, {}GB, is greater than the combined space needed, {}GB: {}'.format(availDataSpace,fullSpaceNeeded,colPrint('OK!','G')))
            combinedSpaceFlag = True
        else:
            spaceDiff = abs(fullSpaceNeeded - availDataSpace)
            print('{} Combined space check Please expand /opt/alation/ drive by {}GB before turning on analytics!'.format(colPrint('WARNING!','O'),spaceDiff))
            combinedSpaceFlag = False
            
        return(combinedSpaceFlag,pgsqlFlag,fullLog)

    elif aaFlag:
        pgsqlFlag = True
        # if Alation Analytics is enabled, we have a different space check
        # ## combined space check (it simply becomes mongoDB check)
        fullSpaceNeeded = mongoSize*MONGOx

        # check against available space
        if availDataSpace > fullSpaceNeeded:
            print('Available space, {}GB, is greater than the combined space needed, {}GB: {}'.format(availDataSpace,fullSpaceNeeded,colPrint('OK!','G')))
            combinedSpaceFlag = True
        else:
            spaceDiff = abs(fullSpaceNeeded - availDataSpace)
            print('{} Combined space check Please expand /opt/alation/ drive by {}GB before turning on analytics!'.format(colPrint('WARNING!','O'),spaceDiff))
            combinedSpaceFlag = False
            
        return(combinedSpaceFlag,pgsqlFlag,fullLog)

# ## datadog check
def dataDogCheck(fullLog):
    # Datadog check
    key,val = alationConfQuery('datadog.enabled')
    fullLog[key] = val

    if val == 'False':
        print("{} Datadog not enabled!".format(colPrint('WARNING','O')))
        datadogFlag = False
    elif val == 'True':
        print("Datadog enabled: ".format(colPrint('OK!','G')))
        datadogFlag = True
        
    return(fullLog,datadogFlag)

# ## Alation Analytics check
def alationAnalyticsCheck():
    # Datadog check
    key,val = alationConfQuery('alation.feature_flags.enable_alation_analytics')
    fullLog[key] = val

    if val == 'False':
        aaFlag = False
    elif val == 'True':
        aaFlag = True
        
    return(aaFlag)
    
## # Extract site ID
def siteIDExtract(fullLog):
    # site_id
    key,siteID = alationConfQuery('site_id')
    fullLog[key] = siteID
    
    return(fullLog,siteID)
    
# parse out the information 
def fileParser(inMessage):
    if len(inMessage) > 1 and ':' in inMessage:
        # split out the directory name and response
        k,v = inMessage.split(':')
        k = k.strip()
        v = v.strip()
        # return values
        return(k,v)
    else:
        return(False,False)

# ## get version information
def linuxVersionInfo():
    # create the command
    cmd = b'cat /proc/version'
    # run and get response
    vResponse = bashCMD(cmd).strip()
    return(vResponse)
    
# ## Get previously installed Alation versions
def alationVerHist():
    # create the command
    cmd = b'update-alternatives --display alation'
    # run and get response
    avResponse = bashCMD(cmd).strip().replace('\n','|')
    return(avResponse)

# ## Configuration parameters
# config
# hex marker to make data processing easier
# use a string no one will use in a normal zendesk ticket
hex_marker = hexlify(b"magnetohydrodynamics")
# minimum empty disk requirement
MINDISKSPACE = 15.0
# warn if disk is at or above below percentage
WARNINGATDISKUSE = 90.0
# critical MINIMUM major version to check for
CRITICALVERSION = 4
# critical MINIMUM minor version to check for
CRITICALMINORVERSION = 8
# maximum acceptable age of a backup in days
MAXBACKUPAGE = 5
# the minimum size of backup disk as a multiple of data disk
# e.g. 1.5 checks size(backup disk)/size(data disk) >= 1.5
MINBACKUPFACTOR = 1.5
# mongoDB size requirements
MONGOx = 0
# postgreSQL multiplication factor for analytics
# in order to turn on analytics, the pgsql folder will doulbe 
# in size.
PGSQLx = 2
# flag to indicate code failure
failure = False
# steps to be run manually
steps = []

##################
# Code start
##################

# ## Version information check
try:
    versionData,majorVersion,minorVersion,patchVersion,buildVersion,version,versionFlag,flag520 = versionCheck()
except:
    versionFlag = False
    flag520 = False
    steps.append('2')


# ## Replication mode check
try:
    replicationMode,replicationFlag = replicationCheck()
except:
    replicationFlag = False
    failure = True
    steps.append('3')
    print(colPrint('WARNING! Replication check failed! Please make sure the installation is standalone!','R'))


# ## Minimum space requirement check
try:
    installDfOutput,availSize,usage,diskFlag = minSpaceCheck()
except:
    diskFlag = False
    failure = True
    steps.append('4')
    print(colPrint('WARNING! Minimum space check failed! Please make sure /opt/alation has 8GB free space.','R'))


# ## Data drive and backup drive space and mounting check
try:
    backupToDataRatio,backupDfOutput,storageFlag,mountFlag,dataDfOutput = dataAndBackupDriveCheck()
except:
    storageFlag,mountFlag = False,False
    failure = True
    steps.append('5')
    print(colPrint('WARNING! Could not verify separation of data and backup disk!','R'))


# ## Backup checks
try:
    backupFlag,backupFiles = confirmBackups()
except:
    backupFlag = False
    failure = True
    steps.append('6')
    print(colPrint('WARNING! Could not verify backups!','R'))


# ## CPU and memory info
try:
    memResponse,lscpuOutput = cpuMemData()
except:
    print(colPrint('Could not obtain CPU and memory Information','O'))
    
# ## get linux version information
try:
    vResponse = linuxVersionInfo()
except:
    print(colPrint('Could not obtain Linux version information','O'))

# ## get Alation version history
try:
    avResponse = alationVerHist()
except:
    print(colPrint('Could not obtain Alation version history','O'))

try:
    # parse out version data collected before
    vDataTemp = list(map(lambda x: versionParser(x),versionData))
    keys = list(map(lambda x: x[0],vDataTemp))
    values = list(map(lambda x: x[1],vDataTemp))
    fullLog = dict(zip(keys,values))

    # add previously obtained data
    try:
        fullLog['backupFiles'] = backupFiles
    except:
        pass
    try:
        fullLog['Replication'] = replicationMode
    except:
        pass
    try:
        fullLog['installDirDf'] = installDfOutput
    except:
        pass
    try:
        fullLog['dataDirDf'] = dataDfOutput
    except:
        pass
    try:
        fullLog['backupDirDf'] = backupDfOutput
    except:
        pass
    try:
        fullLog['backupToDataRatio'] = backupToDataRatio
    except:
        pass
    try:
        fullLog['cpuData'] = lscpuOutput
    except:
        pass
    try:
        fullLog['totalMemory'] = memResponse.values()[0]
    except:
        pass
    try:
        fullLog['linuxVersion'] = vResponse
    except:
        pass
    try:
        fullLog['alationVerHist'] = avResponse
    except:
        pass
except:
    fullLog={}

# ## Mongo Check
try:
    mongoFlag,fullLog,availDataSpace,mongoSize = mongoCheck(fullLog)
except:
    mongoFlag = False
    steps.append('8')

# ## postgreSQL Check
try:
    combinedSpaceFlag,pgsqlFlag,fullLog = pgSQLCheck(fullLog)
except:
    combinedSpaceFlag,pgsqlFlag = False,False
    failure = True
    steps.append('10')
    print(colPrint('Caution! Could not verify the space requirements for Alation Analytics!','O'))

# ## Query alation_conf for Datadog check and site_id
try:
    fullLog,datadogFlag = dataDogCheck(fullLog)
except:
    datadogFlag = False
    print(colPrint('Datadog status could not be verified!','O'))

## # Extract site ID
try:
    fullLog,siteID = siteIDExtract(fullLog)
except:
    siteID = 'NA'

# add current time
ts = time.time()
fullLog['creationTime'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')    

hex_log = hex_marker + hexlify(str(fullLog).encode('utf-8')) + hex_marker

# print our the full log
print("Please copy and paste the following data marked by ########## into the Zendesk ticket")
print('##########')
print(hex_log)
print('##########')

message = colPrint("NOTE",'G') + ": Please read information on this link BEFORE upgrading - https://alationhelp.zendesk.com/hc/en-us/articles/360019302454-Update-Safety-Best-Practice"

# create and share a summary
# everything worked
if versionFlag and backupFlag and storageFlag and mountFlag and diskFlag and replicationFlag:
    print(colPrint('All critical checks passed.\nPlease copy and send all the output back to Alation!','G'))
    print('Upgrade Readiness Check complete.')
    print(message)
# now enough storage
elif not diskFlag:
    print(colPrint('Not enough empty space on /opt/alation!','R'))
# backup processing failed
elif not backupFlag:
    print(colPrint('Do not proceed with upgrade. Please check backup!','R'))
elif not replicationFlag:
    print(colPrint('Please follow the High-Availability install instructions here: https://alationhelp.zendesk.com/hc/en-us/articles/115006108927-Upgrade-on-an-HA-Pair-Configuration-4-7-and-above-','O'))
elif not mountFlag or not storageFlag:
    print(colPrint('Backup and data drives share same device!','O'))
if failure:
    print(colPrint('Python failed to verify some information.\nPlease follow manual instruction step 1 + step(s) {} in the readiness guide.'.format(','.join(steps)),'O'))

try:
    # write data to disk
    # data filename
    dfName = "/tmp/dataOutput_{}.json".format(siteID)
    # write to disk
    with open(dfName, "w") as f:
        json.dump(fullLog,f)

except:
    pass