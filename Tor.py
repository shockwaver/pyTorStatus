__author__ = 'taylorc8'

from pytz import timezone
import pytz
from datetime import datetime
from datetime import timedelta
from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache

class Tor(object):
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        self.byteConversion = 1000
        self.torManager = Manager(OnionSimpleCache())
        self.tor = self.torManager.query('details', lookup=self.fingerprint)
        self.bandwidth = self.torManager.query('bandwidth', lookup=self.fingerprint).relays[0]
        self.time_format = "%Y-%m-%d %H:%M:%S"
        self.tz = timezone('US/Central')
        self.restartTime = self.tor.relays[0].last_restarted
        self.restartTimeLocal = self.convertToLocal(self.restartTime)
        self.getBandwidthSpeeds()
        self.lastUpdated()
        self.getReadSpeed()
        self.getWriteSpeed()
        self.getNetworkBandwidth()
        self.getBandwidthTotals()

    def relay(self):
        return self.tor.relays[0]

    def getBandwidthTotals(self):
        write_histories = self.bandwidth.write_history
        total_written_bytes = 0

        max_written_bytes_relay = 0
        for x, write_history in write_histories.items():
            total = 0
            current = datetime.strptime(write_history.first,
                                        '%Y-%m-%d %H:%M:%S')
            interval = timedelta(seconds=write_history.interval)
            for val in write_history.values:
                if str(val) == "None":
                    val = 0
                total = total + val
                current = current + interval
            total = int(total * write_history.interval * write_history.factor)
            if total > max_written_bytes_relay:
                max_written_bytes_relay = total

        self.total_written_bytes = max_written_bytes_relay

        read_histories = self.bandwidth.read_history
        total_read_bytes = 0

        max_read_bytes_relay = 0
        for x, read_history in read_histories.items():
            total = 0
            current = datetime.strptime(read_history.first,
                                        '%Y-%m-%d %H:%M:%S')
            interval = timedelta(seconds=read_history.interval)
            for val in read_history.values:
                if str(val) == "None":
                    val = 0
                total = total + val
                current = current + interval
            total = int(total * read_history.interval * read_history.factor)
            if total > max_read_bytes_relay:
                max_read_bytes_relay = total
        self.total_read_bytes = max_read_bytes_relay

    def getBandwidthSpeeds(self):
        # Bandwidth, rates are in Bytes/second so divide self.byteConversion to get KB/s
        relayRate = self.relay().bandwidth[0]
        relayBurst = self.relay().bandwidth[1]
        relayObserved = self.relay().bandwidth[2]
        relayAdvertised = self.relay().bandwidth[3]

        # It's possible for these to report None - compensate by setting to 0.00
        self.relayRate = 0.00 if str(relayRate) == "None" else float(relayRate)/self.byteConversion
        self.relayBurst = 0.00 if str(relayBurst) == "None" else float(relayBurst)/self.byteConversion
        self.relayObserved = 0.00 if str(relayObserved) == "None" else float(relayObserved)/self.byteConversion
        self.relayAdvertised = 0.00 if str(relayAdvertised) == "None" else float(relayAdvertised)/self.byteConversion

    # Set the network total bandwidth based on bandwidth_fraction calculation
    def getNetworkBandwidth(self):
        bandFrac = self.relay().advertised_bandwidth_fraction

        # KBytes per second
        networkBandwidth = self.relayAdvertised / bandFrac

        # GBytes per second
        self.networkBandwidth = networkBandwidth / self.byteConversion / self.byteConversion

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
        self.threeDayAvgWrite = (threeDayAvg * writeSpeeds['3_days'].factor) / writeSpeeds['3_days'].count / self.byteConversion

        # One Week
        for value in writeSpeeds['1_week'].values:
            value = 0.0 if str(value) == "None" else value
            oneWeekAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneWeekAvgWrite = (oneWeekAvg * writeSpeeds['1_week'].factor) / writeSpeeds['1_week'].count / self.byteConversion

        # One Month
        for value in writeSpeeds['1_month'].values:
            value = 0.0 if str(value) == "None" else value
            oneMonthAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneMonthAvgWrite = (oneMonthAvg * writeSpeeds['1_month'].factor) / writeSpeeds['1_month'].count / self.byteConversion

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
        self.threeDayAvgRead = (threeDayAvg * readSpeeds['3_days'].factor) / readSpeeds['3_days'].count / self.byteConversion

        # One Week
        for value in readSpeeds['1_week'].values:
            value = 0.0 if str(value) == "None" else value
            oneWeekAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneWeekAvgRead = (oneWeekAvg * readSpeeds['1_week'].factor) / readSpeeds['1_week'].count / self.byteConversion

        # One Month
        for value in readSpeeds['1_month'].values:
            value = 0.0 if str(value) == "None" else value
            oneMonthAvg += value
        # avg speed by adding all values, multiplying by the factor and dividing by count
        self.oneMonthAvgRead = (oneMonthAvg * readSpeeds['1_month'].factor) / readSpeeds['1_month'].count / self.byteConversion

    def lastUpdated(self):
        relayUpdatedStr = str(self.tor.relays_published)
        updated_datetime_obj = datetime.strptime(relayUpdatedStr, self.time_format)
        updated_datetime_obj = pytz.utc.localize(updated_datetime_obj)
        self.relayUpdated = self.tz.normalize(updated_datetime_obj)
