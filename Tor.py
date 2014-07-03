__author__ = 'taylorc8'

from pytz import timezone
import pytz
from datetime import datetime
from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache

class Tor(object):
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        self.torManager = Manager(OnionSimpleCache())
        self.tor = self.torManager.query('details', lookup=self.fingerprint)
        self.bandwidth = self.torManager.query('bandwidth', lookup=self.fingerprint).relays[0]
        self.time_format = "%Y-%m-%d %H:%M:%S"
        self.tz = timezone('US/Central')
        self.restartTime = self.tor.relays[0].last_restarted
        self.restartTimeLocal = self.convertToLocal(self.restartTime)
        self.getBandwidth()
        self.lastUpdated()
        self.getReadSpeed()
        self.getWriteSpeed()

    def relay(self):
        return self.tor.relays[0]

    def getBandwidth(self):
        # Bandwidth, rates are in Bytes/second so divide 1024 to get KB/s
        relayRate = self.relay().bandwidth[0]
        relayBurst = self.relay().bandwidth[1]
        relayObserved = self.relay().bandwidth[2]
        relayAdvertised = self.relay().bandwidth[3]

        # It's possible for these to report None - compensate by setting to 0.00
        self.relayRate = 0.00 if str(relayRate) == "None" else float(relayRate)/1024
        self.relayBurst = 0.00 if str(relayBurst) == "None" else float(relayBurst)/1024
        self.relayObserved = 0.00 if str(relayObserved) == "None" else float(relayObserved)/1024
        self.relayAdvertised = 0.00 if str(relayAdvertised) == "None" else float(relayAdvertised)/1024

    def convertToLocal(self, timestamp):
        time = datetime.strptime(timestamp, self.time_format)
        # set time as being UTC
        time = pytz.utc.localize(time)
        # localize to self.tz
        time = self.tz.normalize(time)
        return time

    # return uptime string X days, hours, minutes
    def getUptime(self):
        dateNow = datetime.now(timezone('US/Central'))
        uptime = dateNow - self.restartTimeLocal
        return str(uptime)

    def getWriteSpeed(self):
        writeSpeeds = self.bandwidth.write_history

        threeDayAvg = 0
        oneWeekAvg = 0
        oneMonthAvg = 0

        # Three Days
        for value in writeSpeeds['3_days'].values:
            value = 0.0 if str(value) == "None" else value
            threeDayAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.threeDayAvgWrite = (threeDayAvg * writeSpeeds['3_days'].factor) / writeSpeeds['3_days'].count / 1024

        # One Week
        for value in writeSpeeds['1_week'].values:
            value = 0.0 if str(value) == "None" else value
            oneWeekAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneWeekAvgWrite = (oneWeekAvg * writeSpeeds['1_week'].factor) / writeSpeeds['1_week'].count / 1024

        # One Month
        for value in writeSpeeds['1_month'].values:
            value = 0.0 if str(value) == "None" else value
            oneMonthAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneMonthAvgWrite = (oneMonthAvg * writeSpeeds['1_month'].factor) / writeSpeeds['1_month'].count / 1024

    def getReadSpeed(self):
        readSpeeds = self.bandwidth.read_history

        threeDayAvg = 0
        oneWeekAvg = 0
        oneMonthAvg = 0

        # Three Days
        for value in readSpeeds['3_days'].values:
            value = 0.0 if str(value) == "None" else value
            threeDayAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.threeDayAvgRead = (threeDayAvg * readSpeeds['3_days'].factor) / readSpeeds['3_days'].count / 1024

        # One Week
        for value in readSpeeds['1_week'].values:
            value = 0.0 if str(value) == "None" else value
            oneWeekAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneWeekAvgRead = (oneWeekAvg * readSpeeds['1_week'].factor) / readSpeeds['1_week'].count / 1024

        # One Month
        for value in readSpeeds['1_month'].values:
            value = 0.0 if str(value) == "None" else value
            oneMonthAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneMonthAvgRead = (oneMonthAvg * readSpeeds['1_month'].factor) / readSpeeds['1_month'].count / 1024

    def lastUpdated(self):
        relayUpdatedStr = str(self.tor.relays_published)
        updated_datetime_obj = datetime.strptime(relayUpdatedStr, self.time_format)
        updated_datetime_obj = pytz.utc.localize(updated_datetime_obj)
        self.relayUpdated = self.tz.normalize(updated_datetime_obj)
