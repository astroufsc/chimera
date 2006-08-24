import win32serviceutil, win32service
import pywintypes, win32con, winerror
import servicemanager


class UTSPointingService(win32serviceutil.ServiceFramework):

    _svc_name_ = "UTSPointingService"
    _svc_display_name_ = "UTS Pointing Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, 'normal starting.')
                )

        servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, "normal stop.")
                )


if __name__=='__main__':
    win32serviceutil.HandleCommandLine(UTSPointingService)
