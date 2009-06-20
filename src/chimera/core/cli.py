from chimera.core.version   import _chimera_version_, _chimera_description_
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.location  import Location, InvalidLocationException

from chimera.core.systemconfig import SystemConfig
from chimera.core.manager      import Manager
from chimera.core.path         import ChimeraPath

from chimera.controllers.site.main import SiteController
from chimera.core.exceptions       import ObjectNotFoundException, printException
from chimera.core.managerlocator   import ManagerLocator, ManagerNotFoundException

from chimera.util.enum      import Enum

import sys
import optparse
import os.path
import signal
import threading
import socket

__all__ = ['ChimeraCLI',
           'Action',
           'Parameter',
           'action',
           'parameter']

ParameterType = Enum("INSTRUMENT", "CONTROLLER", "BOOLEAN", "CHOICE", "INCLUDE_PATH", "CONSTANT")

class Option (object):
    name  = None

    short = None
    long  = None

    type  = None
    default = None
    
    choices = None

    actionGroup = None

    help  = None
    helpGroup = None
    metavar = None

    target = None
    cls = None

    # if ParameterType.INSTRUMENT: is this instrument required?
    required = False

    # if ParameterType.INSTRUMENT or ParameterType.CONTROLLER
    location = None

    const = None

    def __init__ (self, **kw):

        for key, value in kw.items():

            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError("Invalid option '%s'." % key)

        self.validate()

    def validate (self):

        self.name  = self.name or getattr(self.target, '__name__', None)

        if not self.name:
            raise TypeError("Option must have a name")

        self.long  = self.long or self.name
        self.help  = self.help or getattr(self.target, '__doc__', None)

        if self.short and self.short[0] != '-':
            self.short = "-" + self.short

        if self.long and self.long[0] != '-':
            self.long = "--" + self.long

        if self.name and self.name[0] == '-':
            self.name = self.name[self.name.rindex('-')+1:]

        if self.help:
            self.help = self.help.strip().replace("\n", " ")
            if self.default:
                self.help += " [default=%default]"

        if self.metavar:
            self.metavar = self.metavar.upper()
        else:
            self.metavar = self.name.upper()
                        
    def __str__ (self):
        s = ""
        s += "<%s " % self.__class__.__name__
        for name in dir(self):
            attr = getattr(self, name)
            if not name.startswith("_") and not hasattr(attr, '__call__'):
                s += "%s=%s " % (name, attr)
        s = s[:-1]
        s += ">"
        return s

    def __repr__ (self):
        return self.__str__()

class Action (Option):
    pass

class Parameter (Option):
    pass


def action(*args, **kwargs):
    """
    Defines a command line action with short name 'short', long name
    'long'. If 'short' not given, will use the first letter of the
    method name (if possible), if 'long' not given, use full method
    name.

    Use 'type' if the action require a direct parameter, like '--to
    10', in this case, action should be like this:

    # @action(long='to', type='int')
    # def move_to (self, options):
    #     inst.moveTo(options.to)

    See L{Action} for information about valid keywork arguments.
    """

    def mark_action (func):
        kwargs["target"] = func
        act = Action(**kwargs)
        func.__payload__ = act
        return func

    if len(args) > 0:
        return mark_action(args[0])
    else:
        return mark_action


def parameter(*args, **kwargs):
    """
    Defines a command line parameter with short name 'short', long
    name 'long'. If 'short' not given, will use the first letter of
    the method name (if possible), if 'long' not given, use full
    method name. If type given, parameter will be checked to match
    'type'. The default value, if any, shoud be passed on 'default'.

    See L{Parameter} for information about valid keywork arguments.
    """

    def mark_param (func):
        kwargs["target"] = func
        param = Parameter(**kwargs)
        func.__payload__ = param
        return func

    if len(args) > 0:
        return mark_param(args[0])
    else:
        return mark_param

class CLICheckers:

    @staticmethod
    def check_includepath (option, opt_str, value, parser):
        if not value or not os.path.isdir (os.path.abspath(value)):
            raise optparse.OptionValueError ("Couldn't find %s include path." % value)
        l = getattr(parser.values, "%s" % option.dest)
        l.append(value)

    @staticmethod
    def check_location (option, opt_str, value, parser):
        try:
            l = Location (value)
        except InvalidLocationException:
            raise optparse.OptionValueError ("%s isnt't a valid location." % value)

        setattr(parser.values, "%s" % option.dest, value)
    

class CLIValues (object):
    """This class mimics optparse.Values class, but add an order list to keep track of the order
    in which the command line parameters was parser. This is important to ChimeraCLI to keep CLI's
    with very high level of usability.
    
    For every option the parser, OptionParser will call setattr to store the command line value,
    we just keep track of the order and ChimeraCLI does the rest.
    """

    def __init__ (self, defaults=None):
        
        if defaults:
            for (attr, val) in defaults.items():
                setattr(self, attr, val)
        
        object.__setattr__(self, '__order__', [])
        
    def __setattr__ (self, attr, value):

        object.__setattr__(self, attr, value)
        
        if hasattr(self, '__order__'):
            order = object.__getattribute__(self, '__order__')
            order.append(attr)
        

class ChimeraCLI (object):
    """
    Create a command line program with automatic parsing of actions
    and parameters based on decorators.

    This class define common methods for a command line interface
    (CLI) program. You should extends it and add methods with specific
    decorators to create personalized CLI programs.

    This class defines a CLI program which accepts parameters (of any
    kind) and do actions using those parameters. Only one action will
    run for a given command line. if more than one action was asked,
    only the first will run.

    The general form of the arguments that CLI accepts is given
    below:

    cli-program (--action-1|--action-2|...|--action-n)
                [--param-1=value1,--param-2=value-2|...|--param-n=value-n]

    Al parameters are optional, action code will check for required
    parameters and shout if needed.

    At least one action is required, if none given, --help will be
    fired.

    There are a few auto-generated options:
     --help --quiet --verbose (default=True) --log=file

    To create actions, use 'action' decorator. If that action was
    detected on the command line arguments, action method will be
    called with an object containing all the parameters available.

    For example:

    @action(short='s', long='slew'):
    def slew(self, options):
        inst.slew(options.ra, options.dec)

    To define parameters, use parameter decorator or addParameter method.
    The parameter method passed to the decorator will be called to validate
    the parameter value given on the command line. Otherwise, no
    validation, besides type checking, will be done.

    For example:

    self.addParameter(name='ra', help='Help for RA', type=string)

    or

    @parameter(long='ra', type=string)
    def ra(self, value):
        '''
        Help for RA
        '''
        # validate
        # return valid value or throw ValueError

    When you define a Parameter using @parameter decorator,
    the name of the decorated function will be available in the options
    dictionary passed to every action. Otherwise, you need to use name
    keyword to define different names or to use with attribute based parameters

    Before run the selected action, ChimeraCLI runs the method
    __start__, passing all the parameters and the action that would
    run. After the action be runned, __stop__ would be called.

    """
            
    def __init__ (self, prog, description, version,
                  port=None, verbosity=True,
                  instrument_path=True, controllers_path=True):

        self.parser = optparse.OptionParser(prog=prog,
                                             description=_chimera_description_ + " - " + description,
                                             version="Chimera: %s\n%s: %s" % (_chimera_version_, prog, version))

        self.options = None

        self._actions = {}
        self._parameters = {}
        
        self._helpGroups = {}
        
        self._aborting = False

        self._keepRemoteManager = True

        signal.signal(signal.SIGTERM, self._sighandler)
        signal.signal(signal.SIGINT, self._sighandler)

        # base actions and parameters

        if verbosity:
            self.addParameters(dict(name="quiet", short="q", long="quiet",
                                    type=ParameterType.BOOLEAN, default=True,
                                    help="Don't display information while working."),

                               dict(name="verbose", short="v", long="verbose",
                                    type=ParameterType.BOOLEAN, default=False,
                                    help="Display information while working"))

        self.addHelpGroup("LOCALMANAGER", "Client Configuration")
        self.addParameters(dict(name="port", short="P", helpGroup="LOCALMANAGER", default=port or 9000,
                                help="Port to which the local Chimera instance will listen to."),
                           dict(name="config", default=SYSTEM_CONFIG_DEFAULT_FILENAME,
                                    help="Chimera configuration file to use. default=%default",
                                    helpGroup="LOCALMANAGER"))

        self.localManager  = None
        self._remoteManager = None
        self.sysconfig = None

        self._needInstrumentsPath = instrument_path
        self._needControllersPath = controllers_path

    def _print(self, *args, **kwargs):
        sep = kwargs.pop("sep", " ")
        end = kwargs.pop("end", "\n")
        stream = kwargs.pop("file", sys.stdout)
        
        for arg in args:
            stream.write(arg)
            stream.write(sep)

        stream.write(end)
        stream.flush()
        
    def out(self, *args, **kwargs):
        self._print(*args, **kwargs)

    def err(self, *args, **kwargs):
        kwargs["file"] = sys.stderr
        self._print(*args, **kwargs)
        
    def exit(self, msg=None, ret=1):
        self.__stop__(self.options)

        if msg:
            self.err(msg)
            
        sys.exit(ret)

    def addParameters(self, *params):
        for param in params:
            p = Parameter(**param)
            self._parameters[p.name] = p

    def addActions(self, *actions):
        for action in actions:
            act = Action(**action)
            self._actions[act.name] = act

    def addHelpGroup(self, name, shortdesc, longdesc=None):
        self._helpGroups[name] = optparse.OptionGroup(self.parser, shortdesc, longdesc)

    def addInstrument (self, **params):
        params["type"] = ParameterType.INSTRUMENT
        self.addParameters(params)

        if self._needInstrumentsPath:
            if not "PATHS" in self._helpGroups:
                self.addHelpGroup("PATHS", "Object Paths")

            self.addParameters(dict(name="inst_dir", short="I", long="instruments-dir", helpGroup="PATHS",
                                    type=ParameterType.INCLUDE_PATH, default=[ChimeraPath.instruments()],
                                    help="Append PATH to %s load path. "
                                    "This option could be setted multiple "
                                    "times to add multiple directories." % params["name"].capitalize(),
                                    metavar="PATH"))
            self._needInstrumentsPath = False
            

    def addController (self, **params):
        params["type"] = ParameterType.CONTROLLER
        self.addParameters(params)

        if self._needControllersPath:
            if not "PATHS" in self._helpGroups:
                self.addHelpGroup("PATHS", "Object Paths")

            self.addParameters(dict(name="ctrl_dir", short="C", long="controllers-dir", helpGroup="PATHS",
                                    type=ParameterType.INCLUDE_PATH, default=[ChimeraPath.controllers()],
                                    help="Append PATH to controllers load path. "
                                    "This option could be setted multiple "
                                    "times to add multiple directories.",
                                    metavar="PATH"))
            self._needControllersPath = False

    def run (self, cmdlineArgs):

        # create parser from defined actions and parameters
        self._createParser()

        # run the parser
        self.options, args = self.parser.parse_args(cmdlineArgs, values=CLIValues(defaults=self.parser.get_default_values().__dict__))
        
        # check which actions should run and if there is any conflict
        actions = self._getActions(self.options)

        if not actions:
            self.exit("Please select one action or --help for more information.")
            
        # for each defined parameter, run validation code
        self._validateParameters(self.options)

        # setup objects
        self._setupObjects(self.options)

        self.__start__(self.options, args)

        # run actions
        for action in actions:
            if not self._runAction(action, self.options):
                self.exit(ret=1)

        self.__stop__(self.options)

    def _startSystem (self, options):
        
        try:
            self.sysconfig = SystemConfig.fromFile(options.config)
            self.localManager = Manager(self.sysconfig.chimera["host"], getattr(options, 'port', 9000))
            self._remoteManager = ManagerLocator.locate(self.sysconfig.chimera["host"], self.sysconfig.chimera["port"])
        except ManagerNotFoundException:
            # FIXME: better way to start Chimera
            site = SiteController(wait=False)
            site.startup()

            self._keepRemoteManager = False
            self._remoteManager = ManagerLocator.locate(self.sysconfig.chimera["host"], self.sysconfig.chimera["port"])

    def _belongsTo(self, meHost, mePort, location):
        
        if not location: return False

        meName = socket.gethostbyname(meHost)
        return (location.host == None or location.host in (meHost, meName)) and \
               (location.port == None or location.port == mePort)

    def _setupObjects (self, options):

        # CLI requested objects
        instruments = dict([(x.name, x) for x in self._parameters.values() if x.type == ParameterType.INSTRUMENT])
        controllers = dict([(x.name, x) for x in self._parameters.values() if x.type == ParameterType.CONTROLLER])

        # starts a local Manager (not using sysconfig) or a full sysconfig backed if needed.
        self._startSystem(self.options)

        # create locations
        for inst in instruments.values() + controllers.values():
            
            # use user instrument if given
            if inst.default != getattr(options, inst.name):
                try:
                    inst.location = Location(getattr(options, inst.name))
                except InvalidLocationException:
                    self.exit("Invalid location: %s. See --help for more information" % getattr(options, inst.name))

            else:
                # no instrument selected, ask remote Chimera instance for the newest
                if self._remoteManager:
                    insts = self._remoteManager.getResourcesByClass(inst.cls)
                    if insts:
                        # get the older
                        inst.location = insts[0]

            if not inst.location and inst.required:
                self.exit("Couldn't find %s configuration. "
                          "Edit %s or see --help for more information" % (inst.name.capitalize(), os.path.abspath(options.config)))


        for inst in instruments.values() + controllers.values():

            inst_proxy = None

            try:
                inst_proxy = self._remoteManager.getProxy(inst.location)
            except ObjectNotFoundException:
                if inst.required == True:
                    self.exit("Couldn't find %s. (see --help for more information)" % inst.name.capitalize())

            # save values in CLI object (which users are supposed to inherites from).
            setattr(self, inst.name, inst_proxy)                

    def __start__ (self, options, args):
        pass

    def __stop__ (self, options):
        if self.localManager:
            self.localManager.shutdown()

        if self._remoteManager and not self._keepRemoteManager:
            self._remoteManager.shutdown()

    def _createParser (self):

        for name in dir(self):
            attr = getattr(self, name)

            if isinstance(attr, Action) or hasattr(attr, '__payload__'):

                try:
                    # decorated methods
                    payload = getattr(attr, '__payload__')
                except AttributeError:
                    # pure attribute
                    payload = attr

                if type(payload) == Action:
                    self._actions[payload.name] = payload
                elif type(payload) == Parameter:
                    self._parameters[payload.name] = payload

        for action in self._actions.values():
            
            if not action.actionGroup:
                action.actionGroup = action.name

            if action.type:
                kind = "store"
            else:
                kind = "store_true"

            group = self._helpGroups.get(action.helpGroup, self.parser)

            if action.short:
                group.add_option(action.short, action.long,
                                 action=kind, type=action.type, dest=action.name,
                                 help=action.help, metavar=action.metavar)
            else:
                group.add_option(action.long, dest=action.name,
                                 action=kind, type=action.type,
                                 help=action.help, metavar=action.metavar)

        for param in self._parameters.values():

            if not param.type:
                param.type = "string"

            group = self._helpGroups.get(param.helpGroup, self.parser)

            option_action = "store"
            option_callback = None
            option_choices = None
            option_const = None
            option_type = param.type or None

            if param.type in (ParameterType.INSTRUMENT, ParameterType.CONTROLLER):
                option_type = "string"
                option_action = "callback"
                option_callback  = CLICheckers.check_location

            if param.type == ParameterType.BOOLEAN:
                option_action = "store_true"
                option_type = None

            if param.type == ParameterType.CONSTANT:
                option_action = "store_const"
                option_type = None
                option_const = param.const

            if param.type == ParameterType.INCLUDE_PATH:
                option_action = "callback"
                option_type = "string"
                option_callback = CLICheckers.check_includepath
                
            if param.type == ParameterType.CHOICE:
                option_action = "store"
                option_type = "choice"
                option_choices = param.choices
                
            option_kwargs = dict(action=option_action,
                                 dest=param.name,
                                 help=param.help, metavar=param.metavar)

            if option_callback:
                option_kwargs["callback"] = option_callback

            if option_type:
                option_kwargs["type"] = option_type
                
            if option_choices:
                option_kwargs["choices"] = option_choices

            if option_const:
                option_kwargs["const"] = option_const

            if param.short:
                group.add_option(param.short, param.long, **option_kwargs)
            else:
                group.add_option(param.long, **option_kwargs)

        for group in self._helpGroups.values():
            self.parser.add_option_group(group)

        defaults = {}

        for action in self._actions.values():
            if action.default is not None:
                defaults[action.name] = action.default

        for param in self._parameters.values():
            if param.default is not None:
                defaults[param.name] = param.default

        self.parser.set_defaults(**defaults)

    def _getActions(self, options):

        # actions in command line (and run) order
        actions = [ self._actions[action] for action in self.options.__order__ if action in self._actions ]
        
        # add default actions
        # FIXME: there is no way to disable a default action?
        actions.extend([ action for action in self._actions.values() if action.default == True])
        
        if not actions: return []
        
        for action in actions:
            for other in actions:
                if action != other and action.actionGroup == other.actionGroup:
                    self.exit("Cannot use %s and %s at the same time." % (action.long, other.long))

        # remove duplicates
        uniqueActions = []
        
        for action in actions:
            if action in uniqueActions: continue
            uniqueActions.append(action)

        return uniqueActions

    def _validateParameters(self, options):

        paramValues =  [ getattr(options, param) for param in self._parameters.keys() ]

        for name, value in zip(self._parameters.keys(), paramValues):
            param = self._parameters[name]

            try:
                # to signal invalid values, use self.exit or throws a ValueError exception
                # if None returned, just copy passed value
                if param.target is not None:
                    newValue = getattr(self, param.target.__name__)(value)
                    setattr(options, name, newValue or value)
            except ValueError, e:
                self.exit("Invalid value for %s: %s" % (name, e))

    def _runAction(self, action, options):

        try:
            if action.target is not None:
                method = getattr(self, action.target.__name__)
                method(options)
        except Exception, e:
            self.err("Something wrong with '%s' action." % (action.name))
            printException(e)
            return False

        return True
    
    def _sighandler(self, sig=None, frame=None):
        
        if self._aborting == False:
            self._aborting = True
        else:
            return
            
        if hasattr(self, '__abort__'):
            abort = getattr(self, '__abort__')
            if hasattr(abort, '__call__'):
                t = threading.Thread(target=abort)
                t.start()
                t.join()
                
        self.exit(ret=2)
        
    def isAborting(self):
        return self._aborting
