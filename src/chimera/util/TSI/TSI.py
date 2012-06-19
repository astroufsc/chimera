'''
Created on Jan 4, 2012

@author: penteado
'''
from TPL2.TPL2 import TPL2
class TSI(TPL2):
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
    print "Ruuning TSI.py's main"
    t=TSI(user='admin',password='a8zfuoad1',host='sim.tt-data.eu',port=65442,echo=False)
    t
    t.get('SERVER.INFO.DEVICE')
    t.received_objects
    print t.getobject('SERVER.UPTIME')
    t.getobject('POINTING.SETUP.LOCAL.LATITUDE')
    t.set('POINTING.SETUP.LOCAL.LATITUDE',29.78,wait=True)
    t.getobject('POINTING.SETUP.LOCAL.LATITUDE')
    t.log
    
    