
if __name__ == '__main__':

    from chimera.util.position import Position
    from chimera.controllers.scheduler.model import *

    target = Target(name='NGC 4755', position=Position.fromRaDec(10, 10))
 
    exposure = Science(exptime=3, frames=2, interval=0, filter_="I")

    c1 = MoonDistance(name="moon-distance", min=10, max=20)
    c2 = MoonPhase(name="moon-phase", min=40, max=60)

    obs = Observation(target=target, exposures=[exposure], constraints=[c1])

    p = Program(pi='Paulo Henrique', constraints=[c2], observations=[obs])

    session.flush()
