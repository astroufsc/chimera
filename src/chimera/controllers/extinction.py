
from chimera.core.chimeraobject import ChimeraObject
from chimera.controllers.autofocus import Target, Mode
from chimera.util.catalogs.landolt import Landolt
from chimera.util.position import Position

class Extinction (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)

    def __main__ (self):

        tel = self.getManager().getProxy("/Telescope/0")
        cam = self.getManager().getProxy("/Camera/0")
        dome = self.getManager().getProxy("/Dome/0")
        autofocus = self.getManager().getProxy("/Autofocus/0")
        verify = self.getManager().getProxy("/PointVerify/0")
        
        landolt = Landolt()
        landolt.useTarget(Position.fromRaDec("00:38:00", "-22:00:00"), radius=45)
        
        landolt.constrainColumns({"Vmag": "<11"})
        
        landolts = landolt.find(limit=3)

        for landolt in landolts:
            
            pos = Position.fromRaDec(landolt["RA"], landolt["DEC"])
            self.log.info("Slewing to %s" % pos)
            tel.slewToRaDec(pos)

            while (tel.isSlewing() or not dome.isSyncWithTel()):
                self.log.info("Waiting dome...")

            self.log.info("Doing autofocus on %s" % pos)
            fit = autofocus.focus(target=Target.CURRENT, mode=Mode.FIT,
                                  exptime=20, start=0, end=7000, step=1000)

            self.log.info("Verifyng pointing...")
            verify.pointVerify()

            cam.expose(exp_time=120, shutter="OPEN",
                       frames=1, filename="extincao-%s" % landolt["ID"].replace(" ", "_"))


	  

