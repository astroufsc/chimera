import sys
import win32com.client

import servicemanager
from pywintypes import com_error

from socket import *

def _log(str):
#     servicemanager.LogMsg(
#                         servicemanager.EVENTLOG_INFORMATION_TYPE,
#                         servicemanager.PYS_SERVICE_STOPPED,
#                         ("UTS", "%s" % str)
#                         )
    print str
    sys.stdout.flush()

class UTSException(Exception):
    def __init__(self, value):
            self.value = value

    def __str__(self):
        return repr(self.value)

class UTSPointing:

    def __init__(self, port = 10000):
        self.sk = None
        self.port = port

        self.tel = None
        self.util = None

    def start(self, findHome = True):
        try:
            self.tel = win32com.client.Dispatch("TheSky.Telescope")
            self.thesky = win32com.client.Dispatch("TheSky.RASCOMTheSky")
            self.util = win32com.client.Dispatch("DriverHelper.Util")

            self.sk = socket(AF_INET, SOCK_STREAM)
            self.sk.bind((gethostname(), self.port))
            self.sk.listen(5)

            self.tel.Connected = True
            self.thesky.Connect()

            if(findHome):
                self.tel.FindHome()
                            
        except error, e:
            raise UTSException("Erro ao iniciar o servidor (%s)." % (e[1]))

        except AttributeError:
            raise UTSException("Nao foi possivel conectar-se ao telescopio.\n" \
                                "Verifique se o telescopio esta ligado e devidamente conectado ao computador.")
        except com_error, e:
            raise UTSException("Nao foi possivel criar os objetos COM. Contate o administrador." \
                               "(%s)" % str(e))

    def run(self):

        fim = False

        try:

            # connections loop
            while not fim:
                conn, addr = self.sk.accept()
                _log("entrando %s:%s." % addr)

                # data loop
                while 1:
                    data = conn.recv(1024)

                    if not data: continue

                    if data == "BYE":
                        conn.close()
                        break
                    if data in ("SHUTDOWN", "PARK"):
                        conn.close()
                        fim = True
                        break                        
                    else:
                        target = data.split('*')
                        targetRA = target[0]
                        targetDEC = target[1]

                        _log("movendo para %s %s." % (str(targetRA), str(targetDEC)))

                        self.tel.SlewToCoordinates(self.util.HMSToHours(targetRA), self.util.DMSToDegrees(targetDEC))

                        conn.send("OK")
                # end of data loop

                conn.close()
                _log("saindo")
                
            #end of connections loop

        except error, e:
            raise UTSException("%s: %s", e[0],e[1])
        except com_error, e:
            raise UTSException(str(e))

    def stop(self, park = True):
        if(park):
            _log("parking...")
            self.tel.Park()

        _log("closing...")
        self.sk.close()
               
        self.tel.Connected = False
        self.thesky.Quit()

if __name__=='__main__':

    try:
        uts = UTSPointing()
        uts.start()
        uts.run()
        uts.stop()

        sys.exit(-1)

    except (UTSException, KeyboardInterrupt), e:
        uts.stop()
        print e
    
