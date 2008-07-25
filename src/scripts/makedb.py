from elixir import *

from chimera.controllers.schedulerng.model import *

if __name__ == '__main__':

    
    from chimera.util.position import Position
#    from chimera.controllers.scheduler.model import *
#
#    target = Target(name='NGC 4755', position=Position.fromRaDec(10, 10))
    exposures = [
                 Exposure(filter='R', frames=1, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='G', frames=1, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='B', frames=1, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='CLEAR', frames=1, duration=5, binX=1, binY=1, constraints=[])
                 ]
    session.flush()
    
    obs = Observation(caption=u'Test Observation', targetPos=Position.fromRaDec('12:54:07', '-60:24:29'), exposures=exposures)
    session.flush()
    
    p = Program(pi=u'Isaac Richter', observations=[obs])    
    session.flush()
# 
#    exposure = Science(exptime=3, frames=2, interval=0, filter_="I")
#
#    c1 = MoonDistance(name="moon-distance", min=10, max=20)
#    c2 = MoonPhase(name="moon-phase", min=40, max=60)
#
#    obs = Observation(target=target, exposures=[exposure], constraints=[c1])
#
#    p = Program(pi='Paulo Henrique', constraints=[c2], observations=[obs])
#    q = Program(pi='Observer Tester')
#
#    session.flush()
