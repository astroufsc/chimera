import serial

class Meade(object):

    def __init__(self):
	self.tty = None

    def open(self, device):
	self.tty = serial.Serial()
	self.tty.port = device

	try:
		self.tty.open()
	except IOError,e:
		self.setEtror(e)
		return False

	return True

    def close(self):
	if self.tty.isOpen():
		self.tty.close()
		return True
	else:
		self.setError(-1, "Device not open")
		return False

    def slewToRaDec(self, ra, dec):
	pass

    def slewToAltAz(self, alt, az):
        pass

    def abortSlew(self):
	pass

    def moveEast(self, duration):
	pass

    def moveWest(self, duration):
	pass

    def moveNorth(self, duration):
	pass

    def moveSouth(self, duration):
	pass

    def getRa(self):
	pass

    def getDec(self):
	pass

    def getAz(self):
	pass

    def getAz(self):
	pass

    # low-level 

    def _read(self, n = 1):
	if not self.tty.isOpen():
		self.setError(-1, "Device not open")
		return ""
	
	return self.tty.read(n)

    def _readline(self, n = 1, eol='#'):
	if not self.tty.isOpen():
		self.setError(-1, "Device not open")
		return ""
	
	return self.tty.readline(n, eol)

    def _write(self, data):
	if not self.tty.isOpen():
		self.setError(-1, "Device not open")
		return ""

	return self.tty.write(data)

