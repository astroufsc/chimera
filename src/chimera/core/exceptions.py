import traceback
import sys
from chimera.core.constants import TRACEBACK_ATTRIBUTE


def printException(e, stream=sys.stdout):

    print("".join(_strException(e)), file=stream)

    if hasattr(e, "cause") and getattr(e, "cause") is not None:
        print("Caused by:", end=" ", file=stream)
        print("".join(e.cause), file=stream)


def _strException(e):

    def formatRemoteTraceback(remote_tb_lines):
        result = []
        result.append(" +--- Remote traceback:")
        for line in remote_tb_lines:
            if line.endswith("\n"):
                line = line[:-1]
            lines = line.split("\n")

            for line in lines:
                result.append("\n | ")
                result.append(line)

        result.append("\n +--- End of remote traceback")
        return result

    try:
        exc_type, exc_value, exc_tb = sys.exc_info()
        remote_tb = getattr(e, TRACEBACK_ATTRIBUTE, None)
        local_tb = traceback.format_exception(exc_type, exc_value, exc_tb)

        if remote_tb:
            remote_tb = formatRemoteTraceback(remote_tb)
            return local_tb + remote_tb
        else:
            # hmm. no remote tb info, return just the local tb.
            return local_tb
    finally:
        # clean up cycle to traceback, to allow proper GC
        del exc_type, exc_value, exc_tb


# exceptions hierarchy


class ChimeraException(Exception):

    def __init__(self, msg="", *args):
        Exception.__init__(self, msg, *args)

        if not all(sys.exc_info()):
            self.cause = None
        else:
            # self.cause = strException(sys.exc_info()[1])
            # FIXME: remote exception handling
            self.cause = None


class InvalidLocationException(ChimeraException):
    pass


class ObjectNotFoundException(ChimeraException):
    pass


class NotValidChimeraObjectException(ChimeraException):
    pass


class ChimeraObjectException(ChimeraException):
    pass


class ClassLoaderException(ChimeraException):
    pass


class OptionConversionException(ChimeraException):
    pass


class ChimeraValueError(ChimeraException):
    pass


class CantPointScopeException(ChimeraException):
    """
    This exception is raised when we cannot center the scope on a field
    It may happen if there is something funny with our fields like:
    faint objects, bright objects, extended objects
    or non-astronomical problems like:
    clouds, mount misalignment, dust cover, etc
    When this happens one can simply go on and observe or ask for a checkPoint
    if checkPoint succeeds then the problem is astronomical
    if checkPoint fails then the problem is non-astronomical
    """


class CanSetScopeButNotThisField(ChimeraException):
    pass


class CantSetScopeException(ChimeraException):
    """
    This exception is raised to indicate we could not set the telescope
    coordinates when trying to do it on a chosen field.
    Chosen fields are those known to work for setting the scope.
    So, if it fails we must have some serious problem.
    Might be clouds, might be mount misalignment, dust cover, etc, etc
    Never raise this exception for a science field. It may be that pointverify
    fails there because of bright objects or other more astronomical reasons
    """


class ProgramExecutionException(ChimeraException):
    pass


class ProgramExecutionAborted(ChimeraException):
    pass


class ObjectTooLowException(ChimeraException):
    pass
