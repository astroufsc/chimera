import struct
import socket


# These data pack defs are taken from the camera's documentation, as of 2014
si_pkt_base = '>IBB'
si_pkt_cmd_ack = si_pkt_base + 'H'
si_pkt_cmd_hdr = si_pkt_base + '2H'
si_pkt_data_hdr = si_pkt_base + 'iHi'
si_pkt_img_hdr = si_pkt_base + 'i4H3iI'


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
        self.cmds = dict(CamStatus=1011, AcqStatus=1017, TermAcq=1018, GetImage=1019, GetImgHdr=1024, SaveImg=1031,
                         SetAcqMode=1034, SetExpTime=1035, SetAcqType=1036, Acquire=1037, NberOfFrames=1039,
                         GetSGLSettings=1041, SetReadoutMode=1042, SetCCDFormat=1043, SetParam=1044,
                         CoolerOnOff=1046, SetSavetoPath=1047, GetCamPars=1048, GetXMLFiles=1060, GetAcqTypes=1061,
                         ResetCam=1063, HardResetCam=1064)

        self.ipaddr = '192.168.0.111'
        self.port = 2055

        try:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.settimeout(10)
            self.sk.connect((self.ipaddr, self.port))
            print('Camera connected at {} on port {}', self.ipaddr,self.port)
        except socket.error, e:
            print('Is the Camera connected? {}', e)
            return

        # try:
        #     self.cfg = os.path.join(SYSTEM_CONFIG_DIRECTORY, 'SICam.cfg')
        # except:
        #     print('Error getting camera configuration file.')

        # Here goes the unavoidable XML parsing routine...Argh!

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
        cmd = struct.pack(si_pkt_cmd_hdr, 10, 128, 0, self.cmds['GetCamPars'], 0)
        self.sk.send(cmd)
        fmt_size = struct.calcsize(si_pkt_cmd_ack)
        nbytes, pkid, camid, flg = struct.unpack(si_pkt_cmd_ack, self.sk.recv(fmt_size))
        print 'Ack: ', nbytes, pkid, camid, flg

        # Get this much data in a buffer
        cp = self.sk.recv(4096)
        cps = struct.calcsize(si_pkt_data_hdr) - len(cp)
        fmt = si_pkt_data_hdr + repr(cps) + 's'
        print fmt
        pl, pid, cid, err, dt, nb, ln  = struct.unpack(fmt, cp)

        return pl, pid, cid, err, dt, nb, ln

    def getSGLIISettings(self):
        """

        @return:
        """
        cmd = struct.pack(si_pkt_cmd_hdr, 10, 128, 0, self.cmds['GetSGLSettings'], 0)
        self.sk.send(cmd)
        fmt_size = struct.calcsize(si_pkt_cmd_ack)
        nbytes, pkid, camid, flg = struct.unpack(si_pkt_cmd_ack, self.sk.recv(fmt_size))
        print('Ack:', nbytes, pkid, camid, flg)

        # Get this much data in a buffer
        cp = self.sk.recv(4096)

        fmt = si_pkt_data_hdr + 'I2B2I2H6i'
        pl, pid, cid, err, dt, nb, exp, nrd, rm, an, fr, am, at, so, sl, sb, po, pl, pb = struct.unpack(fmt, cp)

        return pl, pid, cid, err, dt, nb, exp, nrd, rm, an, fr, am, at, so, sl, sb, po, pl, pb

    #
    # Camera Commands; CANNOT DEBUG UNTIL A CAMERA IS ATTACHED!
    #
    # def getStatus(self):
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
    #     # pkt format, pkt size, pktid, cmid, cmd, len param
    #     cmd = struct.pack(si_pkt_cmd_hdr, 10, 128, 1, self.cmds['CamStatus'], 0)
    #     self.sk.send(cmd)
    #     # somewhere around here there should be a check for remaining content on the socket buffer...
    #     ack = self.sk.recv(struct.calcsize(si_pkt_cmd_ack))
    #     nbytes, pkid, camid, flg = struct.unpack(si_pkt_cmd_ack, ack)
    #
    #     cp = self.sk.recv(4096)
    #
    #     cps = struct.calcsize(si_pkt_data_hdr) - len(cp)
    #     fmt = si_pkt_data_hdr + repr(cps) + 's'
    #     print fmt
    #     pl, pid, cid, err, dt, nb, ln  = struct.unpack(fmt, cp)
    #
    #     return pl, pid, cid, err, dt, nb, ln

    def getCamXMLFiles(self):
        """

        @return:
        """
        cmd = struct.pack(si_pkt_cmd_hdr, 10, 128, 0, self.cmds['GetXMLFiles'], 0)
        self.sk.send(cmd)
        fmt_size = struct.calcsize(si_pkt_cmd_ack)
        nbytes, pkid, camid, flg = struct.unpack(si_pkt_cmd_ack, self.sk.recv(fmt_size))
        print('Ack:', nbytes, pkid, camid, flg)

        # Get this much data in a buffer
        cp = self.sk.recv(4096)
        cps = struct.calcsize(si_pkt_data_hdr) - len(cp)
        fmt = si_pkt_data_hdr + repr(cps) + 's'
        print fmt
        pl, pid, cid, err, dt, nb, ln  = struct.unpack(fmt, cp)

        return pl, pid, cid, err, dt, nb, ln


