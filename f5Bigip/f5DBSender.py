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

import f5Bigip as bigip
import threading
import time
from influxdb import InfluxDBClient

# ===================================
# Collector Thread Classes Definition
# ===================================

class collectStats_iDB_Thread(threading.Thread):

    iDBServerIP = '127.0.0.1'
    iDBServerDB = ''
    iDBServerIPPort = '8083'
    iDBServerUsername = ''
    iDBServerPassword = ''

    f5Logger = ''

#    getVSStats = true
#    getPoolStats = true
    interval = 10

    def __init__(self, threadName, bigipBox, mVariables, mPoolVariables):
        threading.Thread.__init__(self)
        self.threadName = threadName
        self.bigipBox = bigipBox
        self.mVariables = mVariables
        self.mPoolVariables = mPoolVariables

    def run (self):

        self.f5Logger.logger.info("===>>%s<<=== F5 Collector for iDB - Thread %s starting" % (self.threadName,self.threadName))

        self.f5Logger.logger.debug("===>>%s<<===   Inizialising Rest Connector for Bigip %s" % (self.threadName,self.bigipBox['mgmtIpAddr']))
        bRestConn = bigip.f5RestConnector()
        bRestConn.createF5RestConnector(self.bigipBox['username'], self.bigipBox['password'])

        bPlatform = bigip.bigipPlatform()
        bPlatform.bRestConn = bRestConn
        bPlatform.f5Logger = self.f5Logger
        bPlatform.mgmtIpAddr = self.bigipBox['mgmtIpAddr']
        bPlatform.adminUser = self.bigipBox['username']
        bPlatform.adminPasswd = self.bigipBox['password']

        self.f5Logger.logger.debug("===>>%s<<===   Inizialising Rest Connector for InfluxDB at %s:%s using DB %s" % (self.threadName,self.iDBServerIP,self.iDBServerIPPort,self.iDBServerDB))
        iDBClient = InfluxDBClient(self.iDBServerIP, self.iDBServerIPPort, self.iDBServerUsername, self.iDBServerPassword, self.iDBServerDB)

        self.f5Logger.logger.debug("===>>%s<<===   Getting VS List from bigip" % self.threadName)
        bPlatform.getVSList()
        VSList = bRestConn.restJsonData['items']

        self.f5Logger.logger.debug("===>>%s<<===   Getting Pool List from bigip" % self.threadName)
        bPlatform.getPoolList()
        poolList = bRestConn.restJsonData['items']

        while ( 1 == 1 ):
            if self.getVSStats:
                for VS in VSList:
                    self.f5Logger.logger.debug("===>>%s<<===      Getting Statistics for VS %s" % (self.threadName, VS['name']))
                    bStats = bigip.bigipStats()
                    bStats.bRestConn = bRestConn
                    bStats.f5Logger = self.f5Logger
                    bStats.mgmtIpAddr = self.bigipBox['mgmtIpAddr']
                    bStats.vsName = VS['name']
                    bStats.vsPartition = VS['partition']
                    bStats.vsFullPath = VS['fullPath']
                    bStats.getVSStats()
                    vsStats = bRestConn.restJsonData
                    vsCompleteName = ''

                    fields = {}
                    for sStats in self.mVariables:
                        sStatsName = sStats['variableName']
                        sStatsField = sStats['variableField']
                        sStatsValue = ''
                        if self.bigipBox['mainVersion'] == "12":
                            #vsCompleteName = '~%s~%s' % (bStats.vsPartition, bStats.vsName)
                            vsCompleteName = VS['fullPath'].replace("/","~")
                            vsLink = 'https://localhost/mgmt/tm/ltm/virtual/%s/%s/stats' % (vsCompleteName, vsCompleteName)
                            sStatsValue = vsStats['entries'][vsLink]['nestedStats']['entries'][sStatsName][sStatsField]
                        else:
                            vsCompleteName = VS['name']
                            sStatsValue = vsStats['entries'][sStatsName][sStatsField]

                        self.f5Logger.logger.debug("===>>%s<<===         Adding Statistic value for Virtual Server %s: %s=%s" % (self.threadName, VS['name'], sStatsName, sStatsValue))
                        fields[sStatsName] = sStatsValue
                        self.f5Logger.logger.debug("===>>%s<<===         Done" % self.threadName)

                    self.f5Logger.logger.debug("===>>%s<<===         Sending statistcis to InfluxDBServer" % self.threadName)
                    json_body =[
                        {
                            "measurement" : "virtualServer",
                            "tags" : {
                                "host" : self.bigipBox['hostname'],
                                "VS" : vsCompleteName
                            },
                            "fields" : fields
                        }
                    ]
                    self.f5Logger.logger.debug("===>>%s<<===         json_body is: %s" % (self.threadName,json_body))
                    iDBClient.write_points(json_body)
                    self.f5Logger.logger.debug("===>>%s<<===         Done" % self.threadName)
                    self.f5Logger.logger.debug("===>>%s<<===      Done" % self.threadName)
            else:
                self.f5Logger.logger.debug("===>>%s<<===      Configuration says we should not ask for VS Statistics" % self.threadName)

            if self.getPoolStats:
                for pool in poolList:
                    self.f5Logger.logger.debug("===>>%s<<===      Getting Statistics for Pool %s" % (self.threadName, pool['name']))
                    bStats = bigip.bigipStats()
                    bStats.bRestConn = bRestConn
                    bStats.f5Logger = self.f5Logger
                    bStats.mgmtIpAddr = self.bigipBox['mgmtIpAddr']
                    bStats.poolName = pool['name']
                    bStats.poolPartition = pool['partition']
                    bStats.poolFullPath = pool['fullPath']
                    bStats.getPoolStats()
                    poolStats = bRestConn.restJsonData
                    self.f5Logger.logger.debug("===>>%s<<===         Got poolStats %s" % (self.threadName, poolStats))
                    poolCompleteName = ''

                    fields = {}
                    for sPoolStat in self.mPoolVariables:
                        sPoolStatName = sPoolStat['variableName']
                        sPoolStatField = sPoolStat['variableField']
                        sPoolStatValue = ''
                        if self.bigipBox['mainVersion'] == "12":
                            #poolCompleteName = '~%s~%s' % (bStats.poolPartition, bStats.poolName)
                            poolCompleteName = bStats.poolFullPath.replace("/","~")
                            poolLink = 'https://localhost/mgmt/tm/ltm/pool/%s/%s/stats' % (poolCompleteName, poolCompleteName)
                            self.f5Logger.logger.debug("===>>%s<<===         PoolLink is %s" % (self.threadName, poolLink))
                            sPoolStatValue = poolStats['entries'][poolLink]['nestedStats']['entries'][sPoolStatName][sPoolStatField]
                        else:
                            poolCompleteName = pool['name']
                            sStatsValue = poolStats['entries'][sPoolStatName][sPoolStatField]

                        self.f5Logger.logger.debug("===>>%s<<===         Adding Statistic value for Pool %s: %s=%s" % (self.threadName, pool['name'], sPoolStatName, sPoolStatValue))
                        fields[sPoolStatName] = sPoolStatValue
                        self.f5Logger.logger.debug("===>>%s<<===         Done" % self.threadName)

                    self.f5Logger.logger.debug("===>>%s<<===         Sending statistcis to InfluxDBServer" % self.threadName)
                    json_body =[
                        {
                            "measurement" : "pool",
                            "tags" : {
                                "host" : self.bigipBox['hostname'],
                                "pool" : poolCompleteName
                            },
                            "fields" : fields
                        }
                    ]
                    self.f5Logger.logger.debug("===>>%s<<===         json_body is: %s" % (self.threadName,json_body))
                    iDBClient.write_points(json_body)
                    self.f5Logger.logger.debug("===>>%s<<===         Done" % self.threadName)
                    self.f5Logger.logger.debug("===>>%s<<===      Done" % self.threadName)
            else:
                self.f5Logger.logger.debug("===>>%s<<===      Configuration says we should not ask for Pool Statistics" % self.threadName)

            self.f5Logger.logger.debug("===>>%s<<===      Sleeping %i" % (self.threadName,self.interval))
            time.sleep(self.interval)
