
import Pyro.constants

import sys
import traceback

import logging
import chimera.core.log


def printException (e, stream=sys.stdout):
    print >> stream, ''.join(strException(e))

def strException (e):

    # almost copied form Pyro to allow personalization on format

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

def logException (e):
    logging.getLogger(__name__).debug(printException(e))


# exceptions hierarchy

class ChimeraException (Exception):
    pass

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
