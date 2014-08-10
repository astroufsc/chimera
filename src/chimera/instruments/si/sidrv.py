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

# Data Packet Structures
# Known formats:
dps_acqstat_struct_2004 = '2HI'
dps_cmddone_struct_2007 = 'H'
dps_sgl2img_struct_2008 = 'I2B2I2H6i'
# Unknown data lengths:
dps_bytearr_struct_2003 = 'B'
dps_imghdr_struct_2006 = 's'
dps_campars_struct_2010 = 's'
dps_camxml_struct_2011 = 's'
dps_camstat_struct_2012 = 's'
dps_imgacq_struct_2013 = 's'



class SIDrv(object):

    def __init__(self):
        """
        Initialize TBD
        Connect to the camera (IP)
        Grok the camera's config file, whatever that is! Once initialized,
        the camera is ready to accept commands
        @return:
        """
        # They're not all here...
        self.cmds = dict(
            CamStatus=1011, AcqStatus=1017, TermAcq=1018, GetImage=1019,
            GetImgHdr=1024, SaveImg=1031, SetAcqMode=1034, SetExpTime=1035,
            SetAcqType=1036, Acquire=1037, NberOfFrames=1039,
            GetSGLSettings=1041, SetReadoutMode=1042, SetCCDFormat=1043,
            SetParam=1044, CoolerOnOff=1046, SetSavetoPath=1047,
            GetCamPars=1048, GetXMLFiles=1060, GetAcqTypes=1061,
            ResetCam=1063, HardResetCam=1064)

        self.ipaddr = '192.168.0.116'
        self.port = 2055

        try:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.settimeout(10)
            self.sk.connect((self.ipaddr, self.port))
            print 'Camera at {%s}:{%s}', self.ipaddr, self.port
        except socket.error, e:
            print('Is the Camera connected?', e)
            return

        # try:
        #     self.cfg = os.path.join(SYSTEM_CONFIG_DIRECTORY, 'SICam.cfg')
        # except:
        #     print('Error getting camera configuration file.')


    def _cmd_packet(self, svrcmd, type=0, psl=0):
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

    def _data_packet(self, pktfmt):
        """
        Retrieves the data packet from the socket, unpack it via associated
        format and populates results.
        NOTE: packets with data of unknown length must be handled here!
        @param pktfmt: struct format for the corresponding data structure
        @return: unpacked tuple
        """
        self.dp = self.sk.recv(BUFFER)
        # How we distinguish known from unknown format lengths:
        # if len(dp) - struct.calcsize(fmt) == 0, no trailing data!
        if struct.calcsize(pktfmt) != 1:
            trail = len(self.dp) - struct.calcsize(si_pkt_data_hdr + pktfmt)
        else:
            trail = len(self.dp) - struct.calcsize(si_pkt_data_hdr)
        print trail
        if trail == 0:
            fmt = si_pkt_data_hdr + pktfmt
        else:
            fmt = si_pkt_data_hdr + repr(trail) + pktfmt
        print 'data fmt:', fmt
        resp = struct.unpack(fmt, self.dp)
        return resp

    #
    # Server Commands
    #
    def get_camera_params(self):
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
        ack = self._cmd_packet(self.cmds['GetCamPars'])
        print ack

        cps = struct.calcsize(si_pkt_data_hdr) - ack[0]
        print cps
        cdata = self._data_packet(repr(cps))
        return 'Params:', cdata

    def get_SGLII_settings(self):
        # """
        #
        # @return:
        # """
        ack = self._cmd_packet(self.cmds['GetSGLSettings'])
        print ack

        cdata = self._data_packet(dps_sgl2img_struct_2008)
        return 'Data pkt:', cdata

    def get_cam_XMLfiles(self):
        """

        @return:
        """
        ack = self._cmd_packet(self.cmds['GetXMLFiles'])
        print ack

        cdata = self._data_packet(repr(cps))
        return cdata

    def get_acq_types(self):
        ack = self._cmd_packet(self.cmds['GetAcqTypes'])
        print ack

        cdata = self._data_packet(dps_imgacq_struct_2013)
        return 'Params:', cdata

    #
    # Camera Commands; CANNOT DEBUG UNTIL A CAMERA IS ATTACHED!
    #
    def get_cam_status(self):
        """
        Camera command;
        Retrieves status from the camera:
           +------------------------------------+
           | Function number: 1011              |
           | Parameters: none                   |
           | Returns: Data Packet Structure 2012|
           +------------------------------------+

        @return:
        """
        ack = self._cmd_packet(self.cmds['CamStatus'])
        print ack

        cps = struct.calcsize(si_pkt_data_hdr) - ack[0]
        print cps, repr(cps)
        cdata = self._data_packet(repr(cps) + 's')
        return cdata

    def set_acq_mode(self, am):
        """

        @return:
        """
        ack = self._cmd_packet(self.cmds['SetAcqMode'], type=1, psl=am)
        print ack

        cdata = self._data_packet('H')
        return cdata

    def set_exp_time(self, time):
        # what is DBL? check this time fmt
        ack = self._cmd_packet(self.cmds['SetExpTime'], type=1, psl=time)
        print ack

        cdata = self._data_packet('H')
        return cdata

    def set_acq_type(self, at):
        ack = self._cmd_packet(self.cmds['SetAcqType'], type=1, psl=at)
        print ack
        cdata = self._data_packet('H')
        return cdata

    def abort_exposure(self):
        # This cmd does not return an ack.
        self._cmd_packet(self.cmds['TermAcq'], type=1, psl=0)

        cdata = self._data_packet('H')
        return cdata

    def set_cam_parameter(self, param, val):

        self._cmd_packet(self.cmds['SetParam'], type=1)

