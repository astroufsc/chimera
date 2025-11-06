import enum

# TODO migrate to argparse
import optparse
import random
import sys
import threading
from collections.abc import Callable
from typing import Any, TextIO

from chimera.core.bus import Bus
from chimera.core.chimera_config import ChimeraConfig
from chimera.core.constants import CHIMERA_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.proxy import Proxy
from chimera.core.url import parse_url
from chimera.core.version import chimera_version

__all__ = ["ChimeraCLI", "Action", "Parameter", "action", "parameter"]


class ParameterType(enum.StrEnum):
    INSTRUMENT = "INSTRUMENT"
    CONTROLLER = "CONTROLLER"
    BOOLEAN = "BOOLEAN"
    CHOICE = "CHOICE"
    CONSTANT = "CONSTANT"


class _Option:
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

    # for ParameterType.INSTRUMENT or ParameterType.CONTROLLER
    required: bool = False
    url: str | None = None

    const = None

    def __init__(self, **kw: dict[str, Any]):
        for key, value in list(kw.items()):
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError(f"Invalid option '{key}'.")

        self.validate()

    def validate(self):
        self.name = self.name or getattr(self.target, "__name__")

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


class Action(_Option):
    pass


class Parameter(_Option):
    pass


def action(
    *args: list[Any],
    name: str | None = None,
    short: str | None = None,
    long: str | None = None,
    type: str | None = None,
    action_group: str | None = None,
    help: str | None = None,
    help_group: str | None = None,
    default: Any = None,
    metavar: str | None = None,
):
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

    def mark_action(func: Callable[..., None]) -> Callable[..., None]:
        action = Action(
            *args,
            target=func,
            name=name,
            short=short,
            long=long,
            type=type,
            action_group=action_group,
            help=help,
            help_group=help_group,
            default=default,
            metavar=metavar,
        )
        func.__payload__ = action
        return func

    if len(args) > 0:
        return mark_action(args[0])
    else:
        return mark_action


def parameter(*args: list[Any], **kwargs: dict[str, Any]) -> Any:
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


def check_url(option, opt_str, value, parser):
    try:
        parse_url(value)
    except ValueError:
        raise optparse.OptionValueError(f"'{value}' isnt't a valid URL.")

    setattr(parser.values, f"{option.dest}", value)


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

    All parameters are optional, action code will check for required
    parameters and shout if needed.

    At least one action is required, if none given, --help will be
    fired.

    There are a few auto-generated options:
        --help --verbose

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
    """

    def __init__(
        self,
        prog: str,
        description: str,
        version: str,
        verbosity: bool = True,
    ):
        self.parser = optparse.OptionParser(
            prog=prog,
            description=description,
            version=f"Chimera: {chimera_version}\n{prog}: {version}",
        )

        # hack to inject our exit funciton into the parser
        def parser_exit(status: int = 0, msg: str | None = None):
            return self.exit(msg=msg, ret=status)

        self.parser.exit = parser_exit

        self.options = None

        self._actions: dict[str, Action] = {}
        self._parameters: dict[str, Parameter] = {}

        self._help_groups = {}

        self._aborting = False

        # shutdown event
        self.died = threading.Event()

        # base actions and parameters

        if verbosity:
            self.add_parameters(
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
                default=CHIMERA_CONFIG_DEFAULT_FILENAME,
                help="Chimera configuration file to use. default=%default",
                help_group="CONFIG",
            ),
        )

        self.config = None

    def out(self, *args: str, **kwargs: Any):
        self._print(*args, **kwargs)

    def err(self, *args: str, **kwargs: Any):
        kwargs["file"] = sys.stderr
        self._print(*args, **kwargs)

    def _print(self, *args: str, **kwargs: Any):
        sep = kwargs.pop("sep", " ")
        end = kwargs.pop("end", "\n")
        stream: TextIO = kwargs.pop("file", sys.stdout)

        for arg in args:
            stream.write(arg)
            stream.write(sep)

        stream.write(end)
        stream.flush()

    def add_parameters(self, *params: dict[str, Any]):
        for param in params:
            p = Parameter(**param)
            self._parameters[p.name] = p

    def add_actions(self, *actions: Action):
        for action in actions:
            act = Action(**action)
            self._actions[act.name] = act

    def add_help_group(self, name: str, shortdesc: str, longdesc: str | None = None):
        self._help_groups[name] = optparse.OptionGroup(self.parser, shortdesc, longdesc)

    def add_instrument(self, **params: Any):
        params["type"] = ParameterType.INSTRUMENT
        params["default"] = f"/{params.get('cls')}/0"
        self.add_parameters(params)

    def add_controller(self, **params: Any):
        params["type"] = ParameterType.CONTROLLER
        params["default"] = f"/{params.get('cls')}/0"
        self.add_parameters(params)

    def exit(self, msg: str | None = None, ret: int = 1):
        if msg:
            self.err(msg)

        self.died.set()

        if "bus" in self.__dict__:
            self.bus.shutdown()

        sys.exit(ret)

    def run(self, cmdline_args: list[str]):
        self._run(cmdline_args)

    def wait(self, abort: bool = True):
        self.bus.run_forever()

        # FIXME: bus is already dead now, cannot abort anymore
        # if abort:
        #     self.abort()

        self.bus.shutdown()

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

    def _run(self, cmdline_args: list[str]):
        # create parser from defined actions and parameters
        self._create_parser()

        # run the parser
        self.options, _ = self.parser.parse_args(
            cmdline_args,
            values=self.parser.get_default_values(),
        )

        # check which actions should run and if there is any conflict
        action = self._get_selected_actions(self.options)
        if not action:
            self.exit("Please select one action or --help for more information.")

        self._validate_parameters(self.options)
        self._start_system(self.options)

        t = threading.Thread(target=self._run_actions, args=(action,), daemon=True)
        t.start()

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
                option_callback = check_url

            if param.type == ParameterType.BOOLEAN:
                option_action = "store_true"
                option_type = None

            if param.type == ParameterType.CONSTANT:
                option_action = "store_const"
                option_type = None
                option_const = param.const

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

    def _get_selected_actions(self, options: optparse.Values) -> list[Action]:
        selected: list[Action] = []

        # FIXME: handle default actions. So far, only chimera-cam has it for expose

        for action_name, action in self._actions.items():
            action_selected = getattr(options, action_name)
            # FIXME: ignoring default actions for now
            if action_selected and action.default is None:
                selected.append(action)

        # do not allow more than one action per action group
        for action in selected:
            for other_action in selected:
                if (
                    action != other_action
                    and action.action_group == other_action.action_group
                ):
                    self.exit(
                        f"Cannot use {action.long} and {other_action.long} at the same time."
                    )

        return selected

    def _validate_parameters(self, options: optparse.Values):
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

    def _setup_objects(self, options: optparse.Values):
        instruments = {
            x.name: x
            for x in list(self._parameters.values())
            if x.type is not None and x.type == ParameterType.INSTRUMENT
        }
        controllers = {
            x.name: x
            for x in list(self._parameters.values())
            if x.type is not None and x.type == ParameterType.CONTROLLER
        }

        for inst in list(instruments.values()) + list(controllers.values()):
            url = getattr(options, inst.name)

            # use user instrument if given
            if url != inst.default:
                inst.url = parse_url(url)
            else:
                inst.url = parse_url(
                    f"{self.config.host}:{self.config.port}{inst.default}"
                )

            inst_proxy = Proxy(inst.url.url, self.bus)
            try:
                inst_proxy.resolve()
                setattr(self, inst.name, inst_proxy)
            except ObjectNotFoundException:
                if inst.required:
                    self.exit(
                        f"Could not connect to {inst.cls} at {inst.url.url}. [Ping failed]"
                    )


    def _start_system(self, options: optparse.Values):
        self.config = ChimeraConfig.from_file(options.config)
        random_port = random.randint(10000, 60000)
        self.bus = Bus(f"tcp://{self.config.host}:{random_port}")

    def _run_actions(self, actions: list[Action]):
        # NOTE: we do this here to make sure the Bus is ready before we ask for Proxies
        self._setup_objects(self.options)

        # run actions
        for action in actions:
            if not self._run_action(action, self.options):
                self.exit(ret=1)

        self.died.set()
        self.bus.shutdown()
        self.exit()

    def _run_action(self, action: Action, options: list[_Option]) -> bool:
        try:
            if action.target is not None:
                method = getattr(self, action.target.__name__)
                method(options)
        except Exception:
            # import rich.console

            # rich.console.Console().print_exception()
            self.err(f"Something wrong with '{action.name}' action.")
            # print_exception(e)
            raise
            return False

        return True
