
class ChimeraGUIModule(object):

    module_controls = {"default": "Default"}

    def __init__ (self,  manager):
        self.builder = None
        self.manager = manager
        
    def setupGUI (self, objects):
        """
        You could override this method and add module specific widgets
        to the GUI.  This method must returns a GtkWidget, that would
        be the added to the module's dock.

        The objects parameter is a dict with object Proxies that this
        module can control (defined in self.module_controls).
        """

    def setupEvents (self):
        """
        Override this method to add module specific event handling.
        This methos will be called after GUI creation.
        """


