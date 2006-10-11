import threading
import logging
import time

from uts.core.driver import Driver

class Meade(Driver):

    def __init__(self, manager):
        Driver.__init__(self, manager)
        logging.info("Meade init")

        self.slewing = False
        self.abortEvent = threading.Event()

    def init(self, config):
        pass    

    def isSlewing(self):
        logging.info("Meade isSlewing")

        return self.slewing

    def slewToRaDec(self, ra, dec):

        # verifica estado
        if self.slewing:
            logging.info("Meade busy")
            return "ocupado. esta mensagem deve chegar ao objeto que originou o pedido"

        # transicao de estado
        self.slewing = True

        # verifica conexao com telescopio
        logging.info("Meade pinging telescope...")
        time.sleep(1)
        
        # manda apontar
        logging.info("Meade slewing to...")
        time.sleep(1)

        # checa erros

        dummy = 5
        while dummy > 0:

            if self.abortEvent.isSet():
                logging.info("Meade slew aborting")
                self.abortEvent.clear()
                return "aborted"

            # acompanha o movimento
            logging.info("Meade waiting to reach target position...")
            time.sleep(1)
            # publica posicao atual
            #self.currentPosition(position)
            dummy -= 1

        # aguarda estabilizar... etc..

        self.slewing = False

        return "ok, chegou na posicao x"

    def abortSlew(self):
        if not self.slewing:
            return True

        self.abortEvent.set()

        # manda parar
        time.sleep(1)

        return True

    def getRa(self):
        
        # low-level getRa
        logging.info("Meade getting RA")
        return 10

    def getDec(self):
        return 100000
                         

