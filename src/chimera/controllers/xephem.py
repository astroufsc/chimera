
from chimera.core.chimeraobject import ChimeraObject
from chimera.util.position import Position

import os
import time
from select import select
    
class XEphem (ChimeraObject):

    __config__ = {"telescope": "/Telescope/0",
                  "fifo_dir": "/usr/local/share/xephem/fifos"}

    def __init__ (self):
        ChimeraObject.__init__ (self)

        self._in_fifo  = None
        self._out_fifo = None

    def __start__ (self):

        self._out_fifo  = os.path.join(self["fifo_dir"], "xephem_in_fifo")
        self._in_fifo = os.path.join(self["fifo_dir"], "xephem_loc_fifo")

        for fifo in [self._in_fifo, self._out_fifo]:
            if not os.path.exists(fifo):
                try:
                    os.mkfifo(fifo, 0666)
                except OSError:
                    self.log.exception("Couldn't create XEphem FIFOs.")
                    raise

    def _getTel(self):
        return self.getManager().getProxy(self["telescope"])

    def _updateSlewPosition (self, position):

        try:
            # force non-blocking open
            fd = os.open(self._out_fifo, os.O_WRONLY|os.O_NONBLOCK)
            out_fifo = os.fdopen(fd, "w")

            mark = "RA:%.3f Dec:%.3f" % (position.ra.R, position.dec.R)
            self.log.debug("Updating sky marker: %s" % mark)

            out_fifo.write(mark)
            out_fifo.flush()
            
        except IOError:
            self.log.exception("Error updating sky marker")
        except OSError, e:
            if e.errno==6: #ENXIO (no such device or address): XEphem closed
                pass
            else:
                self.log.exception("Error updating sky marker")
    
    def __main__ (self):

        tel = self._getTel()
        tel.slewComplete  += self.getProxy()._updateSlewPosition
        tel.abortComplete += self.getProxy()._updateSlewPosition

        self._updateSlewPosition(tel.getPositionRaDec())

        # From man(7) fifo: The FIFO must be opened on both ends
        #(reading and writing) before data can be passed.  Normally,
        #opening the FIFO blocks until the other end is opened also

        # force non-blocking open
        fd = os.open(self._in_fifo, os.O_RDONLY|os.O_NONBLOCK)
        in_fifo = os.fdopen(fd, "r")

        while not self._loop_abort.isSet():
            
            ret = select([in_fifo], [], [], 0)

            # timeout
            if not any(ret):
                time.sleep(1)
                continue

            try:
                edb = in_fifo.readline()

                # writer not connected (XEphem closed)
                if not edb:
                    time.sleep(1)
                    continue
                
                edb = edb.split(",")
                
                ra = edb[2].split("|")[0].strip()
                dec = edb[3].split("|")[0].strip()
            
                target = Position.fromRaDec(ra, dec)
                self.log.info("XEphem FIFO changed: slewing to %s" % target)
                self._getTel().slewToRaDec(target)
            except (ValueError, IndexError):
                self.log.exception("Cannot convert XEphem EDB to Position.")
                continue
            except:
                self.log.exception("Something wrong...")
    
            
        

