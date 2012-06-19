'''
Created on Jan 4, 2012

@author: penteado
'''
from TPL2_EPICS.TPL2_EPICS import TPL2_EPICS
class TSI_EPICS(TPL2_EPICS):
    '''
    classdocs
    '''
    
    def open(self):
        pass
    
    def isOpen(self):
        return self.isListening()
    
    def close(self):
        self.diconnect()


if __name__ == "__main__":
    print "Ruuning TSI_EPICS.py's main"
    #t=TSI(user='admin',password='a8zfuoad1',host='sim.tt-data.eu',port=65442,echo=False)
    t=TSI_EPICS()
    t
    t.get('SERVER.INFO.DEVICE')
    t.received_objects
    print t.getobject('SERVER.UPTIME')
    t.getobject('POINTING.SETUP.LOCAL.LATITUDE')
    t.set('POINTING.SETUP.LOCAL.LATITUDE',29.78,wait=True)
    t.getobject('POINTING.SETUP.LOCAL.LATITUDE')
    t.log
    
    
