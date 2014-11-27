import struct
import socket


# These data pack defs are taken from the camera's documentation, as of 2014
si_pkt_base = '>I2B'
si_pkt_cmd_ack = si_pkt_base + 'H'
si_pkt_cmd_hdr = si_pkt_base + '2H'
si_pkt_data_hdr = si_pkt_base + 'iHi'
si_pkt_img_hdr = si_pkt_base + 'i4H3iI'

BUFFER = 4096
# Future idea: at module load time, define a namedtuple subclass for each
# data structure?


class SIDrv(object):

    def __init__(self):
        """
        Initialize TBD
        Connect to the camera (IP)
        Grok the camera's config file, whatever that is! Once initialized, the camera is ready
        to accept commands
        @return:
        """
        # They're not all here...
        self.cmds = dict(CamStatus=1011, AcqStatus=1017, TermAcq=1018,
                         GetImage=1019, GetImgHdr=1024, SaveImg=1031,
                         SetAcqMode=1034, SetExpTime=1035, SetAcqType=1036,
                         Acquire=1037, NberOfFrames=1039, GetSGLSettings=1041,
                         SetReadoutMode=1042, SetCCDFormat=1043, SetParam=1044,
                         CoolerOnOff=1046, SetSavetoPath=1047, GetCamPars=1048,
                         GetXMLFiles=1060, GetAcqTypes=1061, ResetCam=1063,
                         HardResetCam=1064)

        self.ipaddr = '192.168.0.111'
        self.port = 2055

        try:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.settimeout(10)
            self.sk.connect((self.ipaddr, self.port))
            print 'Camera connected at {%s} port {%s}', self.ipaddr, self.port
        except socket.error, e:
            print('Is the Camera connected?', e)
            return

        # try:
        #     self.cfg = os.path.join(SYSTEM_CONFIG_DIRECTORY, 'SICam.cfg')
        # except:
        #     print('Error getting camera configuration file.')

        # Here goes the unavoidable XML parsing routine...Argh!

    def _cmdPacket(self, svrcmd, type=0, psl=0):
        """
        Sends a command packet to the camera server, checks for
        integrity of the ack response
        @return: a tuple of:
            - number of bytes in the packet;
            - packet id;
            - camera id (1 if sole camera);
            - flag
        """
        # Build the cmd packet
        cmd = struct.pack(si_pkt_cmd_hdr, 10, 128, type, svrcmd, psl)
        # Send it away!
        self.sk.send(cmd)
        # Get the ack. back
        try:
            resp = self.sk.recv(struct.calcsize(si_pkt_cmd_ack))
        except socket.error, e:
            print(e)
        else:
            ack = struct.unpack(si_pkt_cmd_ack, resp)

        return ack

    def _dataPacket(self, pktfmt):
        """
        Retrieves the data packet from the socket, unpack it via associated
        format and populates results.
        @param pktfmt: struct format for the corresponding data structure
        @return: unpacked tuple
        """
        dp = self.sk.recv(BUFFER)
        fmt = si_pkt_data_hdr + pktfmt
        print 'data fmt:', fmt

        resp = struct.unpack(fmt, dp)

        return resp

    #
    # Server Commands
    #
    def getCameraParams(self):
        """
        Server command;
        Retrieves parameter tables:
          +-------------------------------------+
          | Function number: 1048               |
          | Parameters: none                    |
          | Returns: Data Packet Structure 2010 |
          +-------------------------------------+
        @return:
        """
        ack = self._cmdPacket(self.cmds['GetCamPars'])
        print ack

        cps = struct.calcsize(si_pkt_data_hdr) - ack[0]
        print cps
        cdata = self._dataPacket(repr(cps))
        return 'Params:', cdata

    def getSGLIISettings(self):
        # """
        #
        # @return:
        # """
        ack = self._cmdPacket(self.cmds['GetSGLSettings'])
        print ack

        cdata = self._dataPacket('I2B2I2H6i')
        return 'Data pkt:', cdata

    def getCamXMLFiles(self):

        ack = self._cmdPacket(self.cmds['GetXMLFiles'])
        print ack

        cps = struct.calcsize(si_pkt_data_hdr) - ack[0]
        print cps
        cdata = self._dataPacket(repr(cps))
        return cdata

    #
    # Camera Commands; CANNOT DEBUG UNTIL A CAMERA IS ATTACHED!
    #
    def getCamStatus(self):
    #     """
    #     Camera command;
    #     Retrieves status from the camera:
    #        +------------------------------------+
    #        | Function number: 1011              |
    #        | Parameters: none                   |
    #        | Returns: Data Packet Structure 2012|
    #        +------------------------------------+
    #
    #     @return:
    #     """
        ack = self._cmdPacket(self.cmds['CamStatus'])
        print ack

        cps = struct.calcsize(si_pkt_data_hdr) - ack[0]
        print cps, repr(cps)
        cdata = self._dataPacket(repr(cps) + 's')
        return cdata

    def setAcqMode(self, am):

        ack = self._cmdPacket(self.cmds['SetAcqMode'], type=1, psl=am)
        print ack

        cdata = self._dataPacket('H')
        return cdata

    def setExpTime(self, time):
        # what is DBL? check this time fmt
        ack = self._cmdPacket(self.cmds['SetExpTime'], type=1, psl=time)
        print ack

        cdata = self._dataPacket('H')
        return cdata

    def setAckType(self, at):
        ack = self._cmdPacket(self.cmds['SetAcqType'], type=1, psl=at)
        print ack
        cdata = self._dataPacket('H')
        return cdata
