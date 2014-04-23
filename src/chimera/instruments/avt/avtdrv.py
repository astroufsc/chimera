# ONLY SCRATCH AT THE MOMENT!!!
import socket, struct
import xml.etree.ElementTree as et


class AVTDrv(object):
    ipaddr = '<broadcast>'
    port = 3956
    gvcp_hdr_fmt = '>8B'
    disc_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01)
    bye_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x04, 0x00, 0x00, 0x00, 0x01)
    pkt_resend_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x40, 0x00, 0x00, 0x00, 0x01)
    reg_read_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x80, 0x00, 0x00, 0x00, 0x01)
    reg_write_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x82, 0x00, 0x00, 0x00, 0x01)
    mem_read_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x84, 0x00, 0x00, 0x00, 0x01)
    mem_write_cmd = struct.pack(gvcp_hdr_fmt, 0x42, 0x01, 0x00, 0x86, 0x00, 0x00, 0x00, 0x01)


    def __init__(self):
        #Singleton!?
        pass

    def GvcpDiscover(self):
        """
        Open socket, enable broadcasting, shout for available gigevision cameras,
        see who responds.
        @return: response, address tuple
        """
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.sk.connect((self.ipaddr, self.port))
        self.sk.sendall(self.disc_cmd)
        self.resp, self.addr = self.sk.recvfrom(1024)
        return




    def GvcpGetRegisters(self,dfile):
        """
        Parse camera xml description file, get registers for supported
        features.
        @return: a dict with
        """
        top = et.parse(dfile)
        tree = top.getroot()





# def stripRoot(t, el):
#     return el.tag.lstrip(t.tag + '}')
#
#
