
import Pyro.constants

import sys
import traceback

import logging

from chimera.core.compat import *


def printException (e, stream=sys.stdout):

    print >> stream, ''.join(strException(e))

    if hasattr(e, 'cause') and getattr(e, 'cause') != None:
        print >> stream, "Caused by:",
        print >> stream, ''.join(e.cause)

        
def strException (e):

    def formatRemoteTraceback(remote_tb_lines) :
        result=[]
        result.append(" +--- Remote traceback:")
        for line in remote_tb_lines :
            if line.endswith("\n"):
                line=line[:-1]
            lines = line.split("\n")

            for line in lines :
                result.append("\n | ")
                result.append(line)

        result.append("\n +--- End of remote traceback")
        return result

    # almost copied form Pyro to allow personalization on format
    try:
        exc_type, exc_value, exc_tb = sys.exc_info()
        remote_tb = getattr(e, Pyro.constants.TRACEBACK_ATTRIBUTE, None)
        local_tb = traceback.format_exception(exc_type, exc_value, exc_tb)
        
        if remote_tb:
            remote_tb=formatRemoteTraceback(remote_tb)
            return local_tb + remote_tb
        else:
            # hmm. no remote tb info, return just the local tb.
            return local_tb
    finally:
        # clean up cycle to traceback, to allow proper GC
        del exc_type, exc_value, exc_tb


# exceptions hierarchy

class ChimeraException (Exception):

    def __init__ (self, msg="", *args):
        Exception.__init__ (self, msg, *args)

        if not all(sys.exc_info()):
            self.cause = None
        else:
            self.cause = strException(sys.exc_info()[1])


class InvalidLocationException(ChimeraException):
    pass

class ObjectNotFoundException(ChimeraException):
    pass

class NotValidChimeraObjectException(ChimeraException):
    pass

class ChimeraObjectException(ChimeraException):
    pass

class ClassLoaderException (ChimeraException):
    pass

class InstrumentBusyException (ChimeraException):
    pass

class OptionConversionException (ChimeraException):
    pass

class ChimeraValueError (ChimeraException):
    pass
