__author__ = 'shockwaver'

import gnupg
import smtplib
from datetime import datetime
from pytz import timezone
import pytz
from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache
from ConfigParser import SafeConfigParser

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
    def __init__(self, signID, passphrase):
        self.signID = signID
        self.passphrase = passphrase
        self.gpg = gnupg.GPG()

    def encrypt(self, message, recipientEmail):
        encrypted_text = self.gpg.encrypt(message, recipientEmail, sign=self.signID, passphrase=self.passphrase)
        return encrypted_text

    def sign(self, message):
        signed_text = self.gpg.sign(message, keyid=self.signID, passphrase=self.passphrase)
        return signed_text

# read config file in
parser = SafeConfigParser()
parser.read(configFile)
# parse email variables
email = parser.get('email', 'email')
password = parser.get('email', 'password')
server = parser.get('email', 'server')
port = parser.get('email', 'port')

# parse PGP variables
signKey = parser.get('pgp key', 'sign_id')
signPass = parser.get('pgp key', 'sign_pass')
cipher = PGP(signKey, signPass)

recipient = parser.get('recipient', 'recipientEmail')

# get tor relay
torRelay = parser.get('tor', 'torFingerprint')
torManager = Manager(OnionSimpleCache())
tor = torManager.query('details', lookup=torRelay)
relay = tor.relays[0]

# build the message
message = "Tor Relay (%s) Status\r\n" \
    "-----------------------------------\r\n" \
    "Fingerprint: %s\r\n" \
    "Running: %s\r\n" \
    "Hibernating: %s\r\n" \
    "Address: %s\r\n" \
    "Contact: %s\r\n" \
    "Last Restarted: %s\r\n" % (relay.nickname, relay.fingerprint, relay.running, relay.hibernating, relay.dir_address,
                                relay.contact, relay.last_restarted)

# Bandwidth, rates are in Bytes/second so divide 1024 to get KB/s
relayRate = relay.bandwidth[0]
relayBurst = relay.bandwidth[1]
relayObserved = relay.bandwidth[2]
relayAdvertised = relay.bandwidth[3]

# It's possible for these to report None - compensate by setting to 0.00
relayRate = 0.00 if str(relayRate) == "None" else float(relayRate)/1024
relayBurst = 0.00 if str(relayBurst) == "None" else float(relayBurst)/1024
relayObserved = 0.00 if str(relayObserved) == "None" else float(relayObserved)/1024
relayAdvertised = 0.00 if str(relayAdvertised) == "None" else float(relayAdvertised)/1024


message += "\r\n" \
    "Bandwidth:\r\n" \
    "         Rate: %0.2fKB/s\r\n" \
    "        Burst: %0.2fKB/s\r\n" \
    "     Observed: %0.2fKB/s\r\n" \
    "   Advertised: %0.2fKB/s\r\n" % (relayRate, relayBurst, relayObserved, relayAdvertised)

# Convert datetime string to localized CDT
dateFormat = "%Y-%m-%d %H:%M:%S %Z"
dateNow = datetime.now(timezone('US/Central'))
relayUpdatedStr = str(tor.relays_published)
updated_datetime_obj = datetime.strptime(relayUpdatedStr, "%Y-%m-%d %H:%M:%S")
updated_datetime_obj = pytz.utc.localize(updated_datetime_obj)
relayUpdated = timezone('US/Central').normalize(updated_datetime_obj)
message += "\r\n" \
    "Last Updated: %s\r\n" \
    "    Time Now: %s\r\n" % (relayUpdated.strftime(dateFormat), dateNow.strftime(dateFormat))
#print message


# build mail object
mail = Gmail(email, password, server, port)
encrypted_message = cipher.encrypt(message, recipient)
print encrypted_message
mail.send_message(recipient, "Status Updated - %s" % dateNow.strftime("%Y-%m-%d %H:%M"), str(encrypted_message))
