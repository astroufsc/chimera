import inspect

from chimera.interfaces.lifecycle import ILifeCycle
from chimera.core.config  import OptionConversionException

from chimera.controllers.console.command import Command
from chimera.controllers.console.message import Message, Error, Hint, Config

class ObjectCommand (Command):

    def __init__ (self, name, obj):
        Command.__init__ (self, name)

        self.obj = obj

        self.specials = {"config": self._configHandler}

        self._cmds = None
        self._completers = None

        self._exclude = [name for name in dir(ILifeCycle) if not name.startswith("_")]

    def _getCommands (self):

        if self._cmds != None:
            return self._cmds

        self._cmds = []
        
        for name in dir(self.obj):

            if name.startswith("_"): continue

            attr = getattr (self.obj, name)

            if not callable (attr): continue
            
            self._cmds.append(name)

        for ex in self._exclude:
            if ex in self._cmds:
                self._cmds.remove(ex)

        for inc in self.specials.keys():
            self._cmds.append (inc)

        return self._cmds

    def complete (self, prefix, line, prefix_start, prefix_end):

        if not line.strip():
            return self._getCommands()
        else:

            # subcommand prefix
            if prefix_start == 0:
                return [cmd for cmd in self._getCommands() if cmd.startswith(prefix) ]

            # subcommand arguments
            subcommand_name = line.strip().split()[0]

            # FIXME: only config by now
            if subcommand_name == "config":
                return self._configCompleter (prefix, line.strip()[len(subcommand_name):],
                                              prefix_start - len(subcommand_name) - 1,
                                              prefix_end   - len(subcommand_name) - 1)

        return []

    def execute (self, args, namespace):
 
        if not args.strip():
            return str(self.name())

        method = args.split()[0]
 
        if method in self.specials:
            return self.specials[method] (args)
        
        try:
            args = args[len(method):].strip()
            evaluated = ()

            # if there are arguments, eval them
            if args:
                evaluated = eval ("(%s,)" % args )

            return self._methodHandler (method, evaluated)            

        except Exception, e:
            print e
            return Error ("Invalid arguments '%s' for %s" % (args, method))
                     

    def _getMethodSignature (self, method):

        args, varargs, kwargs, defaults = inspect.getargspec (method)

        # to remove self
        args = args[1:]        

        non_default = len(args) - len(defaults) 

        sign = ""
        for i, default in zip(range(len(defaults)), defaults):
            args[len(args)-i-1] = "%s=%s" % (args[len(args)-i-1], default)

        for arg in args:
            sign += str(arg) + " "

        sign = sign[:-1]

        sign = "%s %s" % (method.__name__, sign)

        return (len(args), non_default, sign)


    def _methodHandler (self, method, args):

        func= None

        try:
            func = getattr (self.obj, method)
        except AttributeError, e:
            return Error ("Invalid operation on %s" % self.name())

        # check arguments number
        arg_count, non_default_args, signature = self._getMethodSignature (func)

        if len (args) < non_default_args:
            return [Error ("%s takes %d argument(s), %d given." % (method, non_default_args, len(args))),
                    Hint ("Usage: %s" % signature)]

        elif len(args) > arg_count:
            return [Error ("%s takes at most %d argument(s), %d given." % (method, non_default_args, len(args))),
                    Hint ("Usage: %s" % signature)]

        try:
            return func(*args)
        except Exception, e:
            print e
            return Error ("Error in %s %s call" % (self.name(), method))


    def _configCompleter (self, prefix, *ignored):

        if not hasattr(self.obj, 'config'):
            return []
        
        return [name for name in self.obj.config.keys() if name.startswith(prefix)]

    # FIXME: better parsing!
    def _configHandler (self, args):
    
        if not hasattr (self.obj, 'config'):
            return Error ("Object doesn't support configuration")

        args = args[len("config"):].strip()

        if not args:
            # return all
            return Config(self.obj.config)

        def getConfig (key):
            return self.obj.config[key]

        def setConfig (key, value):
            self.obj.config[key] = value
            return None

        # parse required on config args
        tasks   = []
        errors  = []
        results = {}

        for item in args.split(","):

            if "=" in item:
                # setter one
                try:
                    key, value = item.split("=")
                    key = key.strip()
                    value = value.strip()

                    try:
                        value = eval(value)
                    except Exception:
                        errors.append ("invalid configuration value")    

                    tasks.append ((setConfig, (key, value)))
                    
                except ValueError:
                    errors.append ("invalid syntax")

            else:
                # simple getters
                key = item.strip()

                if not key:
                    continue
                
                tasks.append ((getConfig, (key,)))

        for task in tasks:

            handler, name, args = task[0], task[1][0], task[1]
            
            try:
                result = handler (*args)

                if result != None:
                    results[name] = result

            except KeyError:
                errors.append ("'%s' doesn't exists" % name)
            except OptionConversionException:
                errors.append ("invalid configuration value to '%s'" % name)

        errors_list  = [ Error("%s: %s" % (self.name(), err)) for err in errors ]
        results_list = [Config(results)]
        
        return errors_list+results_list

