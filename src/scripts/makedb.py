from elixir import *

from chimera.controllers.scheduler.model import *

if __name__ == '__main__':

    
    from chimera.util.position import Position
#    from chimera.controllers.scheduler.model import *
#
#    target = Target(name='NGC 4755', position=Position.fromRaDec(10, 10))
    
    exposures = [
                 Exposure(shutterOpen = True, filter='CLEAR', frames=20, duration=1, binX=1, binY=1, imageType='flat'),
                 Exposure(shutterOpen = True, filter='CLEAR', frames=20, duration=2, binX=1, binY=1, imageType='flat'),
                 Exposure(shutterOpen = True, filter='CLEAR', frames=20, duration=3, binX=1, binY=1, imageType='flat'),

                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=0, binX=1, binY=1, imageType='zero'),
                 
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=5, binX=1, binY=1, imageType='dark'),
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=10, binX=1, binY=1, imageType='dark'),
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=15, binX=1, binY=1, imageType='dark'),
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=20, binX=1, binY=1, imageType='dark'),
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=30, binX=1, binY=1, imageType='dark'),
                 Exposure(shutterOpen = False, filter='CLEAR', frames=20, duration=60, binX=1, binY=1, imageType='dark'),
                 ]
    
    obs = Observation(caption = 'Calibration', targetName='Calibration', targetPos=Position.fromRaDec('21:34:05.49', '-84:46:12.83'), exposures=exposures)
    
    p = Program(pi='Isaac Richter', observations=[obs], caption='Calibration')
    session.flush()
    
    exposures = [
                 Exposure(filter='R', frames=5, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='G', frames=5, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='B', frames=5, duration=5, binX=1, binY=1, constraints=[]),
                 Exposure(filter='CLEAR', frames=5, duration=5, binX=1, binY=1, constraints=[])
                 ]
    
    obs = Observation(caption='Test Observation', targetPos=Position.fromRaDec('12:54:07', '-60:24:29'), targetName='Jewel Box', exposures=exposures)
    session.flush()
    
    p = Program(pi='Antonio Kanaan', observations=[obs])    
    session.flush()
