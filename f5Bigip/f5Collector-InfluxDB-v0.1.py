import argparse
import yaml
import subprocess

import f5Bigip as bigip
import f5DBSender

f5Logger = bigip.f5BigipLogger()
f5Logger.logLevel = 'DEBUG'
f5Logger.inizializeF5Logging()

f5Logger.logger.debug("f5Collector job starting")
f5Logger.logger.debug("   Parsing command line arguments and loading YAML configuration file")
parser = argparse.ArgumentParser()
parser.add_argument("configFile", help="Path and Filename of the configuration file for this collector")
parser.parse_args()
args = parser.parse_args()

config_file = open(args.configFile, 'r')
collectorConfig = yaml.load(config_file)
config_file.close()
f5Logger.logger.debug("   ===>> Done")

bigipList = collectorConfig['BIGIP_LIST']
iDBServer = collectorConfig['INFLUXDB_SERVER']
mVariables = collectorConfig['MONITORED_VARIABLES']
mPoolVariables = collectorConfig['MONITORED_POOL_VARIABLES']
getVSStats = collectorConfig['GET_VS_STATS']
getPoolStats = collectorConfig['GET_POOL_STATS']

for bigipBox in bigipList:
    cStatThread = f5DBSender.collectStats_iDB_Thread('%s_thread' % bigipBox['hostname'], bigipBox, mVariables, mPoolVariables)
    cStatThread.iDBServerIP = iDBServer['IP']
    cStatThread.iDBServerIPPort = iDBServer['IPPort']
    cStatThread.iDBServerDB = iDBServer['dbName']
    cStatThread.f5Logger = f5Logger
    cStatThread.getVSStats = getVSStats
    cStatThread.getPoolStats = getPoolStats
    cStatThread.start()
