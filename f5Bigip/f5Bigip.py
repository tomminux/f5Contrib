# =============================================================================
#
# Module name:  f5Bigip.py
# Version:      v0.1
# Date:         2016-01-28
#
# Author:       Paolo Arcagni
#               p.arcagni@f5.com
#
# Description:
#
# =============================================================================

import requests
import json
import time
import logging
import logging.handlers
import time

class f5BigipLogger:

    logLevel = 'WARNING'
    logFileName = 'f5Bigip.log'

    def inizializeF5Logging ( self ):
        if self.logLevel == 'DEBUG':
            logging.basicConfig(level=logging.DEBUG)
        elif self.logLevel == 'INFO':
            logging.basicConfig(level=logging.INFO)
        elif self.logLevel == 'WARNING':
            logging.basicConfig(level=logging.INFO)
        elif self.logLevel == 'ERROR':
            logging.basicConfig(level=logging.INFO)
        elif self.logLevel == 'CRITICAL':
            logging.basicConfig(level=logging.INFO)
        else:
            print "Wrong log level \"%s\" declared" % self.logLevel
            exit()

        self.logger = logging.getLogger('f5Bigip')
        self.handler = logging.handlers.RotatingFileHandler(
              self.logFileName, maxBytes=1000000, backupCount=5)
        self.logger.addHandler(self.handler)

class f5RestConnector:

    f5Logger = ''

    restStatusCode = ''
    restRawResponse = ''
    restJsonData = {}

    def createF5RestConnector ( self, user, passwd ):
        self.rConnection = requests.session()
        self.rConnection.auth = (user, passwd)
        self.rConnection.verify = False
        self.rConnection.headers.update({'Content-Type' : 'application/json'})

    def setRESTResponseStatus( self, restR ):
        self.restStatusCode = restR.status_code
        self.restRawResponse = restR.text
        self.restJsonData = json.loads(restR.text)

class bigipPlatform:

    bRestConn = ''
    f5Logger = ''

    mgmtIpAddr = '192.168.1.245'
    adminUser = 'admin'
    adminPasswd = 'admin'
    restResource = ''
    baseRegKey = ''

    ntpServers = ''
    dnsServers = ''

    hostname = 'bigip.local'
    timezone = 'Europe/Rome'

    UIRecordPerScreen = '100'
    UIIdleTimeout = '86400'

    newAdminPassword = 'admin'

    vlanName = ''
    vlanTag = 'untagged'
    vlanIface = ''

    selfIPName = ''
    selfIPAdress = ''
    selfIPVlan = ''
    selfIPAllowService = 'none'
    selfIPTrafficGroup = 'traffic-group-local-only'

    TMOSRouteGW = ''
    TMOSRouteName = ''
    TMOSRouteNetwork = ''
    TMOSRoutePartition = 'Common'

    def saveConfig ( self ):
        payload ={}
        payload['command'] = 'save'
        r = self.bRestConn.rConnection.post('https://%s/mgmt/tm/sys/config' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 5 seconds")
        time.sleep(5)
        self.bRestConn.setRESTResponseStatus ( r )

    def installLicense ( self ):
        payload = {}
        payload['command'] = 'install'
        payload['registrationKey'] = self.baseRegKey
        r = self.bRestConn.rConnection.post('https://%s/mgmt/tm/sys/license' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 60 seconds")
        time.sleep(60)
        self.bRestConn.setRESTResponseStatus ( r )

    def setHostname ( self ):
        payload ={}
        payload['value'] = '%s' % self.hostname
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/db/hostname' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def disableSetupGUI ( self ):
        payload ={}
        payload['value'] = 'false'
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/db/setup.run' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def setUIRecordPerScreen ( self ):
        payload ={}
        payload['value'] = self.UIRecordPerScreen
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/db/ui.system.preferences.recordsperscreen' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def setUIIdleTimeout ( self ):
        payload ={}
        payload['authPamIdleTimeout'] = self.UIIdleTimeout
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/httpd' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def setNTPServers ( self ):
        payload ={}
        payload['timezone'] = self.timezone
        payload['servers'] = self.ntpServers
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/ntp' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def setDNSServers ( self ):
        payload ={}
        payload['description'] = 'Configured by iControl REST'
        payload['nameServers'] = self.dnsServers
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/sys/dns' % self.mgmtIpAddr, data=json.dumps(payload))
        self.f5Logger.logger.debug("      Sleeping 2 seconds")
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def modifyAdminPasswowd ( self ):
        payload = {}
        payload['password'] = self.newAdminPassword
        r = self.bRestConn.rConnection.patch('https://%s/mgmt/tm/auth/user/admin' % self.mgmtIpAddr, data=json.dumps(payload))
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def createVLAN ( self, payload ):
        r = self.bRestConn.rConnection.post('https://%s/mgmt/tm/net/vlan' % self.mgmtIpAddr, data=json.dumps(payload))
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def createSelfIP ( self, payload ):
        r = self.bRestConn.rConnection.post('https://%s/mgmt/tm/net/self' % self.mgmtIpAddr, data=json.dumps(payload))
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def createTMOSRoute ( self, payload ):
        r = self.bRestConn.rConnection.post('https://%s/mgmt/tm/net/route' % self.mgmtIpAddr, data=json.dumps(payload))
        time.sleep(2)
        self.bRestConn.setRESTResponseStatus ( r )

    def getVSList ( self ):
        payload ={}
        r = self.bRestConn.rConnection.get('https://%s/mgmt/tm/ltm/virtual' % self.mgmtIpAddr)
        self.bRestConn.setRESTResponseStatus ( r )

    def getPoolList ( self ):
        payload ={}
        r = self.bRestConn.rConnection.get('https://%s/mgmt/tm/ltm/pool' % self.mgmtIpAddr)
        self.bRestConn.setRESTResponseStatus ( r )


class bigipStats:

    bRestConn = ''
    f5Logger = ''

    mainVersion = '12'

    mgmtIpAddr = '192.168.1.245 '
    restResource = ''

    vsName = ''
    vsPartition = 'Common'
    vsFullPath = ''
    poolName = ''
    poolPartition = ''
    poolFullPath = ''

    def getVSStats ( self ):
        payload ={}
        #r = self.bRestConn.rConnection.get('https://%s/mgmt/tm/ltm/virtual/~%s~%s/stats/' % (self.mgmtIpAddr,self.vsPartition,self.vsName))
        r = self.bRestConn.rConnection.get('https://%s/mgmt/tm/ltm/virtual/%s/stats/' % (self.mgmtIpAddr,self.vsFullPath.replace("/","~")))
        self.bRestConn.setRESTResponseStatus ( r )

    def getPoolStats ( self ):
        payload ={}
        #self.f5Logger.logger.debug("      https://%s/mgmt/tm/ltm/virtual/%s/stats/" % (self.mgmtIpAddr,self.vsName))
        r = self.bRestConn.rConnection.get('https://%s/mgmt/tm/ltm/pool/%s/stats/' % (self.mgmtIpAddr,self.poolFullPath.replace("/","~")))
        self.bRestConn.setRESTResponseStatus ( r )
