__author__ = 'shockwaver'

import gnupg
import smtplib
from datetime import datetime
from pytz import timezone
from configparser import SafeConfigParser
from Tor import Tor

configFile = 'config.cfg'

class Gmail(object):
    def __init__(self, email, password, server, port):
        self.email = email
        self.password = password
        self.server = server
        self.port = port
        session = smtplib.SMTP(self.server, self.port)
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.email, self.password)
        self.session = session

    def send_message(self, email, subject, body):
        ''' This must be removed '''
        headers = [
                "From: " + self.email,
                "Subject: " + subject,
                "To: " + email,
                "MIME-Version: 1.0",
                "Content-Type: text/plain"]
        headers = "\r\n".join(headers)
        self.session.sendmail(
                self.email,
                email,
                headers + "\r\n\r\n" + body)

class PGP(object):
    def __init__(self, signID, passphrase, debug):
        self.signID = signID
        self.passphrase = passphrase
        self.gpg = gnupg.GPG(verbose=debug)

    def encrypt(self, message, recipientEmail):
        encrypted_text = self.gpg.encrypt(message, recipientEmail, sign=self.signID, passphrase=self.passphrase)
        return encrypted_text

    def sign(self, message):
        signed_text = self.gpg.sign(message, keyid=self.signID, passphrase=self.passphrase)
        return signed_text


# read config file in
parser = SafeConfigParser()
parser.read(configFile)

# Check for debug flag
DEBUG = False
if parser.has_option('debug', 'debug'):
    DEBUG = parser.getboolean('debug', 'debug')

###############
# GPG Section #
###############

# parse PGP variables
signKey = parser.get('pgp key', 'sign_id')
signPass = parser.get('pgp key', 'sign_pass')
cipher = PGP(signKey, signPass, DEBUG)


# parse email variables
email = parser.get('email', 'email')
password = parser.get('email', 'password')
server = parser.get('email', 'server')
port = parser.get('email', 'port')


recipient = parser.get('recipient', 'recipientEmail')

# get tor relay
torRelay = parser.get('tor', 'torFingerprint')

# Create Tor object
tor = Tor(torRelay)
relay = tor.relay()

dateFormat = "%Y-%m-%d %H:%M:%S %Z"

# build the message
message = "Tor Relay (%s) Status\r\n" \
    "-----------------------------------\r\n" \
    "Fingerprint: %s\r\n" \
    "Running: %s\r\n" \
    "Hibernating: %s\r\n" \
    "Address: %s\r\n" \
    "Contact: %s\r\n" \
    "Last Restarted: %s\r\n" \
    "Uptime: %s\r\n" % (relay.nickname, relay.fingerprint, relay.running, relay.hibernating, relay.dir_address,
                                relay.contact, tor.restartTimeLocal.strftime(dateFormat), tor.getUptime())

if DEBUG:
    print("First Block: \r\n%s\r\n" % message)

flagString = ""
for flag in relay.flags:
    flag = str(flag)
    if flag == "Guard" or flag == "Stable":
        flag = "*" + flag + "*"
    flagString += flag + "\r\n"

message += "\r\nCurrent Flags:\r\n" \
    "%s" % flagString

if DEBUG:
    print("Flag string: %s" % flagString)

bandwidthBlock = "\r\n" \
    "Bandwidth:\r\n" \
    "         Rate: {:>8,.2f} KB/s\r\n" \
    "        Burst: {:>8,.2f} KB/s\r\n" \
    "     Observed: {:>8,.2f} KB/s\r\n" \
    "   Advertised: {:>8,.2f} KB/s\r\n".format(tor.relayRate, tor.relayBurst, tor.relayObserved, tor.relayAdvertised)
bandwidthBlock += "Total Network Bandwidth (est): %0.2fGB/s\r\n" % tor.networkBandwidth

bandwidthBlock += "\r\n" \
    "Read/Write Speeds: \r\n" \
    "     3 Day Avg: %0.2fKB/s, %0.2fKB/s\r\n" \
    "    1 Week Avg: %0.2fKB/s, %0.2fKB/s\r\n" \
    "   1 Month Avg: %0.2fKB/s, %0.2fKB/s\r\n" % (tor.threeDayAvgRead, tor.threeDayAvgWrite, tor.oneWeekAvgRead,
                                                  tor.oneWeekAvgWrite, tor.oneMonthAvgRead, tor.oneMonthAvgWrite)


# Calculate B/KB/MB/GB
KB = 1024
MB = KB*KB
GB = MB*KB
if tor.total_written_bytes > GB or tor.total_read_bytes > GB:
    writtenAmount = tor.total_written_bytes / GB
    readAmount = tor.total_read_bytes / GB
    byteLabel = "GB"
elif tor.total_written_bytes > MB or tor.total_read_bytes > MB:
    writtenAmount = tor.total_written_bytes / MB
    readAmount = tor.total_read_bytes / MB
    byteLabel = "MB"
elif tor.total_written_bytes > KB or tor.total_read_bytes > KB:
    writtenAmount = tor.total_written_bytes / KB
    readAmount = tor.total_read_bytes / KB
    byteLabel = "KB"
else:
    writtenAmount = tor.total_written_bytes
    readAmount = tor.total_read_bytes
    byteLabel = "B"


bandwidthBlock += "Total Data (previous 30 days): \r\n" \
    "   Write: {writtenAmount:>6,.3f} {byteLabel}\r\n" \
    "    Read: {readAmount:>6,.3f} {byteLabel}\r\n".format(writtenAmount=writtenAmount, readAmount=readAmount,
                                                           byteLabel=byteLabel)

if DEBUG:
    print("Bandwidth block: %s" % bandwidthBlock)
message += bandwidthBlock

# Convert datetime string to localized CDT
dateNow = datetime.now(timezone('US/Central'))

message += "\r\n" \
    "Last Updated: %s\r\n" \
    "    Time Now: %s\r\n" % (tor.relayUpdated.strftime(dateFormat), dateNow.strftime(dateFormat))
if DEBUG:
    print("\r\n====================\r\n")
    print("FULL MESSAGE\r\n")
    print("====================\r\n")
    print(message)


encrypted_message = cipher.encrypt(message, recipient)
if DEBUG:
    print("Encrypted message:\r\n")
    print(encrypted_message)

if not DEBUG:
    # build mail object
    mail = Gmail(email, password, server, port)
    mail.send_message(recipient, "Status Updated - %s" % dateNow.strftime("%Y-%m-%d %H:%M"), str(encrypted_message))
