import enum
import optparse
import os.path
import random
import socket
import sys
import threading

from chimera.core.bus import Bus
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.path import ChimeraPath
from chimera.core.proxy import Proxy
from chimera.core.systemconfig import SystemConfig
from chimera.core.url import parse_url
from chimera.core.version import _chimera_version_

__all__ = ["ChimeraCLI", "Action", "Parameter", "action", "parameter"]


class ParameterType(enum.StrEnum):
    INSTRUMENT = "INSTRUMENT"
    CONTROLLER = "CONTROLLER"
    BOOLEAN = "BOOLEAN"
    CHOICE = "CHOICE"
    INCLUDE_PATH = "INCLUDE_PATH"
    CONSTANT = "CONSTANT"


class Option:
    name = None

    short = None
    long = None

    type = None
    default = None

    choices = None

    action_group = None

    help = None
    help_group = None
    metavar = None

    target = None
    cls = None

    # if ParameterType.INSTRUMENT: is this instrument required?
    required = False

    # if ParameterType.INSTRUMENT or ParameterType.CONTROLLER
    location = None

    const = None

    def __init__(self, **kw):

        for key, value in list(kw.items()):

            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError(f"Invalid option '{key}'.")

        self.validate()

    def validate(self):

        self.name = self.name or getattr(self.target, "__name__", None)

        if not self.name:
            raise TypeError("Option must have a name")

        self.long = self.long or self.name
        self.help = self.help or getattr(self.target, "__doc__", None)

        if self.short and self.short[0] != "-":
            self.short = "-" + self.short

        if self.long and self.long[0] != "-":
            self.long = "--" + self.long

        if self.name and self.name[0] == "-":
            self.name = self.name[self.name.rindex("-") + 1 :]

        if self.help:
            self.help = self.help.strip().replace("\n", " ")
            if self.default:
                self.help += " [default=%default]"

        if self.metavar:
            self.metavar = self.metavar.upper()
        else:
            self.metavar = self.name.upper()

    def __str__(self):
        s = ""
        s += f"<{self.__class__.__name__} "
        for name in dir(self):
            attr = getattr(self, name)
            if not name.startswith("_") and not hasattr(attr, "__call__"):
                s += f"{name}={attr} "
        s = s[:-1]
        s += ">"
        return s

    def __repr__(self):
        return self.__str__()


class Action(Option):
    pass


class Parameter(Option):
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
    #     inst.move_to(options.to)

    See L{Action} for information about valid keywork arguments.
    """

    def mark_action(func):
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

    def mark_param(func):
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
    def check_include_path(option, opt_str, value, parser):
        if not value or not os.path.isdir(os.path.abspath(value)):
            raise optparse.OptionValueError(f"Couldn't find {value} include path.")
        getattr(parser.values, f"{option.dest}").append(value)

    @staticmethod
    def check_url(option, opt_str, value, parser):
        try:
            parse_url(value)
        except ValueError:
            raise optparse.OptionValueError(f"{value} isnt't a valid URL.")

        setattr(parser.values, f"{option.dest}", value)


class CLIValues:
    """
    This class mimics optparse.Values class, but add an order list to keep
    track of the order in which the command line parameters was parser. This
    is important to ChimeraCLI to keep CLI's with very high level of usability.

    For every option the parser, OptionParser will call setattr to store the
    command line value, we just keep track of the order and ChimeraCLI does
    the rest.
    """

    def __init__(self, defaults=None):

        if defaults:
            for attr, val in list(defaults.items()):
                setattr(self, attr, val)

        object.__setattr__(self, "__order__", [])

    def __setattr__(self, attr, value):

        object.__setattr__(self, attr, value)

        if hasattr(self, "__order__"):
            order = object.__getattribute__(self, "__order__")
            order.append(attr)


class ChimeraCLI:
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

    To define parameters, use parameter decorator or add_parameter method.
    The parameter method passed to the decorator will be called to validate
    the parameter value given on the command line. Otherwise, no
    validation, besides type checking, will be done.

    For example:

    self.add_parameter(name='ra', help='Help for RA', type=string)

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

    def __init__(
        self,
        prog,
        description,
        version,
        verbosity=True,
        instrument_path=True,
        controllers_path=True,
    ):

        self.parser = optparse.OptionParser(
            prog=prog,
            description=description,
            version=f"Chimera: {_chimera_version_}\n{prog}: {version}",
        )

        # hack to inject our exit funciton into the parser
        def parser_exit(status=0, msg=None):
            return self.exit(msg=msg, ret=status)

        self.parser.exit = parser_exit

        self.options = None

        self._actions = {}
        self._parameters = {}

        self._help_groups = {}

        self._aborting = False

        # shutdown event
        self.died = threading.Event()

        # base actions and parameters

        if verbosity:
            self.add_parameters(
                dict(
                    name="quiet",
                    short="q",
                    long="quiet",
                    type=ParameterType.BOOLEAN,
                    default=True,
                    help="Don't display information while working.",
                ),
                dict(
                    name="verbose",
                    short="v",
                    long="verbose",
                    type=ParameterType.BOOLEAN,
                    default=False,
                    help="Display information while working",
                ),
            )

        self.add_help_group("CONFIG", "Client Configuration")
        self.add_parameters(
            dict(
                name="config",
                default=SYSTEM_CONFIG_DEFAULT_FILENAME,
                help="Chimera configuration file to use. default=%default",
                help_group="CONFIG",
            ),
        )

        self.sysconfig = None

        self._need_instruments_path = instrument_path
        self._need_controllers_path = controllers_path

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

    def add_parameters(self, *params):
        for param in params:
            p = Parameter(**param)
            self._parameters[p.name] = p

    def add_actions(self, *actions):
        for action in actions:
            act = Action(**action)
            self._actions[act.name] = act

    def add_help_group(self, name, shortdesc, longdesc=None):
        self._help_groups[name] = optparse.OptionGroup(self.parser, shortdesc, longdesc)

    def add_instrument(self, **params):
        params["type"] = ParameterType.INSTRUMENT
        self.add_parameters(params)

        if self._need_instruments_path:
            if "PATHS" not in self._help_groups:
                self.add_help_group("PATHS", "Object Paths")

            self.add_parameters(
                dict(
                    name="inst_dir",
                    short="I",
                    long="instruments-dir",
                    help_group="PATHS",
                    type=ParameterType.INCLUDE_PATH,
                    default=ChimeraPath().instruments,
                    help="Append PATH to {} load path. "
                    "This option could be setted multiple "
                    "times to add multiple directories.".format(
                        params["name"].capitalize()
                    ),
                    metavar="PATH",
                )
            )
            self._need_instruments_path = False

    def add_controller(self, **params):
        params["type"] = ParameterType.CONTROLLER
        self.add_parameters(params)

        if self._need_controllers_path:
            if "PATHS" not in self._help_groups:
                self.add_help_group("PATHS", "Object Paths")

            self.add_parameters(
                dict(
                    name="ctrl_dir",
                    short="C",
                    long="controllers-dir",
                    help_group="PATHS",
                    type=ParameterType.INCLUDE_PATH,
                    default=ChimeraPath().controllers,
                    help="Append PATH to controllers load path. "
                    "This option could be setted multiple "
                    "times to add multiple directories.",
                    metavar="PATH",
                )
            )
            self._need_controllers_path = False

    def exit(self, msg=None, ret=1):
        if msg:
            self.err(msg)

        self.died.set()

        sys.exit(ret)

    def run(self, cmdline_args):
        self._run(cmdline_args)

    def _run(self, cmdline_args):

        # create parser from defined actions and parameters
        self._create_parser()

        # run the parser
        self.options, args = self.parser.parse_args(
            cmdline_args,
            values=CLIValues(defaults=self.parser.get_default_values().__dict__),
        )

        # check which actions should run and if there is any conflict
        actions = self._get_actions(self.options)

        if not actions:
            self.exit("Please select one action or --help for more information.")

        # for each defined parameter, run validation code
        self._validate_parameters(self.options)

        # setup objects
        self._setup_objects(self.options)

        t = threading.Thread(target=self._run_actions, args=(actions,), daemon=True)
        t.start()

    def _run_actions(self, actions):
        # run actions
        for action in actions:
            if not self._run_action(action, self.options):
                self.exit(ret=1)

        self.died.set()
        self.bus.shutdown()
        self.exit()

    def wait(self, abort: bool = True):
        self.bus.run_forever()

        # FIXME: bus is already dead now, cannot abort anymore
        # if abort:
        #     self.abort()

        self.bus.shutdown()

    def _start_system(self, options):
        self.sysconfig = SystemConfig.from_file(options.config)
        # FIXME: how to assign this in a nice way?
        n = random.randint(10000, 60000)
        self.bus = Bus(f"tcp://127.0.0.1:{10000}")

    def _belongs_to(self, me_host, me_port, location):

        if not location:
            return False

        me_name = socket.gethostbyname(me_host)
        return (location.host is None or location.host in (me_host, me_name)) and (
            location.port is None or location.port == me_port
        )

    def _setup_objects(self, options):

        # CLI requested objects
        instruments = dict(
            [
                (x.name, x)
                for x in list(self._parameters.values())
                if x.type == ParameterType.INSTRUMENT
            ]
        )
        controllers = dict(
            [
                (x.name, x)
                for x in list(self._parameters.values())
                if x.type == ParameterType.CONTROLLER
            ]
        )

        # starts a local Manager (not using sysconfig) or a full sysconfig
        # backed if needed.
        self._start_system(self.options)

        # create locations
        for inst in list(instruments.values()) + list(controllers.values()):

            # use user instrument if given
            if inst.default != getattr(options, inst.name):
                try:
                    inst.location = parse_url(getattr(options, inst.name))
                except ValueError:
                    self.exit(
                        f"Invalid location: {getattr(options, inst.name)}. See --help for more information"
                    )

            else:
                inst.location = None

            if not inst.location and inst.required:
                self.exit(
                    f"Couldn't find {inst.name.capitalize()} configuration. "
                    f"Edit {os.path.abspath(options.config)} or see --help for more information"
                )

        for inst in list(instruments.values()) + list(controllers.values()):

            inst_proxy = None

            if inst.location:
                try:
                    inst_proxy = Proxy(str(inst.location), self.bus)
                # FIXME: I don't think this exception exists anymore
                except ObjectNotFoundException:
                    if inst.required:
                        self.exit(
                            f"Couldn't find {inst.name.capitalize()}. (see --help for more information)"
                        )

                # save values in CLI object (which users are supposed to inherits from).
                setattr(self, inst.name, inst_proxy)

    def _create_parser(self):

        for name in dir(self):
            attr = getattr(self, name)

            if isinstance(attr, Action) or hasattr(attr, "__payload__"):

                try:
                    # decorated methods
                    payload = getattr(attr, "__payload__")
                except AttributeError:
                    # pure attribute
                    payload = attr

                if isinstance(payload, Action):
                    self._actions[payload.name] = payload
                elif isinstance(payload, Parameter):
                    self._parameters[payload.name] = payload

        for action in list(self._actions.values()):

            if not action.action_group:
                action.action_group = action.name

            if action.type:
                kind = "store"
            else:
                kind = "store_true"

            group = self._help_groups.get(action.help_group, self.parser)

            if action.short:
                group.add_option(
                    action.short,
                    action.long,
                    action=kind,
                    type=action.type,
                    dest=action.name,
                    help=action.help,
                    metavar=action.metavar,
                )
            else:
                group.add_option(
                    action.long,
                    dest=action.name,
                    action=kind,
                    type=action.type,
                    help=action.help,
                    metavar=action.metavar,
                )

        for param in list(self._parameters.values()):

            if not param.type:
                param.type = "string"

            group = self._help_groups.get(param.help_group, self.parser)

            option_action = "store"
            option_callback = None
            option_choices = None
            option_const = None
            option_type = param.type or None

            if param.type in (ParameterType.INSTRUMENT, ParameterType.CONTROLLER):
                option_type = "string"
                option_action = "callback"
                option_callback = CLICheckers.check_url

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
                option_callback = CLICheckers.check_include_path

            if param.type == ParameterType.CHOICE:
                option_action = "store"
                option_type = "choice"
                option_choices = param.choices

            option_kwargs = dict(
                action=option_action,
                dest=param.name,
                help=param.help,
                metavar=param.metavar,
            )

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

        for group in list(self._help_groups.values()):
            self.parser.add_option_group(group)

        defaults = {}

        for action in list(self._actions.values()):
            if action.default is not None:
                defaults[action.name] = action.default

        for param in list(self._parameters.values()):
            if param.default is not None:
                defaults[param.name] = param.default

        self.parser.set_defaults(**defaults)

    def _get_actions(self, options):

        # actions in command line (and run) order
        actions = [
            self._actions[action]
            for action in self.options.__order__
            if action in self._actions
        ]

        # add default actions
        # FIXME: there is no way to disable a default action?
        actions.extend(
            [action for action in list(self._actions.values()) if action.default]
        )

        if not actions:
            return []

        for action in actions:
            for other in actions:
                if action != other and action.action_group == other.action_group:
                    self.exit(
                        f"Cannot use {action.long} and {other.long} at the same time."
                    )

        # remove duplicates
        unique_actions = []

        for action in actions:
            if action in unique_actions:
                continue
            unique_actions.append(action)

        return unique_actions

    def _validate_parameters(self, options):

        param_values = [
            getattr(options, param) for param in list(self._parameters.keys())
        ]

        for name, value in zip(list(self._parameters.keys()), param_values):
            param = self._parameters[name]

            try:
                # to signal invalid values, use self.exit or throws a
                # ValueError exception if None returned, just copy passed value
                if param.target is not None:
                    new_value = getattr(self, param.target.__name__)(value)
                    setattr(options, name, new_value or value)
            except ValueError as e:
                self.exit(f"Invalid value for {name}: {e}")

    def _run_action(self, action, options):
        try:
            if action.target is not None:
                method = getattr(self, action.target.__name__)
                method(options)
        except Exception as e:
            self.err(f"Something wrong with '{action.name}' action.")
            print_exception(e)
            return False

        return True

    def abort(self):

        if self._aborting is False:
            self._aborting = True
        else:
            return

        if hasattr(self, "__abort__"):
            abort = getattr(self, "__abort__")
            if hasattr(abort, "__call__"):
                t = threading.Thread(target=abort)
                t.start()
                try:
                    t.join()
                except KeyboardInterrupt:
                    pass

        self.exit(ret=2)

    def is_aborting(self):
        return self._aborting
